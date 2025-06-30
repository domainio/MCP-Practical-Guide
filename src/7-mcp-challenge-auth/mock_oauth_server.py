from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any
import secrets
import time
import json

app = FastAPI(title="Mock OAuth Server")

users = json.load(open("users.json"))

# In-memory tokens storage for demo
tokens: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str
    grant_type: str = "password"

@app.get("/.well-known/oauth-authorization-server")
async def oauth_server_metadata():
    return {
        "issuer": "http://localhost:3000",
        "authorization_endpoint": "http://localhost:3000/auth/login",
        "token_endpoint": "http://localhost:3000/auth/token",
        "token_introspection_endpoint": "http://localhost:3000/token/introspect",
        "revocation_endpoint": "http://localhost:3000/token/revoke",
        "scopes_supported": ["mcp:read", "mcp:write", "admin"],
        "grant_types_supported": ["password"],
        "response_types_supported": ["token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "none"]
    }

@app.post("/auth/login")
async def login_json(credentials: dict):
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    
    # Store token info
    tokens[access_token] = {
        "username": username,
        "client_id": user["client_id"],
        "scope": user["scope"],
        "issued_at": time.time(),
        "expires_in": 3600,
        "active": True
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": user["scope"]
    }

@app.post("/auth/token")
async def token_endpoint(
    grant_type: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(None),
    scope: str = Form(None)
):
    """OAuth2 form-based token endpoint"""
    if grant_type != "password":
        raise HTTPException(status_code=400, detail="Unsupported grant type")
    
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    
    # Store token info
    tokens[access_token] = {
        "username": username,
        "client_id": client_id or user["client_id"],
        "scope": scope or user["scope"],
        "issued_at": time.time(),
        "expires_in": 3600,
        "active": True
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": scope or user["scope"]
    }

@app.post("/token/introspect")
async def introspect_token(token: str = Form(...)):
    """Token introspection endpoint for resource servers"""
    token_info = tokens.get(token)
    
    if not token_info:
        return {"active": False}
    
    # Check if token expired
    if time.time() > token_info["issued_at"] + token_info["expires_in"]:
        tokens.pop(token, None)
        return {"active": False}
    
    return {
        "active": True,
        "client_id": token_info["client_id"],
        "username": token_info["username"],
        "scope": token_info["scope"],
        "exp": int(token_info["issued_at"] + token_info["expires_in"])
    }

@app.post("/token/revoke")
async def revoke_token(token: str = Form(...)):
    """Token revocation endpoint"""
    if token in tokens:
        tokens.pop(token)
    return JSONResponse(status_code=200, content={})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000) 