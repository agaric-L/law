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
    law_blocks = []
    case_blocks = []
    for item in results:
        if item['type'] == 'law':
            law_blocks.append({
                "title": item['title'],  # 如“第X条”
                "content": '\n'.join(item['details'])  # 保证内容换行
            })
        else:
            case_blocks.append({
                "title": item['title'],  # 如“案例：XXX”
                "content": '\n'.join(item['details'])
            })
    return {
        "laws": law_blocks,
        "cases": case_blocks
    }

def search_law(query, top_k=20):
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
            m = re.match(r"^(第[\d一二三四五六七八九十百千万]+条)[，。:：\\s]*(.*)", text, re.DOTALL)
            if m:
                title = m.group(1)
                content = m.group(2).strip()
                details = [line.strip() for line in content.split('\n') if line.strip()]
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