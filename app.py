from flask import  Flask, render_template, request, jsonify
from flask_frozen import Freezer
from openai import AsyncOpenAI
from metagpt.config import CONFIG

from metagpt.roles import (
    PreliminaryEvaluator, 
    Doctor, 
    Nutritionist, 
    Summarizer, 
)
from metagpt.team import Team
from metagpt.utils.get_result import get_result
from metagpt.const import PROJECT_ROOT
import json

app = Flask(__name__, template_folder='./templates')
params = []
round = 0

company = Team()

prompt_bot = '''
You are a medical robot and you will be facing a patient.
Your consultation with the patient is divided into two stages, You need to judge which stage the conversation is currently in.

Stage 1:
Inquire information from the patient.
For each output, you need to inquire information from the patient about their condition. You will need to determine the content of your inquiries yourself.
Before the end of all conversations, you must collect all the information listed in the "content" section. Additionally, you can ask about the patient's diet, lifestyle habits, and other relevant factors that may help in assessing the patient's condition.
You and the patient have already engaged in some dialogue, which is recorded in the "context" section.
If you believe you have collected all the information you need, just output "over" without quotation marks.

Stage 2:
you will receive a report about the patient. 
ask the patient if they have any further questions. 
If the patient has any questions, try your best to answer them.
no need to output "阶段二: "

Notes:
You only need to output your own content.
for each output, you can only discuss one topic.
If you haven't introduced yourself, you should do so first.
If you feel that you have already obtained a particular piece of information listed in the "content" section, do not ask about it again.
If the patient discusses irrelevant topics with you, it is expected that you can smoothly steer the conversation back to the original topic.
You must ensure the fluency and coherence of the conversation.
You need to answer in Chinese, Except for "over" which indicates the end of the conversation.

## context
{context}

## content
    ## symptoms, the symptoms experienced by the patient.
    ## medical_history, the patient's medical records.
    ## eating_habits, the patient's eating habits in recent days.
'''

prompt_summary = '''
You need to summarize a JSON file based on the content in "content".
Output an appropriate JSON format file, referring to the format example.
Remember, don't output any irrelevant content outside the JSON! No need for "json" and ""
The most important thing is: you must output your answer in Chinese.

The requirements for the content of the JSON file are as follows:
    ## symptoms, provided as a python string, representing the symptoms experienced by the patient.
    ## medical_history, provided as a python string, representing the patient's medical history.
    ## eating_habits, provided as a python list of strings, a list of foods representing the patient's recent eating habits.
    ## longterm_eating_habits, provided as a python list of strings, a list of foods representing the patient's long-term eating habits.
    ## additional_eating_habits, provided as a python list of strings, a list of foods representing the patient's additional eating habits.
    ## sleep_time, provided as a python string, representing the patient's sleep duration.
    ## bad_lifestyle, provided as a python string, representing the patient's unhealthy habits.
    ## additional_lifestyle, provided as a python string, representing any additional lifestyle habits of the patient.

## content:
{context}

## format_example:
{format_example}
'''

format_example = '''
{
    "age": "",
    "symptoms": "",
    "height_weight": "",
    "medical_history": "",
    "eating_habits": [],
    "longterm_eating_habits": [],
    "additional_eating_habits": [],
    "sleep_time": "",
    "bad_lifestyle": "",
    "additional_lifestyle": "",
}
'''

context = '''
'''

async def _achat_completion(messages: list[dict]) -> dict:
    aclient = AsyncOpenAI(api_key=CONFIG.openai_api_key, base_url=CONFIG.base_url)
    rsp = await aclient.chat.completions.create(
        messages=messages,
        model=CONFIG.openai_api_model
    )
    return rsp

def get_choice_text(rsp: dict) -> str:
    return rsp.choices[0].message.content

async def ask_gpt(question):
    msg = [{'role': 'user', 'content': question}]
    rsp = await _achat_completion(msg)
    return get_choice_text(rsp)

@app.route('/show', methods=['GET'])
async def show():
    global context
    # hello = "你好，我的名字叫计算机设计大赛"
    res = get_result()
    patient_info = res["assessment"]["Patient_Info"]
    disease_list = " ".join(map(str, res["assessment"]["Disease_List"]))
    eat_recommend = res["assessment"]["Eat_Recommand"]
    
    doctor_disease = res["doctor"]["Disease"]
    cause = res["doctor"]["Cause"]
    doctor_solution = res["doctor"]["Solution"]
    doctor_suggestion = res["doctor"]["Suggestion"]
    
    nutritionist_do_eat = " ".join(map(str, res["nutritionist"]["do_eat"]))
    nutritionist_not_eat = " ".join(map(str, res["nutritionist"]["not_eat"]))
    nutritionist_solution = res["nutritionist"]["Solution"]
    
    summary = res["summary"]
    context += "bot: {res}".format(res=summary)
    return render_template('/description.html', patient_info=patient_info, disease_list=disease_list, eat_recommend=eat_recommend, doctor_disease=doctor_disease, cause=cause, doctor_solution=doctor_solution, doctor_suggestion=doctor_suggestion, nutritionist_do_eat=nutritionist_do_eat, nutritionist_not_eat=nutritionist_not_eat, nutritionist_solution=nutritionist_solution, summary=summary)

@app.route('/clear', methods=['POST'])
def clear():
    global context, round
    context = ''
    round = 0
    return 'ee'

@app.route('/discuss', methods=['POST'])
async def discuss():
    global round
    response = {}
    if round == 0:
        company.hire(
            [
                PreliminaryEvaluator(), 
                Doctor(), 
                Nutritionist(), 
                Summarizer(), 
            ]
        )
        idea = await ask_gpt(prompt_summary.format(context=context, format_example=format_example))
        company.invest(3.0)
        company.start_project(idea)
        await company.run()
        f = open(PROJECT_ROOT / 'results/assessment.txt', "r", encoding='utf-8')
        a = json.load(f)
        response = {
            'pre': a['Patient_Info']
            # 'pre': 'you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you ',
        }
    else:
        await company.run()
        f = open(PROJECT_ROOT / 'results/doctor.txt', "r", encoding='utf-8')
        d = json.load(f)
        f = open(PROJECT_ROOT / 'results/nutritionist.txt', "r", encoding='utf-8')
        n = json.load(f)
        response = {
            'doctor': d['Discuss'],
            'nutritionist': n['Discuss'],
            # 'doctor': 'you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you ',
            # 'nutritionist': 'you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you you ',
        }
    round += 1
    return jsonify(response)

@app.route('/getHistory', methods=['POST'])
def getHistory():
    global context
    with open('results/history.json', 'r') as f:
        try:
            datas = request.json['message']
            res = json.load(f)
            context = str(res[int(datas)-1])
        except:
            res = json.load(f)
        print(context)
        return res

@app.route('/saveHistory', methods=['POST'])
def saveHistory():
    datas = request.json['message']
    with open('results/history.json', 'w') as f:
        f.write(json.dumps(datas))
        return "ee"

@app.route('/delete', methods=['POST'])
def delete():
    datas = request.form['message']
    with open('results/history.json', 'r') as f:
        res = json.load(f)
        ids = []
        for _id in list(datas.split(',')):
            try:
                ids.append(int(_id))
            except:
                continue
        ids.sort(reverse=True)
        for x in ids:
            try:
                res.pop(x-1)
            except: continue
    with open('results/history.json', 'w') as f:
        f.write(json.dumps(res))

@app.route('/', methods=['GET', 'POST'])
async def index():
    global params, context
    
    if request.method == 'GET':
        return render_template('/index.html')
    if request.method == 'POST':
        question = request.json['message']     # 获取POST请求中的question字段
        context += "patient: {question}\n".format(question=question)
        answer = await ask_gpt(prompt_bot.format(context=context))      # 获取GPT-3的回答
        # 将回答以JSON格式返回
        response = {
            'answer': answer
            # 'answer': 'over'
        }
        context += "bot: {answer}\n".format(answer=answer)
        return jsonify(response)    # 返回JSON格式的响应

if __name__ == '__main__':
    app.run(debug=True)
    freezer = Freezer(app)
    freezer.freeze()