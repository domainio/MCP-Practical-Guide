from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any
import secrets
import time
import json
import os

app = FastAPI(title="Mock OAuth Server")

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
users_file_path = os.path.join(script_dir, "users.json")
users = json.load(open(users_file_path))

# In-memory tokens storage for demo
tokens: Dict[str, Dict[str, Any]] = {}

# In-memory client registration storage for demo
registered_clients: Dict[str, Dict[str, Any]] = {}

# In-memory authenticated sessions storage for demo
authenticated_sessions: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str
    grant_type: str = "password"

class ClientRegistrationRequest(BaseModel):
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str] = ["authorization_code", "refresh_token"]
    response_types: list[str] = ["code"]
    scope: str = "mcp:read mcp:write"
    token_endpoint_auth_method: str = "client_secret_post"

@app.get("/.well-known/oauth-authorization-server")
async def oauth_server_metadata():
    return {
        "issuer": "http://localhost:3000",
        "authorization_endpoint": "http://localhost:3000/auth/authorize",
        "token_endpoint": "http://localhost:3000/auth/token",
        "registration_endpoint": "http://localhost:3000/register",
        "token_introspection_endpoint": "http://localhost:3000/token/introspect",
        "revocation_endpoint": "http://localhost:3000/token/revoke",
        "scopes_supported": ["mcp:read", "mcp:write", "admin"],
        "grant_types_supported": ["password", "authorization_code", "refresh_token"],
        "response_types_supported": ["token", "code"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "none"]
    }

@app.post("/register")
async def register_client(registration_request: ClientRegistrationRequest):
    """
    OAuth 2.0 Dynamic Client Registration endpoint (RFC 7591)
    """
    # Generate unique client credentials
    client_id = f"client_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    # Store client registration
    client_info = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": registration_request.client_name,
        "redirect_uris": registration_request.redirect_uris,
        "grant_types": registration_request.grant_types,
        "response_types": registration_request.response_types,
        "scope": registration_request.scope,
        "token_endpoint_auth_method": registration_request.token_endpoint_auth_method,
        "client_id_issued_at": int(time.time()),
        # For demo purposes, set secret to never expire
        "client_secret_expires_at": 0  # 0 means never expires
    }
    
    registered_clients[client_id] = client_info
    
    print(f"✅ Registered new client: {client_id} ({registration_request.client_name})")
    
    # Return client information per RFC 7591
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": registration_request.client_name,
        "redirect_uris": registration_request.redirect_uris,
        "grant_types": registration_request.grant_types,
        "response_types": registration_request.response_types,
        "scope": registration_request.scope,
        "token_endpoint_auth_method": registration_request.token_endpoint_auth_method,
        "client_id_issued_at": client_info["client_id_issued_at"],
        "client_secret_expires_at": client_info["client_secret_expires_at"]
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
    
    # 🔒 SECURITY FIX: Create authenticated session for the user
    session_id = secrets.token_urlsafe(16)
    authenticated_sessions[session_id] = {
        "username": username,
        "authenticated_at": time.time(),
        "expires_at": time.time() + 600  # 10 minute session
    }
    print(f"🔐 Created authenticated session for user '{username}': {session_id}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": user["scope"],
        "session_id": session_id  # Return session ID for authorization step
    }

@app.get("/auth/authorize")
async def authorization_endpoint(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = None,
    state: str = None,
    username: str = None,  # Added to receive authenticated username
    session_id: str = None  # Added to validate session
):
    """OAuth2 authorization endpoint - NOW WITH PROPER AUTHENTICATION VALIDATION"""
    print(f"🔐 Authorization request: client_id={client_id}, username={username}")
    
    # Validate client_id exists (either registered or in users)
    client_exists = (
        client_id in registered_clients or
        any(user["client_id"] == client_id for user in users.values())
    )
    
    if not client_exists:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")
    
    # 🔒 SECURITY FIX: Validate user authentication before issuing authorization code
    if not username:
        raise HTTPException(status_code=401, detail="User authentication required")
    
    # Check if user exists and has valid authenticated session
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Find valid session for this user (in real apps, use proper session management)
    valid_session = None
    current_time = time.time()
    
    for sid, session in authenticated_sessions.items():
        if (session["username"] == username and 
            session["expires_at"] > current_time):
            valid_session = session
            break
    
    if not valid_session:
        raise HTTPException(
            status_code=401, 
            detail="No valid authenticated session found. Please login first."
        )
    
    print(f"✅ User '{username}' has valid authenticated session")
    
    # Generate authorization code only for authenticated users
    auth_code = f"auth_code_{secrets.token_urlsafe(16)}"
    
    # Store auth code with user context
    auth_code_info = {
        "client_id": client_id,
        "username": username,  # Link auth code to authenticated user
        "redirect_uri": redirect_uri,
        "scope": scope or "mcp:read mcp:write",
        "created_at": time.time(),
        "used": False
    }
    
    # Simple storage - in production you'd use a proper cache
    if not hasattr(authorization_endpoint, "auth_codes"):
        authorization_endpoint.auth_codes = {}
    authorization_endpoint.auth_codes[auth_code] = auth_code_info
    
    # Return authorization code (in real OAuth, this would redirect)
    callback_url = f"{redirect_uri}?code={auth_code}"
    if state:
        callback_url += f"&state={state}"
    
    return {
        "authorization_code": auth_code,
        "callback_url": callback_url,
        "message": f"Authorization granted for authenticated user '{username}'"
    }

@app.post("/auth/token")
async def token_endpoint(request: Request):
    """OAuth2 token endpoint with proper authorization code validation"""
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        data = await request.json()
    else:
        form_data = await request.form()
        data = dict(form_data)
    
    grant_type = data.get("grant_type")
    print(f"🔐 Token request: grant_type={grant_type}")
    
    if grant_type == "password":
        # Direct password authentication (legacy flow)
        username = data.get("username")
        password = data.get("password")
        client_id = data.get("client_id")
        
        if not all([username, password, client_id]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        user = users.get(username)
        if not user or user["password"] != password or user["client_id"] != client_id:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = secrets.token_urlsafe(32)
        tokens[access_token] = {
            "username": username,
            "client_id": client_id,
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
    
    elif grant_type == "authorization_code":
        # 🔒 SECURITY FIX: Properly validate authorization codes
        code = data.get("code")
        client_id = data.get("client_id")
        redirect_uri = data.get("redirect_uri")
        
        if not all([code, client_id]):
            raise HTTPException(status_code=400, detail="Missing code or client_id")
        
        # Get stored auth code info
        if not hasattr(authorization_endpoint, "auth_codes"):
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        auth_code_info = authorization_endpoint.auth_codes.get(code)
        if not auth_code_info:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        # Validate auth code hasn't been used and belongs to correct client
        if auth_code_info["used"]:
            raise HTTPException(status_code=400, detail="Authorization code already used")
        
        if auth_code_info["client_id"] != client_id:
            raise HTTPException(status_code=400, detail="Client ID mismatch")
        
        if redirect_uri and auth_code_info["redirect_uri"] != redirect_uri:
            raise HTTPException(status_code=400, detail="Redirect URI mismatch")
        
        # Check if auth code is expired (10 minutes)
        if time.time() - auth_code_info["created_at"] > 600:
            raise HTTPException(status_code=400, detail="Authorization code expired")
        
        # Mark auth code as used
        auth_code_info["used"] = True
        
        # Get the authenticated user from the auth code
        username = auth_code_info["username"]
        user = users.get(username)
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid user in authorization code")
        
        print(f"✅ Valid authorization code for user '{username}'")
        
        # Generate access token for the authenticated user
        access_token = secrets.token_urlsafe(32)
        tokens[access_token] = {
            "username": username,
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
    
    elif grant_type == "client_credentials":
        # Client credentials flow (for registered clients)
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        
        if not all([client_id, client_secret]):
            raise HTTPException(status_code=400, detail="Missing client_id or client_secret")
        
        # Check registered clients
        client_info = registered_clients.get(client_id)
        if not client_info or client_info["client_secret"] != client_secret:
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        
        access_token = secrets.token_urlsafe(32)
        tokens[access_token] = {
            "client_id": client_id,
            "scope": client_info["scope"],
            "issued_at": time.time(),
            "expires_in": 3600,
            "active": True
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": client_info["scope"]
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

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
    
    response = {
        "active": True,
        "client_id": token_info["client_id"],
        "scope": token_info["scope"],
        "exp": int(token_info["issued_at"] + token_info["expires_in"])
    }
    
    # Add username only if it exists (for password flow tokens)
    if "username" in token_info:
        response["username"] = token_info["username"]
    
    return response

@app.post("/token/revoke")
async def revoke_token(token: str = Form(...)):
    """Token revocation endpoint"""
    if token in tokens:
        tokens.pop(token)
    return JSONResponse(status_code=200, content={})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000) 