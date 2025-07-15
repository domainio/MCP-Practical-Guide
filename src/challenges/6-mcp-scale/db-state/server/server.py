#!/usr/bin/env python3
"""
MCP Stateless Scale Demo - Backend Server

This demonstrates a STATELESS MCP server using FastMCP with stateless_http=True
that can scale horizontally with multiple replicas behind a load balancer.

Key Features:
- Stateless server design: No session persistence in the server
- Redis-based state management: All state stored externally in Redis
- Horizontal scaling: Multiple identical replicas can run simultaneously 
- Load balancer ready: Nginx proxies requests to available replicas

Official MCP SDK implementation for production scaling scenarios.
"""

import asyncio
import json
import os
import uuid
from typing import Optional

import redis.asyncio as redis

# Official MCP imports
from mcp.server.fastmcp import FastMCP

# Local imports
from state_helper import StateHelper


# Initialize Redis connection - sync function that returns async client
def initialize_redis_sync():
    """Initialize Redis connection synchronously"""
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )
    print(f"✅ Redis client configured")
    return redis_client


# Initialize dependencies at module level - STATELESS
redis_client = initialize_redis_sync()
state_helper = StateHelper(redis_client, None)  # No replica ID - truly stateless!

print(f"🚀 Stateless MCP Scale Demo server initialized")

# Create stateless FastMCP server for horizontal scaling
mcp = FastMCP("mcp-stateless-scale-demo", stateless_http=True)


@mcp.tool()
async def create_task(name: str, session_id: str) -> str:
    """Create a new task"""
    result = await state_helper.create_task(name, session_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def assign_task(task_id: str, worker_id: str, session_id: str) -> str:
    """Assign a task to a worker"""
    result = await state_helper.assign_task(task_id, worker_id, session_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def complete_task(task_id: str, session_id: str) -> str:
    """Mark a task as completed"""
    result = await state_helper.complete_task(task_id, session_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_session_stats(session_id: str) -> str:
    """Get statistics for a session"""
    result = await state_helper.get_session_stats(session_id)
    return json.dumps(result, indent=2)


def main():
    print(f"🚀 Stateless MCP Scale Demo server starting")
    print(f"📊 Using Redis for state management at {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
    print(f"🔄 This server is STATELESS - any replica can handle any request")
    
    # Use uvicorn directly to bind to 0.0.0.0 for nginx access
    import uvicorn
    app = mcp.streamable_http_app
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 