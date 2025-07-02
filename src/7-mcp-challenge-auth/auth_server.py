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

app = FastAPI(title="MCP OAuth Server with PKCE")

# Configuration
BASE_URL = "http://localhost:3000"

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
users_file_path = os.path.join(script_dir, "users.json")
users = json.load(open(users_file_path))

# In-memory storage for demo (in production, use secure database)
tokens: Dict[str, Dict[str, Any]] = {}
auth_codes: Dict[str, Dict[str, Any]] = {}

class ClientRegistrationRequest(BaseModel):
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str] = ["authorization_code", "refresh_token"]
    response_types: list[str] = ["code"]
    scope: str = "mcp:read mcp:write"
    token_endpoint_auth_method: str = "none"  # PKCE instead of client secret

@app.get("/.well-known/oauth-authorization-server")
async def oauth_server_metadata():
    return {
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/auth/authorize",
        "token_endpoint": f"{BASE_URL}/auth/token",
        "registration_endpoint": f"{BASE_URL}/register",
        "scopes_supported": ["mcp:read", "mcp:write"],
        "grant_types_supported": ["authorization_code"],
        "response_types_supported": ["code"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"]
    }

def validate_credentials(username: str, password: str) -> dict:
    """Validate user credentials"""
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return user

def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Verify PKCE code challenge matches code verifier"""
    expected_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return expected_challenge == code_challenge

@app.get("/auth/authorize")
async def authorization_endpoint(
    response_type: str, 
    client_id: str, 
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
    scope: str = "mcp:read mcp:write",
    state: str = None,
    username: str = None,  # For demo simplicity
    password: str = None   # For demo simplicity
):
    """PKCE OAuth2 authorization endpoint"""
    print(f"🔐 PKCE Authorization request: client_id={client_id}, challenge={code_challenge[:10]}...")
    
    # Validate request
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")
    if code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="Unsupported code_challenge_method")
    if not code_challenge:
        raise HTTPException(status_code=400, detail="Missing code_challenge")
    
    # Validate user credentials (in production, this would be a proper login page)
    user = validate_credentials(username, password)
    print(f"✅ User '{username}' authenticated")
    
    # Generate authorization code
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
        "message": f"PKCE authorization granted for user '{username}'"
    }

@app.post("/auth/token")
async def token_endpoint(request: Request):
    """PKCE OAuth2 token endpoint"""
    data = await request.json() if "application/json" in request.headers.get("content-type", "") else dict(await request.form())
    grant_type = data.get("grant_type")
    
    print(f"🔐 Token request: grant_type={grant_type}")
    print(f"🔍 Token request data: {dict(data)}")  # Debug what we're receiving
    
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")
    
    # Extract parameters
    code = data.get("code")
    client_id = data.get("client_id")
    code_verifier = data.get("code_verifier")
    redirect_uri = data.get("redirect_uri")
    
    print(f"🔍 Extracted params - code: {code}, client_id: {client_id}, code_verifier: {code_verifier}, redirect_uri: {redirect_uri}")
    
    if not all([code, client_id, code_verifier]):
        missing = [k for k, v in {"code": code, "client_id": client_id, "code_verifier": code_verifier}.items() if not v]
        raise HTTPException(status_code=400, detail=f"Missing required parameters: {missing}")
    
    # Validate authorization code
    auth_code_info = auth_codes.get(code)
    if not auth_code_info:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    if auth_code_info["used"]:
        raise HTTPException(status_code=400, detail="Authorization code already used")
    
    if auth_code_info["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Client ID mismatch")
    
    if redirect_uri and auth_code_info["redirect_uri"] != redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI mismatch")
    
    if time.time() - auth_code_info["created_at"] > 600:
        raise HTTPException(status_code=400, detail="Authorization code expired")
    
    # Verify PKCE
    print(f"🔍 PKCE verification - received verifier: {code_verifier}")
    print(f"🔍 PKCE verification - stored challenge: {auth_code_info['code_challenge']}")
    
    if not verify_pkce(code_verifier, auth_code_info["code_challenge"]):
        raise HTTPException(status_code=400, detail="Invalid code_verifier")
    
    print(f"✅ PKCE verification successful for user '{auth_code_info['username']}'")
    
    # Mark code as used
    auth_code_info["used"] = True
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    tokens[access_token] = {
        "username": auth_code_info["username"],
        "client_id": client_id,
        "scope": auth_code_info["scope"],
        "issued_at": time.time(),
        "expires_in": 3600,
        "active": True
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": auth_code_info["scope"]
    }

@app.post("/token/introspect")
async def introspect_token(token: str = Form(...)):
    """Token introspection endpoint"""
    token_info = tokens.get(token)
    
    if not token_info or time.time() > token_info["issued_at"] + token_info["expires_in"]:
        tokens.pop(token, None)
        return {"active": False}
    
    return {
        "active": True,
        "client_id": token_info["client_id"],
        "username": token_info["username"],
        "scope": token_info["scope"],
        "exp": int(token_info["issued_at"] + token_info["expires_in"])
    }

@app.post("/register")
async def register_client(req: ClientRegistrationRequest):
    """Dynamic Client Registration for MCP"""
    client_id = f"mcp_client_{secrets.token_urlsafe(8)}"
    
    # For PKCE, we don't need client secrets
    client_info = {
        "client_id": client_id,
        "client_id_issued_at": int(time.time()),
        "client_name": req.client_name,
        "redirect_uris": req.redirect_uris,
        "grant_types": req.grant_types,
        "response_types": req.response_types,
        "scope": req.scope,
        "token_endpoint_auth_method": req.token_endpoint_auth_method
    }
    
    print(f"✅ Registered MCP client: {client_id}")
    return client_info

if __name__ == "__main__":
    print("🚀 Starting MCP OAuth Server with PKCE on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000) 