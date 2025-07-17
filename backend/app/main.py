from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router
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

