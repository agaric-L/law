import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import re

#加入AI处理数据库检索结果
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from pydantic import SecretStr

MODEL_CONFIG = {
    '星火大模型': {
        'api_key': os.environ.get('SPARK_API_KEY', ''),
        'model': os.environ.get('SPARK_MODEL', 'x1'),
        'url': os.environ.get('SPARK_URL', 'https://spark-api-open.xf-yun.com/v2/chat/completions'),
    },
    
}

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "law_code"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def summarize_law_results(results, query):
    # 拼接检索结果为结构化内容
    law_blocks = []
    case_blocks = []
    for item in results:
        if item['type'] == 'law':
            law_blocks.append({
                "title": item['title'],
                "content": ''.join(item['details'])
            })
        else:
            case_blocks.append({
                "title": item['title'],
                "content": ' '.join(item['details'])
            })
    # 优化后的结构化prompt，要求AI输出标准JSON
    prompt = f"""
你现在需要扮演一个法律文本结构化工具，将用户输入关键字相关的法律条文，整理成如下结构化JSON格式输出，不要输出任何解释说明：

{{
  "laws": [
    {{"title": "第...条", "content": "...（对应法条内容，简要描述）"}},
    ...
  ]
}}

请严格按照上述JSON格式输出，laws为数组，字段含义见示例。详细内容提取概要精简输出，不要输出多余内容。

用户查询：{query}

已检索到的法律条文：
{chr(10).join([f'{l["title"]} {l["content"]}' for l in law_blocks])}
"""
    conf = MODEL_CONFIG['星火大模型']
    llm = ChatOpenAI(
        model=conf['model'],
        base_url=conf['url'],
        api_key=SecretStr(conf['api_key']),
        temperature=0.3
    )
    response = llm([HumanMessage(content=prompt)])
    import json, re
    def extract_json_str(s):
        s = s.strip()
        match = re.search(r'```json([\s\S]*?)```', s)
        if match:
            return match.group(1).strip()
        match = re.search(r'```([\s\S]*?)```', s)
        if match:
            return match.group(1).strip()
        match = re.search(r'({[\s\S]*})', s)
        if match:
            return match.group(1).strip()
        return s
    def try_json_loads(s):
        try:
            return json.loads(s)
        except Exception:
            return None
    result = response.content if hasattr(response, 'content') else str(response)
    if isinstance(result, list):
        result = '\n'.join([str(x) for x in result])
    result = result.strip()
    json_str = extract_json_str(result)
    data = try_json_loads(json_str)
    if not data:
        return {"laws": law_blocks, "cases": case_blocks, "raw": result}
    return data

def search_law(query, top_k=5):
    query_vec = model.encode([query])[0]
    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vec,
        limit=top_k
    )
    results = []
    for hit in hits:
        payload = hit.payload
        if not payload:
            continue
        text = payload['text']
        data_type = payload.get('type', 'law')
        if data_type == 'law':
            m = re.match(r"^(第[\d一二三四五六七八九十百千万]+条.*?)([\n\r]+|$)(.*)", text, re.DOTALL)
            if m:
                title = m.group(1)
                details = [line.strip() for line in m.group(3).split('\n') if line.strip()]
            else:
                title = text
                details = []
        else:  # case
            lines = text.split('\n')
            title = lines[0]
            details = [line.strip() for line in lines[1:] if line.strip()]
        results.append({"type": data_type, "title": title, "details": details})
    # AI摘要
    summary = summarize_law_results(results, query)
    return {
        "summary": summary,
        "raw_results": results
    }