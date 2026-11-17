from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.evaluation import router as evaluation_router

app = FastAPI(
    title="Assessiva API",
    description="Multilingual AI Essay Evaluation Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Assessiva API is running",
        "status": "online",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(
    evaluation_router,
    prefix="/api",
    tags=["Essay Evaluation"],
)