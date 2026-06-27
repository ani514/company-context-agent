from dotenv import load_dotenv; load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_agent          # reuse your existing agent

app = FastAPI()

# CORS: lets the React app (different port) call this backend.
# Without it, the browser blocks the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # React's dev address
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defines the shape of the incoming request body: {"question": "..."}
class Ask(BaseModel):
    question: str

@app.post("/ask")
def ask(body: Ask):
    # TODO: call run_agent with the question from the request body,
    #       and return it as JSON like {"answer": ...}
    answer = run_agent(body.question)
    return {"answer": answer}
