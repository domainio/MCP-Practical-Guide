from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import json
import os
import uuid

app = FastAPI(title="MCP Scale Demo Client")

# Backend URLs
BACKEND_URLS = [
    "http://mcp:8000",  # Docker service name
    "http://mcp:8001",
    "http://mcp:8002"
]

class Task(BaseModel):
    id: str
    name: str
    status: str
    worker_id: Optional[str] = None

async def get_backend_url() -> str:
    """Get a backend URL (simple round-robin)."""
    # In a real application, you might want to implement proper load balancing
    return BACKEND_URLS[0]

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "MCP Scale Demo Client"}

@app.post("/tasks")
async def create_task(name: str, request: Request) -> Dict:
    """Create a new task."""
    backend_url = await get_backend_url()
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{backend_url}/tasks",
            params={"name": name},
            headers={"X-Session-ID": session_id}
        )
        response.raise_for_status()
        return response.json()

@app.get("/tasks")
async def list_tasks() -> List[Dict]:
    """List all tasks."""
    backend_url = await get_backend_url()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{backend_url}/tasks")
        response.raise_for_status()
        return response.json()

@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> Dict:
    """Get a specific task."""
    backend_url = await get_backend_url()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{backend_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()

@app.put("/tasks/{task_id}/assign/{worker_id}")
async def assign_task(task_id: str, worker_id: str, request: Request) -> Dict:
    """Assign a task to a worker."""
    backend_url = await get_backend_url()
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{backend_url}/tasks/{task_id}/assign/{worker_id}",
            headers={"X-Session-ID": session_id}
        )
        response.raise_for_status()
        return response.json()

@app.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, request: Request) -> Dict:
    """Complete a task."""
    backend_url = await get_backend_url()
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{backend_url}/tasks/{task_id}/complete",
            headers={"X-Session-ID": session_id}
        )
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 