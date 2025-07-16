import asyncio
import json
import logging
import os
import webbrowser
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs
from typing import Optional, Dict, Any
import httpx
from aiohttp import web, ClientSession as AIOHTTPClientSession
from aiohttp.web_runner import AppRunner, TCPSite
from dotenv import load_dotenv

from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# Load environment variables from .env file
load_dotenv()


class GoogleOAuthClient:
    """Google OAuth 2.0 client with PKCE for MCP authentication."""
    
    def __init__(self):
        # Load configuration from environment variables
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/oauth/callback')
        
        # OAuth endpoints
        self.auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        
        # PKCE parameters
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        
        # State for security
        self.state = secrets.token_urlsafe(32)
        
        # Storage for auth code
        self.auth_code: Optional[str] = None
        self.auth_error: Optional[str] = None
        
    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier."""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    def get_authorization_url(self) -> str:
        """Build Google OAuth authorization URL with PKCE."""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': self.state,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    async def handle_callback(self, request) -> web.Response:
        """Handle OAuth callback from Google."""
        try:
            query_params = dict(request.query)
            
            # Check for errors
            if 'error' in query_params:
                self.auth_error = f"OAuth error: {query_params.get('error')} - {query_params.get('error_description', '')}"
                return web.Response(text=f"❌ Authentication failed: {self.auth_error}", status=400)
            
            # Verify state parameter
            if query_params.get('state') != self.state:
                self.auth_error = "Invalid state parameter"
                return web.Response(text="❌ Authentication failed: Invalid state", status=400)
            
            # Get authorization code
            self.auth_code = query_params.get('code')
            if not self.auth_code:
                self.auth_error = "No authorization code received"
                return web.Response(text="❌ Authentication failed: No authorization code", status=400)
            
            return web.Response(text="✅ Authentication successful! You can close this window.", status=200)
            
        except Exception as e:
            self.auth_error = str(e)
            return web.Response(text=f"❌ Callback error: {e}", status=500)
    
    async def start_callback_server(self) -> tuple[AppRunner, TCPSite]:
        """Start local callback server."""
        app = web.Application()
        app.router.add_get('/oauth/callback', self.handle_callback)
        
        runner = AppRunner(app)
        await runner.setup()
        
        site = TCPSite(runner, 'localhost', 8080)
        await site.start()
        
        return runner, site
    
    async def exchange_code_for_tokens(self) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        if not self.auth_code:
            raise ValueError("No authorization code available")
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': self.auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code_verifier': self.code_verifier
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
            
            return response.json()


async def get_oauth_token() -> str:
    """Get OAuth access token through proper OAuth 2.0 flow."""
    
    # Check environment first
    access_token = os.getenv("GOOGLE_ACCESS_TOKEN")
    if access_token:
        print("🔑 Using access token from environment variable")
        return access_token
    
    print("🔐 Starting Google OAuth 2.0 flow...")
    print("=" * 50)
    
    # Initialize OAuth client
    oauth_client = GoogleOAuthClient()
    
    # Start callback server
    print("🌐 Starting callback server on http://localhost:8080...")
    runner, site = await oauth_client.start_callback_server()
    
    try:
        # Get authorization URL and open browser
        auth_url = oauth_client.get_authorization_url()
        print(f"🔗 Opening browser for authorization...")
        print(f"   If browser doesn't open, go to: {auth_url}")
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("⏳ Waiting for authorization callback...")
        print("   Please complete the authentication in your browser...")
        
        # Poll for completion
        max_wait = 300  # 5 minutes
        wait_time = 0
        while wait_time < max_wait:
            if oauth_client.auth_code or oauth_client.auth_error:
                break
            await asyncio.sleep(1)
            wait_time += 1
        
        if oauth_client.auth_error:
            raise Exception(f"OAuth failed: {oauth_client.auth_error}")
        
        if not oauth_client.auth_code:
            raise Exception("Timeout waiting for authorization")
        
        print("✅ Authorization code received!")
        
        # Exchange code for tokens
        print("🔄 Exchanging authorization code for access token...")
        token_response = await oauth_client.exchange_code_for_tokens()
        
        access_token = token_response.get('access_token')
        id_token = token_response.get('id_token')  # This is the JWT we need for the server
        
        if not id_token:
            raise Exception("No ID token received from Google")
        
        print("✅ OAuth 2.0 flow completed successfully!")
        print(f"💡 To skip this flow next time, set: export GOOGLE_ACCESS_TOKEN='{id_token[:50]}...'")
        
        return id_token  # Return the JWT ID token for server authentication
        
    finally:
        # Cleanup callback server
        await runner.cleanup()


async def test_mcp_server(server_name: str, server_url: str, jwt_token: str) -> None:
    """Test a specific MCP server implementation."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"\n🔍 Testing {server_name}")
    logger.info(f"🔌 Connecting to: {server_url}")
    
    try:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with streamablehttp_client(server_url, headers=headers) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                logger.info(f"✅ Connected to {server_name}")
                
                # List available tools
                tools_response = await session.list_tools()
                tools = tools_response.tools
                tool_names = [tool.name for tool in tools]
                logger.info(f"🛠️ Available tools: {tool_names}")
                
                # Test all tools
                for tool in tools:
                    logger.info(f"\n🔍 Testing tool: {tool.name}")
                    try:
                        result = await session.call_tool(tool.name, {})
                        if result.content:
                            content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                            logger.info(f"   ✅ Result: {content}")
                        else:
                            logger.info("   ⚠️  No content returned")
                    except Exception as e:
                        logger.error(f"   ❌ Tool error: {e}")
                
                logger.info(f"\n🎉 {server_name} testing completed!")
                
    except Exception as e:
        logger.error(f"❌ {server_name} connection failed: {e}")


async def main() -> None:
    """Test Google OAuth MCP integration with multiple server implementations."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Google OAuth MCP Client - Multi-Server Test")
    logger.info("=" * 60)
    
    try:
        # Get OAuth token through proper flow
        jwt_token = await get_oauth_token()
        logger.info("✅ JWT token obtained")
        
        # Test servers - you can choose which ones to test
        servers_to_test = [
            ("FastMCP Native Auth", "http://localhost:8001/mcp/"),
            ("MCP-Auth Integration", "http://localhost:8002/mcp/"),
        ]
        
        # Check which servers are running
        available_servers = []
        for name, url in servers_to_test:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url.replace('/mcp/', '/.well-known/oauth-authorization-server'), timeout=2)
                    if response.status_code == 200:
                        available_servers.append((name, url))
                        logger.info(f"✅ {name} is running on {url}")
                    else:
                        logger.warning(f"⚠️  {name} responded with {response.status_code}")
            except Exception:
                logger.warning(f"⚠️  {name} is not running on {url}")
        
        if not available_servers:
            logger.error("❌ No MCP servers are running! Please start a server first.")
            return
        
        # Test each available server
        for server_name, server_url in available_servers:
            await test_mcp_server(server_name, server_url, jwt_token)
            
    except Exception as e:
        logger.error(f"❌ Client error: {e}")
        return


if __name__ == "__main__":
    asyncio.run(main()) 