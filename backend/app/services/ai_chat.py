from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage

# 可根据需要引入其他langchain集成的模型
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI

MODEL_CONFIG = {
    '通义千问': {
        'api_key': os.environ.get('QWEN_API_KEY', ''),
        'model': os.environ.get('QWEN_MODEL', 'qwen-turbo'),
        'url': os.environ.get('QWEN_URL',
                              'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'),
    },
    '星火大模型': {
        'api_key': os.environ.get('SPARK_API_KEY', ''),
        'model': os.environ.get('SPARK_MODEL', 'x1'),
        'url': os.environ.get('SPARK_URL', 'https://spark-api-open.xf-yun.com/v2/chat/completions'),
    },
    'deepseek': {
        'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
        'model': os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
        'url': os.environ.get('DEEPSEEK_URL', 'https://api.deepseek.com/v1/chat/completions'),
    },
    '智谱': {
        'api_key': os.environ.get('ZHIPU_API_KEY', ''),
        'model': os.environ.get('ZHIPU_MODEL', 'glm-4'),
        'url': os.environ.get('ZHIPU_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions'),
    },
}


def reset_ai_legal_memory():
    print("memory reset")
    if hasattr(ai_legal_qa_function, 'memory'):
        del ai_legal_qa_function.memory


def ai_legal_qa_function(question: str, model: str = 'qwen') -> dict:
    print("memory id:", id(ai_legal_qa_function.memory) if hasattr(ai_legal_qa_function, 'memory') else "no memory")
    # 静态变量/全局变量，保证多轮对话记忆
    if not hasattr(ai_legal_qa_function, 'memory'):
        ai_legal_qa_function.memory = ConversationBufferMemory(return_messages=True)
    memory = ai_legal_qa_function.memory

    # 构建prompt
    system_prompt = (
        "你作为专业法律助手，严格参考用户的历史提问，结合历史问题的关键词，再结合当前问题，严格按照以下格式分四部分输出：\n"
        "1. 法律条文依据：\n[在这里详细列出相关的法律条文和依据]\n\n"
        "2. 参考案例：\n[在这里提供相关的参考案例]\n\n"
        "3. 实际解决办法：\n[在这里提供具体的解决步骤和建议]\n"
        "4. 总结回答：\n[在这里总结总体的回答，包括法律条文依据、参考案例和实际解决办法，并针对问题给出具体的回答]\n"
    )

    model_key = model.lower()
    if model_key not in MODEL_CONFIG:
        raise ValueError(f"暂不支持的模型: {model}")
    conf = MODEL_CONFIG[model_key]
    llm = ChatOpenAI(
        model=conf['model'],
        base_url=conf['url'],
        api_key=conf['api_key'],
        temperature=0.2,
        max_tokens=1024
    )

    # 获取历史对话
    chat_history = memory.load_memory_variables({})['history']
    # 组装messages
    messages = []
    for msg in chat_history:
        if isinstance(msg, str):
            messages.append(HumanMessage(content=msg))
        else:
            messages.append(msg)

    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=question)]
    response = response = llm.invoke(messages)
    answer = response.content.strip()

    # 追加本轮用户输入
    memory.save_context({"input": question}, {"output": answer})

    # 自动分段解析
    import re
    def parse_answer(ans):
        law, case, solution, summary = '', '', '', ''
        # 优化分割逻辑，兼容更多格式
        patterns = [
            r'1[、.、．]? ?法律条文依据[:：]?\s*(.*?)(?:\n|\r|$)2[、.、．]? ?参考案例[:：]?\s*(.*?)(?:\n|\r|$)3[、.、．]? ?实际解决办法[:：]?\s*(.*?)(?:\n|\r|$)4[、.、．]? ?总结回答[:：]?\s*(.*)',
            r'1[、.、．]? ?法律条文依据[:：]?\s*(.*?)(?:2[、.、．]? ?参考案例[:：]?)(.*?)(?:3[、.、．]? ?实际解决办法[:：]?)(.*?)(?:4[、.、．]? ?总结回答[:：]?)(.*)',
            r'1[、.、．]? ?(.*?)(2[、.、．]? ?)(.*?)(3[、.、．]? ?)(.*?)(4[、.、．]? ?)(.*)'
        ]
        for pattern in patterns:
            m = re.search(pattern, ans, re.S)
            if m:
                if len(m.groups()) == 4:
                    law = m.group(1).strip()
                    case = m.group(2).strip()
                    solution = m.group(3).strip()
                    summary = m.group(4).strip()
                elif len(m.groups()) == 5:
                    law = m.group(1).strip()
                    case = m.group(2).strip()
                    solution = m.group(3).strip()
                    summary = m.group(5).strip()
                elif len(m.groups()) == 7:
                    law = m.group(1).strip()
                    case = m.group(3).strip()
                    solution = m.group(5).strip()
                    summary = m.group(7).strip()
                break
        # 2. 如果没有分割成功，尝试按换行和数字分割
        if not law and not case:
            parts = re.split(r'\n?\d+[、.、．]?[. ]?', ans)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 4:
                law = parts[0]
                case = parts[1]
                solution = parts[2]
                summary = parts[3]
            elif len(parts) == 3:
                law = parts[0]
                case = parts[1]
                solution = parts[2]
            elif len(parts) == 2:
                law = parts[0]
                solution = parts[1]
            elif len(parts) == 1:
                solution = parts[0]
        # 3. 如果还是没有，尝试按关键词分割
        if not law and not case:
            law_match = re.search(r'法律条文依据[:：]?\s*(.*?)(参考案例[:：]?|实际解决办法[:：]?|总结回答[:：]?|$)', ans,
                                  re.S)
            if law_match:
                law = law_match.group(1).strip()
            case_match = re.search(r'参考案例[:：]?\s*(.*?)(实际解决办法[:：]?|总结回答[:：]?|$)', ans, re.S)
            if case_match:
                case = case_match.group(1).strip()
            solution_match = re.search(r'实际解决法[:：]?\s*(.*?)(总结回答[:：]?|$)', ans, re.S)
            if solution_match:
                solution = solution_match.group(1).strip()
            summary_match = re.search(r'总结回答[:：]?\s*(.*)', ans, re.S)
            if summary_match:
                summary = summary_match.group(1).strip()
        return law, case, solution, summary

    def clean_text(text):
        import re
        # 去除markdown标题、粗体、列表等符号
        text = re.sub(r'[#*`>\-]+', '', text)
        # 去除AI返回的JSON片段和usage等调试信息
        text = re.sub(r'\{\s*"total_tokens"[\s\S]*?\}', '', text)
        text = re.sub(r'"usage"[\s\S]*?\}', '', text)
        text = re.sub(r'"request_id"[\s\S]*?\}', '', text)
        text = re.sub(r'\{\s*"cached_tokens"[\s\S]*?\}', '', text)
        # 将\n或\\n等转为真正换行
        text = text.replace('\\n', '\n').replace('\\r', '').replace('\r', '').replace('\n', '\n')
        # 连续多行空行合并为一个
        text = re.sub(r'\n{2,}', '\n', text)
        # 去除首尾空白
        text = text.strip()
        # 去除通义千问答案结尾的'}}]},,'等异常符号
        text = re.sub(r'"[}}\]\]},,]+$', '', text)
        return text

    law, case, solution, summary = map(clean_text, parse_answer(answer))
    return {
        'law': law,
        'case': case,
        'solution': solution,
        'summary': summary,
        'history': chat_history + [HumanMessage(content=question), SystemMessage(content=answer)]
    }
