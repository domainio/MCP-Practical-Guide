from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any
import secrets
import time
import json
import os
import hashlib
import base64

app = FastAPI(title="Simple MCP OAuth Server")

# Simple settings
users = json.load(open(os.path.join(os.path.dirname(__file__), "users.json")))

# Store everything in memory (simple!)
tokens: Dict[str, Dict[str, Any]] = {}
auth_codes: Dict[str, Dict[str, Any]] = {}

class ClientRegistrationRequest(BaseModel):
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str] = ["authorization_code", "refresh_token"]
    response_types: list[str] = ["code"]
    scope: str = "mcp:read mcp:write"
    token_endpoint_auth_method: str = "none"

@app.get("/.well-known/oauth-authorization-server")
async def oauth_server_info():
    """Tell clients what this server can do"""
    return {
        "issuer": "http://localhost:3000",
        "authorization_endpoint": "http://localhost:3000/auth/authorize",
        "token_endpoint": "http://localhost:3000/auth/token",
        "registration_endpoint": "http://localhost:3000/register",
        "scopes_supported": ["mcp:read", "mcp:write"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "response_types_supported": ["code"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"]
    }

@app.get("/auth/authorize")
async def login_and_get_code(
    response_type: str, 
    client_id: str, 
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
    scope: str = "mcp:read mcp:write",
    state: str = None,
    username: str = None,
    password: str = None
):
    """Step 1: User logs in and gets authorization code"""
    
    # Check if request is valid
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Only 'code' response type supported")
    if code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="Only 'S256' challenge method supported")
    if not code_challenge:
        raise HTTPException(status_code=400, detail="Missing code_challenge")
    
    # Check username and password
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    
    # Create authorization code
    auth_code = f"auth_code_{secrets.token_urlsafe(16)}"
    auth_codes[auth_code] = {
        "client_id": client_id,
        "username": username,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": time.time(),
        "used": False
    }
    
    # Build callback URL
    callback_url = f"{redirect_uri}?code={auth_code}"
    if state:
        callback_url += f"&state={state}"
    
    return {
        "authorization_code": auth_code,
        "callback_url": callback_url,
        "message": f"Login successful for user '{username}'"
    }

@app.post("/auth/token")
async def get_tokens(request: Request):
    """Step 2: Exchange code for tokens OR refresh tokens"""
    
    # Get form data
    if "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)
    
    grant_type = data.get("grant_type")
    
    if grant_type == "authorization_code":
        # Exchange authorization code for tokens
        return await exchange_code_for_tokens(data)
    elif grant_type == "refresh_token":
        # Use refresh token to get new access token
        return await refresh_tokens(data)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown grant_type: {grant_type}")

async def exchange_code_for_tokens(data: dict):
    """Exchange authorization code for access + refresh tokens"""
    
    # Check required fields
    code = data.get("code")
    client_id = data.get("client_id")
    code_verifier = data.get("code_verifier")
    
    if not code or not client_id or not code_verifier:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Find the authorization code
    auth_code_info = auth_codes.get(code)
    if not auth_code_info:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Check if code is valid
    if auth_code_info["used"]:
        raise HTTPException(status_code=400, detail="Authorization code already used")
    
    if auth_code_info["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Wrong client_id")
    
    if time.time() - auth_code_info["created_at"] > 600:
        raise HTTPException(status_code=400, detail="Authorization code expired")
    
    # Verify PKCE challenge
    expected_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    if expected_challenge != auth_code_info["code_challenge"]:
        raise HTTPException(status_code=400, detail="Invalid code_verifier")
    
    # Mark code as used
    auth_code_info["used"] = True
    
    # Create tokens
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    
    # Store access token
    tokens[access_token] = {
        "username": auth_code_info["username"],
        "client_id": client_id,
        "scope": auth_code_info["scope"],
        "issued_at": time.time(),
        "expires_in": 30,  # 1 hour
        "active": True,
        "refresh_token": refresh_token
    }
    
    # Store refresh token
    tokens[refresh_token] = {
        "username": auth_code_info["username"],
        "client_id": client_id,
        "scope": auth_code_info["scope"],
        "issued_at": time.time(),
        "expires_in": 30,  # 90 days
        "active": True,
        "token_type": "refresh_token",
        "access_token": access_token
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30,
        "refresh_token": refresh_token,
        "scope": auth_code_info["scope"]
    }

async def refresh_tokens(data: dict):
    """Use refresh token to get new access token"""
    
    # Check required fields
    refresh_token = data.get("refresh_token")
    client_id = data.get("client_id")
    
    if not refresh_token or not client_id:
        raise HTTPException(status_code=400, detail="Missing refresh_token or client_id")
    
    # Find refresh token
    refresh_token_info = tokens.get(refresh_token)
    if not refresh_token_info:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    
    # Check if refresh token is valid
    if not refresh_token_info.get("active"):
        raise HTTPException(status_code=400, detail="Refresh token revoked")
    
    if refresh_token_info.get("token_type") != "refresh_token":
        raise HTTPException(status_code=400, detail="Token is not a refresh token")
    
    if refresh_token_info["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Wrong client_id")
    
    # Check if refresh token expired
    if time.time() > refresh_token_info["issued_at"] + refresh_token_info["expires_in"]:
        # Clean up expired tokens
        tokens.pop(refresh_token, None)
        if refresh_token_info.get("access_token"):
            tokens.pop(refresh_token_info["access_token"], None)
        raise HTTPException(status_code=400, detail="Refresh token expired")
    
    # Revoke old access token
    old_access_token = refresh_token_info.get("access_token")
    if old_access_token and old_access_token in tokens:
        tokens[old_access_token]["active"] = False
    
    # Create new access token
    new_access_token = secrets.token_urlsafe(32)
    tokens[new_access_token] = {
        "username": refresh_token_info["username"],
        "client_id": client_id,
        "scope": refresh_token_info["scope"],
        "issued_at": time.time(),
        "expires_in": 30,  # 1 hour
        "active": True,
        "refresh_token": refresh_token
    }
    
    # Update refresh token to point to new access token
    refresh_token_info["access_token"] = new_access_token
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer", 
        "expires_in": 30,
        "refresh_token": refresh_token,
        "scope": refresh_token_info["scope"]
    }

@app.post("/token/introspect")
async def check_token(token: str = Form(...)):
    """Check if token is valid and get info about it"""
    
    token_info = tokens.get(token)
    
    # If token doesn't exist or is expired, return inactive
    if not token_info or time.time() > token_info["issued_at"] + token_info["expires_in"]:
        if token_info:
            tokens.pop(token, None)  # Clean up expired token
        return {"active": False}
    
    return {
        "active": True,
        "client_id": token_info["client_id"],
        "username": token_info["username"],
        "scope": token_info["scope"],
        "exp": int(token_info["issued_at"] + token_info["expires_in"])
    }

@app.post("/register")
async def register_new_client(req: ClientRegistrationRequest):
    """Register a new OAuth client"""
    
    client_id = f"mcp_client_{secrets.token_urlsafe(8)}"
    
    return {
        "client_id": client_id,
        "client_id_issued_at": int(time.time()),
        "client_name": req.client_name,
        "redirect_uris": req.redirect_uris,
        "grant_types": req.grant_types,
        "response_types": req.response_types,
        "scope": req.scope,
        "token_endpoint_auth_method": req.token_endpoint_auth_method
    }

if __name__ == "__main__":
    print("🚀 Starting Simple MCP OAuth Server on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000) 