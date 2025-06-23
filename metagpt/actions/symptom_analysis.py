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

template = """
As a Doctor, you will perform a symptom_analysis operation.
During this process, you will conduct an in-depth analysis of the nature, duration, and severity of the patient's symptoms based on the analysis results provided by others. (The analysis results of others are provided in the "context" section.)
Additionally, the database offers information including the causes, descriptions, prevention methods, treatments, and therapeutic drugs for various diseases. (The resources provided by the database are saved in the "knowledges" section.)
Your goal is to comprehensively analyze this information and generate a detailed report about the patient.
Please ensure that your analysis is comprehensive and in-depth to provide the most accurate diagnosis and treatment recommendations for the patient.
The output of the "Solution" and "Suggestion" sections are directly readable by the patient. Please describe the results in a caring tone.

Output an appropriate JSON format file, referring to the format example for guidance.
Remember, do not output any irrelevant content outside of the JSON format! There is no need for "json" and "" delimiters.
The most important thing is: you must output your answer in Chinese.

The report should be structured as follows, divided into four sections:
## Discuss: Provided as Python str, according to the content in 'context', discuss with others and give your views.
## Disease: Provided as Python str, indicating the most likely disease the patient may have contracted.
## Cause: Provided as Python str, specifying the specific cause of the patient's condition.
## Solution: Provided as Python str, based on a comprehensive understanding of therapeutic drugs, treatment methods, and prevention measures, provide medical advice that is conducive to the patient's recovery. This section must be fully detailed!
## Suggestion: Provided as Python str, indicating whether the patient should be advised to visit a hospital for further examination, along with detailed medical advice. This section must also be fully detailed!


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
    "Disease": "", 
    "Cause": "", 
    "Solution": "", 
    "Suggestion": ""
}
'''

OUTPUT_MAPPING = {
    "Discuss": (str, ...),
    "Disease": (str, ...),
    "Cause": (str, ...),
    "Solution": (str, ...), 
    "Suggestion": (str, ...), 
}

class SymptomAnalysis(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, requirements, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        requirement = dict(requirements[0].instruct_content)
        assessment = requirement.get('Disease_List')
        knowledges = []
        if assessment != None:
            for ids, disease in enumerate(assessment):
                if (ids >= 3): break
                k = await self.ask_db(disease, 'medical', 1)
                k = k[0]
                k = {
                    "name": k.get("name"),
                    "desc": k.get("desc")[:600] + '...', 
                    "prevent": k.get('prevent'),
                    "cause": k.get('cause')[:600] + '...',
                    "cure_department": k.get('cure_department'),
                    "cure_way": k.get('cure_way'),
                    "cure_lasttime": k.get('cure_lasttime'),
                    "cured_prob": k.get('cured_prob'),
                    "cost_money": k.get('cost_money'),
                    "check": k.get('check'),
                    "common_drug": k.get('common_drug'), 
                    "recommand_drug": k.get('recommand_drug'),
                }
                knowledges.append(str(k))

        prompt = template.format(requirements=requirements, knowledges='\n'.join(knowledges), format_example=format_example)
        logger.debug(prompt)
        article = await self._aask_v1(prompt, "doctor", OUTPUT_MAPPING)
        with open(PROJECT_ROOT / 'results/doctor.txt', "w", encoding='utf-8') as f:
            f.write(json.dumps(dict(article.instruct_content)))
            f.close()
        return article
