#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd.py
"""
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.const import PROJECT_ROOT

template = """
As a Summarizer, you will perform a summary operation. In this process, you need to summarize and analyze the analysis results from both the Nutritionist and the Doctor.
Your task is to synthesize this information, extract key points and core viewpoints, and form a concise and to-the-point overview.
This overview will serve as the concluding section of the final report, providing readers with a clear and comprehensive summary.
Please ensure that your summary accurately reflects the analyses of the various professionals involved, while also being highly generalized and readable.
Keep in mind that your output will be directly presented to the patient, so use a caring tone.
Do not output any content unrelated to the summary.

##
context:
{requirements} 
"""

class Summary(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, requirements, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        prompt = template.format(requirements=requirements)
        logger.debug(prompt)
        article = await self._aask(prompt)
        with open(PROJECT_ROOT / 'results/summary.txt', "w", encoding='utf-8') as f:
            f.write(article)
            f.close()
        return article
