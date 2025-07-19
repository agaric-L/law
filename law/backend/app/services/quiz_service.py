import json
import os
from tokenize import Expfloat
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, SecretStr
from typing import List
import random
from langchain_openai import ChatOpenAI

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]

class QuizAnswerRequest(BaseModel):
    id: int
    answer: int  # 0,1,2,3

class QuizAnswerResponse(BaseModel):
    correct: bool
    correct_answer: int
    explanation: str = ""

# 读取题库 JSON 文件
DATA_PATH = os.path.join(os.path.dirname(__file__), '../data/law_questions.json')
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    _questions = json.load(f)

# 将答案字母转为索引
for q in _questions:
    answer = q.get('answer')
    if isinstance(answer, str) and answer and answer[0] in 'ABCD':
        q['answer'] = ord(answer[0]) - ord('A')
    elif isinstance(answer, str) and answer and answer[0] in '0123':
        q['answer'] = int(answer[0])
    # 其他情况可根据需要补充
MODEL_CONFIG = {
    '智谱': {
        'api_key': os.environ.get('ZHIPU_API_KEY', ''),
        'model': os.environ.get('ZHIPU_MODEL', 'glm-4'),
        'url': os.environ.get('ZHIPU_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions'),
    },
}
def generate_explanation(question, options, correct_answer):
    # 构造 prompt
    prompt = f"请为以下法律选择题生成详细的纯文本解析（不要超过250字）：\n题目：{question}\n选项：{options}\n正确答案：{options[correct_answer]}"
    # 调用大模型
    conf = MODEL_CONFIG['智谱']
    llm = ChatOpenAI(
        model=conf['model'],
        base_url=conf['url'],
        api_key=SecretStr(conf['api_key']),
        temperature=0.2
    )
    # 通过 generation_config 传递 max_tokens
    ai_msg = llm.invoke(
        [HumanMessage(content=prompt)],
    )
    # 统一处理为字符串
    result = ai_msg.content if hasattr(ai_msg, 'content') else ai_msg
    if isinstance(result, str):
        return result
    elif isinstance(result, list):
        return "\n".join(str(item) for item in result)
    elif isinstance(result, dict):
        return str(result)
    else:
        return str(result)

def generate_explanation_stream(question, options, correct_answer):
    prompt = f"请为以下法律选择题生成详细的纯文本解析（不要超过250字）：\n题目：{question}\n选项：{options}\n正确答案：{options[correct_answer]}"
    conf = MODEL_CONFIG['智谱']
    llm = ChatOpenAI(
        model=conf['model'],
        base_url=conf['url'],
        api_key=SecretStr(conf['api_key']),
        temperature=0.2,
        stream=True
    )
    messages = [HumanMessage(content=prompt)]
    for chunk in llm.stream(messages):
        yield chunk.content

def get_random_question():
    q = random.choice(_questions)
    return QuizQuestion(id=q['id'], question=q['question'], options=q['options'])

def get_all_questions():
    questions = [QuizQuestion(id=q['id'], question=q['question'], options=q['options']) for q in _questions]
    random.shuffle(questions)
    return questions

def check_answer(qid: int, answer: int) -> QuizAnswerResponse:
    for q in _questions:
        if q['id'] == qid:
            correct = (answer == q['answer'])
            explanation = generate_explanation(q['question'], q['options'], q['answer'])
            return QuizAnswerResponse(correct=correct, correct_answer=q['answer'], explanation=explanation)
    return QuizAnswerResponse(correct=False, correct_answer=-1, explanation="题目不存在")
