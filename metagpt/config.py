#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provide configuration, singleton
"""
import os

import openai
import yaml

from metagpt.const import PROJECT_ROOT
from metagpt.logs import logger
from metagpt.utils.singleton import Singleton


class NotConfiguredException(Exception):
    """Exception raised for errors in the configuration.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="The required configuration is not set"):
        self.message = message
        super().__init__(self.message)


class Config(metaclass=Singleton):
    """
    Regular usage method:
    config = Config("config.yaml")
    secret_key = config.get_key("MY_SECRET_KEY")
    print("Secret key:", secret_key)
    """

    _instance = None
    key_yaml_file = PROJECT_ROOT / "config/key.yaml"
    default_yaml_file = PROJECT_ROOT / "config/config.yaml"

    def __init__(self, yaml_file=default_yaml_file):
        self._configs = {}
        self._init_with_config_files_and_env(self._configs, yaml_file)
        logger.info("Config loading done.")
        self.base_url = self._get("OPENAI_API_BASE")
        self.global_proxy = self._get("GLOBAL_PROXY")
        self.openai_api_key = self._get("OPENAI_API_KEY")
        self.anthropic_api_key = self._get("Anthropic_API_KEY")
        if (not self.openai_api_key or "YOUR_API_KEY" == self.openai_api_key) and (
                not self.anthropic_api_key or "YOUR_API_KEY" == self.anthropic_api_key
        ):
            raise NotConfiguredException("Set OPENAI_API_KEY or Anthropic_API_KEY first")
        self.openai_api_base = self._get("OPENAI_API_BASE")
        openai_proxy = self._get("OPENAI_PROXY") or self.global_proxy
        if openai_proxy:
            openai.proxy = openai_proxy
            openai.api_base = self.openai_api_base
        self.openai_api_type = self._get("OPENAI_API_TYPE")
        self.openai_api_version = self._get("OPENAI_API_VERSION")
        self.openai_api_rpm = self._get("RPM", 3)
        self.openai_api_model = self._get("OPENAI_API_MODEL", "gpt-4")
        self.max_tokens_rsp = self._get("MAX_TOKENS", 2048)
        self.deployment_name = self._get("DEPLOYMENT_NAME")
        self.deployment_id = self._get("DEPLOYMENT_ID")

        self.qianfan_access_key = self._get("QIANFAN_ACCESS_KEY")
        self.qianfan_api_key = self._get("QIANFAN_API_KEY")
        self.qianfan_secret_key = self._get("QIANFAN_SECRET_KEY")
        self.qianfan_model = self._get("QIANFAN_MODEL")
        self.qianfan_endpoint = self._get("QIANFAN_ENDPOINT")
        self.qianfan_calc_usage = self._get("QIANFAN_CALC_USAGE")
        self.qianfan_temperature = self._get("QIANFAN_TEMPERATURE")

        self.max_budget = self._get("MAX_BUDGET", 10.0)
        self.total_cost = 0.0

        self.calc_usage = self._get("CALC_USAGE", True)


        self.prompt_format = self._get("PROMPT_FORMAT", "markdown")

    def _init_with_config_files_and_env(self, configs: dict, yaml_file):
        """Load from config/key.yaml, config/config.yaml, and env in decreasing order of priority"""
        configs.update(os.environ)

        for _yaml_file in [yaml_file, self.key_yaml_file]:
            if not _yaml_file.exists():
                continue

            # Load local YAML file
            with open(_yaml_file, "r", encoding="utf-8") as file:
                yaml_data = yaml.safe_load(file)
                if not yaml_data:
                    continue
                os.environ.update({k: v for k, v in yaml_data.items() if isinstance(v, str)})
                configs.update(yaml_data)

    def _get(self, *args, **kwargs):
        return self._configs.get(*args, **kwargs)

    def get(self, key, *args, **kwargs):
        """Search for a value in config/key.yaml, config/config.yaml, and env; raise an error if not found"""
        value = self._get(key, *args, **kwargs)
        if value is None:
            raise ValueError(f"Key '{key}' not found in environment variables or in the YAML file")
        return value


CONFIG = Config()
