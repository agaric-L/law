import re
from langchain_community.document_loaders import Docx2txtLoader
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "law_code"

files = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../民法典.docx")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../民法判例百选.docx"))
]

chunks = []
for file in files:
    print(f"正在处理文件: {file}")
    loader = Docx2txtLoader(file)
    docs = loader.load()
    if "民法典" in file:
        data_type = "law"
        for doc in docs:
            lines = doc.page_content.split('\n')
            current_chunk = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if re.match(r"^第[\d一二三四五六七八九十百千万]+条", line):
                    if current_chunk:
                        chunks.append({"text": current_chunk, "type": data_type})
                    current_chunk = line
                else:
                    current_chunk += "\n" + line
            if current_chunk:
                chunks.append({"text": current_chunk, "type": data_type})
    else:
        data_type = "case"
        for doc in docs:
            lines = doc.page_content.split('\n')
            current_chunk = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if re.match(r".*案$", line) or re.match(r".*判决书$", line):
                    if current_chunk:
                        chunks.append({"text": current_chunk, "type": data_type})
                    current_chunk = line
                else:
                    current_chunk += "\n" + line
            if current_chunk:
                chunks.append({"text": current_chunk, "type": data_type})

print(f"共提取{len(chunks)}条文本，开始向量化...")

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode([c["text"] for c in chunks])

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)
# 清空原有 collection（如果存在）
if client.collection_exists(collection_name=COLLECTION_NAME):
    client.delete_collection(collection_name=COLLECTION_NAME)

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=embeddings.shape[1], distance=Distance.COSINE)
)

BATCH_SIZE = 20
for i in range(0, len(chunks), BATCH_SIZE):
    batch_points = [
        PointStruct(id=i+j, vector=embeddings[i+j], payload=chunks[i+j])
        for j in range(min(BATCH_SIZE, len(chunks)-i))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=batch_points)
    print(f"已写入 {i+len(batch_points)} / {len(chunks)}")
print("全部导入完成！")