#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : llm api of qianfan from Baidu, supports ERNIE(wen xin yi yan) and opensource models
import copy
import os
import asyncio
import time
from typing import NamedTuple, Union

import qianfan
from qianfan import ChatCompletion
from qianfan.resources.typing import JsonBody

from metagpt.config import CONFIG
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI

from metagpt.utils.singleton import Singleton
from metagpt.utils.token_counter import (
    TOKEN_COSTS,
    QIANFAN_ENDPOINT_TOKEN_COSTS,
    QIANFAN_MODEL_TOKEN_COSTS,
)


class RateLimiter:
    """Rate control class, each call goes through wait_if_needed, sleep if rate control is needed"""

    def __init__(self, rpm):
        self.last_call_time = 0
        # Here 1.1 is used because even if the calls are made strictly according to time,
        # they will still be QOS'd; consider switching to simple error retry later
        self.interval = 1.1 * 60 / rpm
        self.rpm = rpm

    def split_batches(self, batch):
        return [batch[i : i + self.rpm] for i in range(0, len(batch), self.rpm)]

    async def wait_if_needed(self, num_requests):
        current_time = time.time()
        elapsed_time = current_time - self.last_call_time

        if elapsed_time < self.interval * num_requests:
            remaining_time = self.interval * num_requests - elapsed_time
            logger.info(f"sleep {remaining_time}")
            await asyncio.sleep(remaining_time)

        self.last_call_time = time.time()


class Costs(NamedTuple):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    total_budget: float

class CostManager(metaclass=Singleton):
    """计算使用接口的开销"""

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.total_budget = 0

    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        cost = (
            prompt_tokens * TOKEN_COSTS[model]["prompt"] + completion_tokens * TOKEN_COSTS[model]["completion"]
        ) / 1000
        self.total_cost += cost
        logger.info(
            f"Total running cost: ${self.total_cost:.3f} | Max budget: ${CONFIG.max_budget:.3f} | "
            f"Current cost: ${cost:.3f}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )
        CONFIG.total_cost = self.total_cost

    def get_total_prompt_tokens(self):
        """
        Get the total number of prompt tokens.

        Returns:
        int: The total number of prompt tokens.
        """
        return self.total_prompt_tokens

    def get_total_completion_tokens(self):
        """
        Get the total number of completion tokens.

        Returns:
        int: The total number of completion tokens.
        """
        return self.total_completion_tokens


    def get_total_cost(self):
        """
        Get the total cost of API calls.

        Returns:
        float: The total cost of API calls.
        """
        return self.total_cost


    def get_costs(self) -> Costs:
        """Get all costs"""
        return Costs(self.total_prompt_tokens, self.total_completion_tokens, self.total_cost, self.total_budget)

class QianFanLLM(BaseGPTAPI, RateLimiter):
    """
    Refs
        Auth: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/3lmokh7n6#%E3%80%90%E6%8E%A8%E8%8D%90%E3%80%91%E4%BD%BF%E7%94%A8%E5%AE%89%E5%85%A8%E8%AE%A4%E8%AF%81aksk%E9%89%B4%E6%9D%83%E8%B0%83%E7%94%A8%E6%B5%81%E7%A8%8B
        Token Price: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7#tokens%E5%90%8E%E4%BB%98%E8%B4%B9
        Models: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlmhm7vuo#%E5%AF%B9%E8%AF%9Dchat
                https://cloud.baidu.com/doc/WENXINWORKSHOP/s/xlmokikxe#%E6%94%AF%E6%8C%81%E6%A8%A1%E5%9E%8B%E5%88%97%E8%A1%A8
    """

    def __init__(self,):
        self.config = CONFIG
        self.use_system_prompt = False  # only some ERNIE-x related models support system_prompt
        self.__init_qianfan()
        self.cost_manager = CostManager()

    def __init_qianfan(self):
        if self.config.qianfan_access_key and self.config.qianfan_secret_key:
            # for system level auth, use access_key and secret_key, recommended by official
            # set environment variable due to official recommendation
            os.environ.setdefault("QIANFAN_ACCESS_KEY", self.config.qianfan_access_key)
            os.environ.setdefault("QIANFAN_SECRET_KEY", self.config.qianfan_secret_key)
        elif self.config.qianfan_api_key and self.config.qianfan_secret_key:
            # for application level auth, use api_key and secret_key
            # set environment variable due to official recommendation
            os.environ.setdefault("QIANFAN_AK", self.config.qianfan_api_key)
            os.environ.setdefault("QIANFAN_SK", self.config.qianfan_secret_key)
        else:
            raise ValueError("Set the `access_key`&`secret_key` or `api_key`&`secret_key` first")

        support_system_pairs = [
            ("ERNIE-Bot-4", "completions_pro"),  # (model, corresponding-endpoint)
            ("ERNIE-Bot-8k", "ernie_bot_8k"),
            ("ERNIE-Bot", "completions"),
            ("ERNIE-Bot-turbo", "eb-instant"),
            ("ERNIE-Speed", "ernie_speed"),
            ("EB-turbo-AppBuilder", "ai_apaas"),
        ]
        if self.config.qianfan_model in [pair[0] for pair in support_system_pairs]:
            # only some ERNIE models support
            self.use_system_prompt = True
        if self.config.qianfan_endpoint in [pair[1] for pair in support_system_pairs]:
            self.use_system_prompt = True
        assert not (self.config.qianfan_model and self.config.qianfan_endpoint), "Only set `model` or `endpoint` in the config"
        assert self.config.qianfan_model or self.config.qianfan_endpoint, "Should set one of `model` or `endpoint` in the config"

        self.token_costs = copy.deepcopy(QIANFAN_MODEL_TOKEN_COSTS)
        self.token_costs.update(QIANFAN_ENDPOINT_TOKEN_COSTS)

        # self deployed model on the cloud not to calculate usage, it charges resource pool rental fee
        self.calc_usage = self.config.qianfan_calc_usage and self.config.qianfan_endpoint is None
        self.aclient: ChatCompletion = qianfan.ChatCompletion()

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {
            "messages": messages,
            "stream": stream,
        }
        if self.config.qianfan_temperature > 0:
            # different model has default temperature. only set when it's specified.
            kwargs["temperature"] = self.config.qianfan_temperature
        if self.config.qianfan_endpoint:
            kwargs["endpoint"] = self.config.qianfan_endpoint
        elif self.config.qianfan_model:
            kwargs["model"] = self.config.qianfan_model

        if self.use_system_prompt:
            # if the model support system prompt, extract and pass it
            if messages[0]["role"] == "system":
                kwargs["messages"] = messages[1:]
                kwargs["system"] = messages[0]["content"]  # set system prompt here
        return kwargs

    def _update_costs(self, usage: dict):
        if CONFIG.calc_usage:
            try:
                prompt_tokens = int(usage["prompt_tokens"])
                completion_tokens = int(usage["completion_tokens"])
                self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error("updating costs failed!", e)

    def get_choice_text(self, resp: JsonBody) -> str:
        rsp = resp.get("result", "")
        start_index = rsp.find("```json")
        end_index = rsp.rfind("```")
        result = rsp[start_index+8:end_index]
        return result

    def completion(self, messages: list[dict]) -> JsonBody:
        resp = self.aclient.do(**self._const_kwargs(messages=messages, stream=False))
        self._update_costs(resp.body.get("usage", {}))
        return resp.body

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> JsonBody:
        resp = await self.aclient.ado(**self._const_kwargs(messages=messages, stream=False))
        self._update_costs(resp.body.get("usage", {}))
        return resp.body

    async def acompletion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> JsonBody:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        resp = await self.aclient.ado(**self._const_kwargs(messages=messages, stream=True))
        collected_content = []
        usage = {}
        async for chunk in resp:
            content = chunk.body.get("result", "")
            usage = chunk.body.get("usage", {})
            collected_content.append(content)

        self._update_costs(usage)
        full_content = "".join(collected_content)
        print(full_content)
        start_index = full_content.find("```json")
        end_index = full_content.rfind("```")
        result = full_content[start_index+8:end_index]
        return result
    
    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """when streaming, print each token in place."""
        if stream:
            return await self._achat_completion_stream(messages)
        rsp = await self._achat_completion(messages)
        print(rsp)
        return self.get_choice_text(rsp)