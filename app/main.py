from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import API_V1_STR, PROJECT_NAME
from app.api.v1 import router as api_v1_router
from app.db.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title=PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Chatbot API가 정상 작동 중입니다!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
