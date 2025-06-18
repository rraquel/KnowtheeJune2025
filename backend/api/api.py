from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from backend.services import talent_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify your frontend's URL for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(talent_router, prefix="/api/talent")

# Optionally, add a root endpoint for health check
def root():
    return {"status": "ok"}

app.get("/")(root) 