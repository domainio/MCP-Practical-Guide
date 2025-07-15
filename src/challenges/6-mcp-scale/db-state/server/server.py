import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal
import redis.asyncio as redis
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

class TaskState(BaseModel):
    """Task state model stored in Redis"""
    task_id: str
    request_id: str
    user_id: str
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)  # Progress 0-100%
    result: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def initialize_redis():
    """Initialize Redis client"""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )

redis_client = initialize_redis()

mcp = FastMCP("mcp-db-state", stateless_http=True)


@mcp.tool()
async def create_task(task_name: str, ctx: Context) -> str:
    """Create a new task for the user"""
    user_id = ctx.request_context.request.headers.get("X-User-ID")
    request_id = ctx.request_id
    
    task_state = TaskState(
        task_id=str(uuid.uuid4()),
        request_id=request_id,
        user_id=user_id,
        status="pending"
    )
    
    result = await redis_client.hset(
        f"user:{user_id}:tasks",
        task_name,
        task_state.model_dump_json()
    )
    return f"Task '{task_name}' created for user {user_id}. Redis HSET returned: {result} (1=new, 0=updated)"
    
@mcp.tool()
async def do_task(task_name: str, ctx: Context) -> str:
    """Execute a task with progress simulation"""
    user_id = ctx.request_context.request.headers.get("X-User-ID")
    request_id = ctx.request_id
    task_data = await redis_client.hget(f"user:{user_id}:tasks", task_name)
    task_state = TaskState(**json.loads(task_data))
    
    if task_state.status == "completed":
        return f"Task '{task_name}' is already completed"
    
    task_state.status = "in_progress"
    task_state.updated_at = datetime.now(timezone.utc).isoformat()
    
    await redis_client.hset(
        f"user:{user_id}:tasks",
        task_name,
        task_state.model_dump_json()
    )
    
    max_steps = 3
    for i in range(max_steps):
        task_state.progress = i
        task_state.updated_at = datetime.now(timezone.utc).isoformat()
        await redis_client.hset(
            f"user:{user_id}:tasks",
            task_name,
            task_state.model_dump_json()
        )
        await ctx.info(f"Task '{task_name}' progress step {i} of {max_steps}")    
        await asyncio.sleep(5)
    
    task_state.status = "completed"
    task_state.updated_at = datetime.now(timezone.utc).isoformat()  
    await redis_client.hset(
        f"user:{user_id}:tasks",
        task_name,
        task_state.model_dump_json()
    )
    
    await redis_client.hdel(f"user:{user_id}:tasks", task_name)
    return f"Task '{task_name}' completed and removed from Redis"

@mcp.tool()
async def complete_task(task_name: str, ctx: Context) -> str:
    """Mark a task as completed manually"""
    user_id = ctx.request_context.request.headers.get("X-User-ID")
    request_id = ctx.request_id
    
    # Get task from Redis
    task_data = await redis_client.hget(f"user:{user_id}:tasks", task_name)
    if not task_data:
        return json.dumps({
            "status": "error",
            "message": f"No such task '{task_name}' found for user {user_id}"
        }, indent=2)
    
    task_state = TaskState(**json.loads(task_data))
    
    # Update task to completed
    task_state.status = "completed"
    task_state.progress = 100
    task_state.result = f"Task '{task_name}' manually completed"
    task_state.updated_at = datetime.now(timezone.utc).isoformat()
    
    # Update in Redis
    await redis_client.hset(
        f"user:{user_id}:tasks",
        task_name,
        task_state.model_dump_json()
    )
    await redis_client.set(f"task:{task_state.task_id}", task_state.model_dump_json(), ex=3600)
    
    return json.dumps({
        "status": "success",
        "message": f"Task '{task_name}' marked as completed",
        "task": task_state.model_dump(),
        "user_id": user_id,
        "request_id": request_id
    }, indent=2)
        

@mcp.tool()
async def list_tasks(ctx: Context) -> str:
    """List all tasks for the current user"""
    user_id = ctx.request_context.request.headers.get("X-User-ID")
    tasks = await redis_client.hgetall(f"user:{user_id}:tasks")
    
    task_list = []
    for task_name, task_data in tasks.items():
        task_state = TaskState(**json.loads(task_data))
        task_list.append({
            "name": task_name,
            "task": task_state.model_dump()
        })
    
    return f"Found {len(task_list)} tasks for user {user_id}: {task_list}"
        
        
def main():
    import uvicorn
    app = mcp.streamable_http_app
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 