from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Mock OAuth Server")

# Mock OAuth discovery endpoint
@app.get("/.well-known/oauth-authorization-server")
def oauth_discovery():
    return {
        "issuer": "http://localhost:3000",
        "authorization_endpoint": "http://localhost:3000/auth",
        "token_endpoint": "http://localhost:3000/token",
        "token_introspection_endpoint": "http://localhost:3000/token/introspect",
        "revocation_endpoint": "http://localhost:3000/token/revoke",
        "scopes_supported": ["mcp:read", "mcp:write"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "response_types_supported": ["code"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"]
    }

# Mock token introspection endpoint
@app.post("/token/introspect")
async def token_introspect(request: Request):
    """Mock token introspection endpoint"""
    from fastapi import Request
    
    # Read the request body to check for token
    body = await request.body()
    body_str = body.decode('utf-8')
    
    # Check if our test token is in the request
    if "test_token_123" in body_str:
        return {
            "active": True,
            "client_id": "demo_client",
            "scope": "mcp:read mcp:write",
            "exp": 9999999999,  # Far future expiry
            "sub": "user1"
        }
    return {"active": False}

# Mock authorization endpoint
@app.get("/auth")
def authorize():
    return {"message": "Mock authorization endpoint"}

# Mock token endpoint
@app.post("/token")
def token():
    return {
        "access_token": "test_token_123",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "mcp:read mcp:write"
    }

if __name__ == "__main__":
    print("🔐 Mock OAuth Server starting on http://localhost:3000")
    print("Discovery: http://localhost:3000/.well-known/oauth-authorization-server")
    uvicorn.run(app, host="127.0.0.1", port=3000) 