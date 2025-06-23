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
import json
import re


template = """
As a Nutritionist, you will conduct a diet_analysis.
During this process, you need to carefully analyze the results provided by others, taking into account the types of food consumed, portion sizes, meal times, and any specific dietary preferences the patient may have. (The analysis results from others are provided in the "context" section.)
In addition, the patient's dietary history, lifestyle, and recent changes in eating habits are also important factors to consider in the analysis.
To make a more accurate assessment, you will also need to utilize database resources to query basic information about relevant foods. (The resources provided by the database are saved in the "knowledges" section.)
Your goal is to give the patient personalized dietary advice.
The content of the "knowledges" section is for reference only, you need to have your own thinking.
The output of the "Solution" sections are directly readable by the patient. Please describe the results in a caring tone.

Output a properly formatted JSON file, referring to the format example for guidance.
Remember, do not output any irrelevant content outside of the JSON format! There is no need for "json" and "" delimiters.
The most important thing is: you must output your answer in Chinese.

The advice should be structured as follows, divided into three parts:
## Discuss: Provided as Python str, according to the content in 'context', discuss with others and give your views.
## do_eat: Provided as Python list[str], listing the recommended foods for the patient to eat. Keep this section concise.
## not_eat: Provided as Python list[str], listing the foods that are not recommended for the patient. Keep this section concise.
## Solution: Provided as Python str, offering personalized dietary recommendations to help the patient improve their eating habits and promote health. This section should be detailed!


##
context: 
{requirements}

##
knowledges: 
{knowledges}

##
format example: 
{format_example}
"""


format_example = '''
{
    "Discuss": "",
    "do_eat": [], 
    "not_eat": [], 
    "Solution": ""
}
'''

OUTPUT_MAPPING = {
    "Discuss": (str, ...),
    "do_eat": (List[str], ...),
    "not_eat": (List[str], ...), 
    "Solution": (str, ...), 
}


class DietAnalysis(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, requirements, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        requirement = dict(requirements[0].instruct_content)

        foods = requirement.get('Eat_List')
        knowledges = []
        if foods != None:
            for food in foods:
                k = await self.ask_db(food, 'food', 1)
                k = k[0]
                knowledges.append(str(k))


        prompt = template.format(requirements=requirements, knowledges='\n'.join(knowledges), format_example=format_example)
        logger.debug(prompt)
        article = await self._aask_v1(prompt, "nutritionist", OUTPUT_MAPPING)
        with open(PROJECT_ROOT / 'results/nutritionist.txt', "w", encoding='utf-8') as f:
            f.write(json.dumps(dict(article.instruct_content)))
            f.close()
        return article
