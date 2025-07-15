#!/usr/bin/env python3
"""
State Helper for MCP Scale Demo

Handles all Redis state management and business logic.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from pydantic import BaseModel


class TaskData(BaseModel):
    """Task data model - STATELESS"""
    id: str
    name: str
    status: str = "pending"  # pending, assigned, in_progress, completed
    worker_id: Optional[str] = None
    created_at: str
    assigned_at: Optional[str] = None
    completed_at: Optional[str] = None


class SessionState(BaseModel):
    """Session state stored in Redis - STATELESS"""
    session_id: str
    active_tasks: List[str] = []
    worker_assignments: Dict[str, List[str]] = {}  # worker_id -> [task_ids]


class StateHelper:
    """Helper class for Redis state management - STATELESS"""
    
    def __init__(self, redis_client: redis.Redis, replica_id: Optional[str] = None):
        self.redis_client = redis_client
        # Ignore replica_id - we are STATELESS!
    
    async def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get session state from Redis"""
        session_key = f"session:{session_id}"
        session_data = await self.redis_client.get(session_key)
        
        if session_data:
            return SessionState(**json.loads(session_data))
        return None
    
    async def save_session_state(self, session: SessionState):
        """Save session state to Redis"""
        session_key = f"session:{session.session_id}"
        await self.redis_client.set(session_key, json.dumps(session.dict()))
    
    async def get_all_tasks(self) -> List[TaskData]:
        """Get all tasks from Redis"""
        task_keys = await self.redis_client.keys("task:*")
        tasks = []
        
        for key in task_keys:
            task_data = await self.redis_client.get(key)
            if task_data:
                tasks.append(TaskData(**json.loads(task_data)))
        
        return tasks
    
    async def save_task(self, task: TaskData):
        """Save task to Redis"""
        task_key = f"task:{task.id}"
        await self.redis_client.set(task_key, json.dumps(task.dict()))
    
    async def get_global_status(self) -> Dict[str, Any]:
        """Get global system status - STATELESS"""
        tasks = await self.get_all_tasks()
        
        return {
            "total_tasks": len(tasks),
            "status_breakdown": {
                "pending": len([t for t in tasks if t.status == "pending"]),
                "assigned": len([t for t in tasks if t.status == "assigned"]),
                "in_progress": len([t for t in tasks if t.status == "in_progress"]),
                "completed": len([t for t in tasks if t.status == "completed"])
            }
        }
    
    async def create_task(self, task_name: str, session_id: str) -> Dict[str, Any]:
        """Create a new task"""
        # Create task
        task = TaskData(
            id=str(uuid.uuid4()),
            name=task_name,
            status="pending",
            created_at=asyncio.get_event_loop().time().__str__()
        )
        
        # Save task to Redis
        await self.save_task(task)
        
        # Update session state
        session = await self.get_session_state(session_id)
        if not session:
            session = SessionState(
                session_id=session_id
            )
        
        session.active_tasks.append(task.id)
        await self.save_session_state(session)
        
        return {
            "status": "created",
            "task_id": task.id,
            "task_name": task_name,
            "session_id": session_id
        }
    
    async def assign_task(self, task_id: str, worker_id: str, session_id: str) -> Dict[str, Any]:
        """Assign task to worker"""
        # Get and update task
        task_key = f"task:{task_id}"
        task_data = await self.redis_client.get(task_key)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        task = TaskData(**json.loads(task_data))
        task.status = "assigned"
        task.worker_id = worker_id
        task.assigned_at = asyncio.get_event_loop().time().__str__()
        
        await self.save_task(task)
        
        # Update session state
        session = await self.get_session_state(session_id)
        if session:
            if task_id in session.active_tasks:
                session.active_tasks.remove(task_id)
            
            if worker_id not in session.worker_assignments:
                session.worker_assignments[worker_id] = []
            session.worker_assignments[worker_id].append(task_id)
            
            await self.save_session_state(session)
        
        return {
            "status": "assigned",
            "task_id": task_id,
            "worker_id": worker_id,
            "session_id": session_id
        }
    
    async def complete_task(self, task_id: str, session_id: str) -> Dict[str, Any]:
        """Complete a task"""
        # Get and update task
        task_key = f"task:{task_id}"
        task_data = await self.redis_client.get(task_key)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        task = TaskData(**json.loads(task_data))
        task.status = "completed"
        task.completed_at = asyncio.get_event_loop().time().__str__()
        
        await self.save_task(task)
        
        # Update session state
        session = await self.get_session_state(session_id)
        if session:
            # Remove from worker assignments
            for worker_id, task_ids in session.worker_assignments.items():
                if task_id in task_ids:
                    task_ids.remove(task_id)
            
            await self.save_session_state(session)
        
        return {
            "status": "completed",
            "task_id": task_id,
            "session_id": session_id
        }
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        session = await self.get_session_state(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}
        
        # Get detailed task info
        all_tasks = await self.get_all_tasks()
        session_tasks = [t for t in all_tasks if t.id in session.active_tasks or 
                       any(t.id in tasks for tasks in session.worker_assignments.values())]
        
        return {
            "session_id": session_id,
            "active_tasks": len(session.active_tasks),
            "worker_assignments": {
                worker: len(tasks) for worker, tasks in session.worker_assignments.items()
            },
            "task_details": [task.dict() for task in session_tasks],
            "total_session_tasks": len(session_tasks)
        } 