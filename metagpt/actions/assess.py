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
As a Preliminary Evaluator, you will perform the assess operation.
Your goal is to generate a report about the patient. This report is mainly written in the "Patient_Info" section of the output.
In this operation, you need to receive and carefully analyze the patient's medical history, current symptoms, and basic physical data such as height, weight, etc. These information are provided in the "user requirements" section.
In addition, the database provides information on possible diseases that this population may suffer from, which is available in the "knowledges" section.
The database also provides some suggestions on the patient's diet, which are available in the "knowledges" section.
Synthesize this information. The content of the "knowledges" section is for reference only, you need to have your own thinking.
This analysis does not need to include other content, and there is no need to point out the incompleteness of the information provided by the patient.
The disease list will provide an important reference for subsequent doctor diagnosis, so it is necessary to ensure the comprehensiveness and accuracy of the listed diseases.

Output an appropriate JSON format file, referring to the format example.
Remember, don't output any irrelevant content outside the JSON! No need for "json" and ""
The most important thing is: you must output your answer in Chinese.

The report requirements are as follows, divided into four parts:
## Patient_Info: Provided as Python str, analyze the patient's condition, try to include all the information in the "user requirements", and this part must be fully detailed!!!
## Disease_List: Provided as Python list[str], a detailed list of possible infections the patient may have contracted, combining your own understanding of the patient and the information provided by "konwledges". It should include at least three diseases. This part should be concise.
## Eat_Recommand: Provided as Python str, listing the patient's recommended and non-recommended diets. This part should be concise.
## Eat_List: Provided as Python list[str], listing the patient's diet, without outputting any content other than the food eaten by the patient. This part should be concise.


##
user requirements:
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
    "Patient_Info": "", 
    "Disease_List": [],
    "Eat_Recommand": "", 
    "Eat_List": []
}
'''

OUTPUT_MAPPING = {
    "Patient_Info": (str, ...), 
    "Disease_List": (List[str], ...),
    "Eat_Recommand": (str, ...), 
    "Eat_List": (List[str], ...), 
}


class Assess(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, requirements, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        requirement = requirements[0].content
        infos = json.loads(requirement)
        medical_history = infos['medical_history']
        symptoms = infos['symptoms']

        disease_info = 'medical_history: ' + medical_history + '   ' + 'symptoms: ' + symptoms
        knowledges = await self.ask_db(disease_info, 'medical', 3)
        for ids, k  in enumerate(knowledges):
            knowledges[ids] = {"name": k['name'], 
                               "desc": k['desc'][:100] + '...', 
                               "symptom": k['symptom'], 
                               "acompany": k['acompany'], 
                               "do_eat": k.get('do_eat'), 
                               "not_eat": k.get('not_eat'), 
                               "recommand_eat": k.get('recommand_eat')}


        prompt = template.format(requirements=requirement, knowledges=str(knowledges), format_example=format_example)
        logger.debug(prompt)
        article = await self._aask_v1(prompt, "assessment", OUTPUT_MAPPING)
        
        with open(PROJECT_ROOT / 'results/assessment.txt', "w", encoding='utf-8') as f:
            f.write(json.dumps(dict(article.instruct_content)))
            f.close()
            
        return article