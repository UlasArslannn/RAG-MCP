"""
FastAPI server for MCP Chat API
Imports agent utilities from agent_utils.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
from typing import Any

from llama_index.core.workflow import Context

# Import shared utilities
from agent_utils import get_agent, handle_user_message


# -------------------- Pydantic Models --------------------
class ChatRequest(BaseModel):
    message: str
    verbose: bool = False


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] = []
    


# -------------------- Global State --------------------
agent = None
agent_context = None


# -------------------- Lifespan (Startup/Shutdown) --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, agent_context
    
    # Startup
    print("🚀 Starting FastAPI server...")
    agent, tools = await get_agent()
    agent_context = Context(agent)
    
    print(f"✅ Agent initialized with {len(tools)} tools")
    for tool in tools:
        print(f"   - {tool.metadata.name}: {tool.metadata.description[:50]}...")
    
    yield
    
    # Shutdown
    print(" Shutting down...")


# -------------------- FastAPI App --------------------
app = FastAPI(
    title="MCP Chat API",
    description="FastAPI wrapper for LlamaIndex MCP Agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- Endpoints --------------------
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "MCP Chat API is running"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI agent
    
    - **message**: The user's message to the agent
    - **verbose**: If true, includes tool call details in response
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized yet")
    
    try:
        response, tool_calls = await handle_user_message(
            request.message,
            agent,
            agent_context,
            verbose=request.verbose
        )
        
        
        return ChatResponse(
            response=response,
            tool_calls=tool_calls if request.verbose else [],
        
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_context():
    """Reset the agent context (clear conversation history)"""
    global agent_context
    
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized yet")
    
    agent_context = Context(agent)
    return {"status": "ok", "message": "Agent context reset successfully"}


# -------------------- Run Server --------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )
