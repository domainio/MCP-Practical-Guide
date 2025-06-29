from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import redis
import json
import os
import uuid
from fastmcp import FastMCP, Context, Resource, Tool
from mcp.types import TaskStatus

# Initialize FastAPI and MCP
app = FastAPI(title="MCP Scale Demo")
mcp = FastMCP("MCP Scale Demo")

# Redis connection for session state
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

class SessionState(BaseModel):
    """Session state stored in Redis"""
    session_id: str
    replica_id: str  # Which replica created/owns this session
    active_tasks: List[str]  # List of active task IDs
    worker_sessions: Dict[str, List[str]]  # Worker ID -> List of task IDs

def get_or_create_session(request: Request) -> SessionState:
    """
    Get existing session or create new one.
    Uses request headers to identify session and replica.
    """
    # Get session ID from header or create new one
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    replica_id = os.getenv("HOSTNAME", "unknown")  # Docker container hostname
    
    # Try to get existing session
    session_key = f"session:{session_id}"
    session_data = redis_client.get(session_key)
    
    if session_data:
        session = SessionState(**json.loads(session_data))
        # Update replica_id if session was created by a different replica
        if session.replica_id != replica_id:
            session.replica_id = replica_id
            redis_client.set(session_key, session.json())
    else:
        # Create new session
        session = SessionState(
            session_id=session_id,
            replica_id=replica_id,
            active_tasks=[],
            worker_sessions={}
        )
        redis_client.set(session_key, session.json())
    
    return session

# MCP Resources
@mcp.resource
async def get_task_resource(task_id: str) -> Resource:
    """Get task data from MCP."""
    try:
        task = await mcp.get_task(task_id)
        return Resource(content=json.dumps(task.dict()), content_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@mcp.resource
async def list_tasks_resource() -> Resource:
    """Get all tasks from MCP."""
    try:
        tasks = await mcp.list_tasks()
        return Resource(content=json.dumps([task.dict() for task in tasks]), content_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MCP Tools
@mcp.tool
async def create_task(name: str, ctx: Context, request: Request) -> str:
    """Create a new task with MCP orchestration."""
    # Get or create session
    session = get_or_create_session(request)
    
    # Create MCP task
    mcp_task = await ctx.create_task(
        name=name,
        payload={"task_name": name}
    )
    
    # Update session state
    session.active_tasks.append(mcp_task.id)
    redis_client.set(f"session:{session.session_id}", session.json())
    
    await ctx.info(f"Created task {mcp_task.id} in session {session.session_id} on replica {session.replica_id}")
    return mcp_task.id

@mcp.tool
async def assign_task(task_id: str, worker_id: str, ctx: Context, request: Request) -> Dict:
    """Assign a task to a worker with MCP orchestration."""
    try:
        # Get session
        session = get_or_create_session(request)
        
        # Update MCP task
        await ctx.update_task(
            task_id=task_id,
            status=TaskStatus.IN_PROGRESS,
            worker_id=worker_id
        )
        
        # Update session state
        if task_id in session.active_tasks:
            session.active_tasks.remove(task_id)
            if worker_id not in session.worker_sessions:
                session.worker_sessions[worker_id] = []
            session.worker_sessions[worker_id].append(task_id)
            redis_client.set(f"session:{session.session_id}", session.json())
        
        await ctx.info(f"Assigned task {task_id} to worker {worker_id} in session {session.session_id} on replica {session.replica_id}")
        return {
            "status": "assigned",
            "task_id": task_id,
            "worker_id": worker_id,
            "session_id": session.session_id,
            "replica_id": session.replica_id
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@mcp.tool
async def complete_task(task_id: str, ctx: Context, request: Request) -> Dict:
    """Complete a task with MCP orchestration."""
    try:
        # Get session
        session = get_or_create_session(request)
        
        # Update MCP task
        await ctx.update_task(
            task_id=task_id,
            status=TaskStatus.COMPLETED
        )
        
        # Update session state
        # Remove from worker sessions
        for worker_id, tasks in session.worker_sessions.items():
            if task_id in tasks:
                tasks.remove(task_id)
        # Remove from active tasks
        if task_id in session.active_tasks:
            session.active_tasks.remove(task_id)
        redis_client.set(f"session:{session.session_id}", session.json())
        
        await ctx.info(f"Completed task {task_id} in session {session.session_id} on replica {session.replica_id}")
        return {
            "status": "completed",
            "task_id": task_id,
            "session_id": session.session_id,
            "replica_id": session.replica_id
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# FastAPI endpoints that use MCP
@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "MCP Scale Demo"}

@app.post("/tasks")
async def create_task_endpoint(name: str, request: Request) -> Dict:
    task_id = await create_task(name, mcp.get_context(), request)
    return {"task_id": task_id}

@app.get("/tasks")
async def list_tasks() -> List[Dict]:
    resource = await list_tasks_resource()
    return json.loads(resource.content)

@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> Dict:
    resource = await get_task_resource(task_id)
    return json.loads(resource.content)

@app.put("/tasks/{task_id}/assign/{worker_id}")
async def assign_task_endpoint(task_id: str, worker_id: str, request: Request) -> Dict:
    return await assign_task(task_id, worker_id, mcp.get_context(), request)

@app.put("/tasks/{task_id}/complete")
async def complete_task_endpoint(task_id: str, request: Request) -> Dict:
    return await complete_task(task_id, mcp.get_context(), request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 