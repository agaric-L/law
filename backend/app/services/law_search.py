import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
#from sentence_transformers import SentenceTransformer

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "law_code"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
#model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def search_law(query, top_k=5):
   # query_vec = model.encode([query])[0]
   # hits = client.search(
        #collection_name=COLLECTION_NAME,
        #query_vector=query_vec,
        #limit=top_k
    #)
    #return [hit.payload['text'] for hit in hits]
    return []



#说明：因为sentence_transformers库在云端部署时无法使用，所以暂时注释掉，返回空列表