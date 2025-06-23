from metagpt.const import PROJECT_ROOT
import json

def get_result():
    """
    :return assessment 一个字典包括初步评估的内容
    :return doctor 一个字典包括doctor的所有回复
    :return nutritionist 一个字典包括nutritionist的所有回复
    :return summary 一个字符串包括最后的总结
    """
    with open(PROJECT_ROOT / 'results/doctor.txt', "r", encoding='utf-8') as f:
        d = json.load(f)
    with open(PROJECT_ROOT / 'results/assessment.txt', "r", encoding='utf-8') as f:
        a = json.load(f)
    with open(PROJECT_ROOT / 'results/nutritionist.txt', "r", encoding='utf-8') as f:
        n = json.load(f)
    with open(PROJECT_ROOT / 'results/summary.txt', "r", encoding='utf-8') as f:
        s = f.read()

    res = {'assessment': a, 'doctor': d, 'nutritionist': n, 'summary': s}
    with open(PROJECT_ROOT / 'results/result.json', "w", encoding='utf-8') as f:
        f.write(json.dumps(res))
        f.close()
    return res