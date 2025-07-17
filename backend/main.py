from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import router

#git add .
#git commit -m "XXXXX"
#git remote set-url origin https://github.com/agaric-L/law.git
#git push -u origin master

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)
app.include_router(router)

#云部署添加
import os
from fastapi.staticfiles import StaticFiles
from qdrant_client import QdrantClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
# Qdrant 客户端
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
