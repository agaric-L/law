print("脚本已启动")


from langchain_community.document_loaders import Docx2txtLoader
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
load_dotenv()

# Qdrant Cloud配置
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "law_code"

# 需要导入的docx文件列表（可自行添加路径）
files = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../民法典.docx")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../民法判例百选.docx"))
]

# 1. 解析docx并分条
chunks = []
for file in files:
    print(f"正在处理文件: {file}")
    loader = Docx2txtLoader(file)
    docs = loader.load()
    for doc in docs:
        for line in doc.page_content.split('\n'):
            line = line.strip()
            if line:
                chunks.append(line)

print(f"共提取{len(chunks)}条文本，开始向量化...")

# 2. 文本向量化
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode(chunks)

# 3. 写入Qdrant Cloud
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)
# 检查并创建collection
if not client.collection_exists(collection_name=COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=embeddings.shape[1], distance=Distance.COSINE)
    )

# 分批写入
BATCH_SIZE = 20
for i in range(0, len(chunks), BATCH_SIZE):
    batch_points = [
        PointStruct(id=i+j, vector=embeddings[i+j], payload={"text": chunks[i+j]})
        for j in range(min(BATCH_SIZE, len(chunks)-i))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=batch_points)
    print(f"已写入 {i+len(batch_points)} / {len(chunks)}")
print("全部导入完成！")
print("全部导入完成！")