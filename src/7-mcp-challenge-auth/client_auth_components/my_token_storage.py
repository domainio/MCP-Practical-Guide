import json
import os
from typing import Optional
from mcp.client.auth import TokenStorage
from mcp.shared.auth import OAuthToken, OAuthClientInformationFull


class MyTokenStorage(TokenStorage):
    def __init__(self) -> None:
        # Store tokens file in the same directory as this component
        self.storage_dir = os.path.dirname(os.path.abspath(__file__))
        self.tokens_file = os.path.join(self.storage_dir, "tokens.json")
        self.client_info_file = os.path.join(self.storage_dir, "client_info.json")
        
        print(f"[TokenStorage] Using storage directory: {self.storage_dir}")
    
    async def get_tokens(self) -> Optional[OAuthToken]:
        """Load tokens from file"""
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r') as f:
                    data = json.load(f)
                    tokens = OAuthToken(
                        access_token=data['access_token'],
                        token_type=data.get('token_type', 'bearer'),
                        expires_in=data.get('expires_in'),
                        refresh_token=data.get('refresh_token'),
                        scope=data.get('scope')
                    )
                    print(f"[get_tokens] Loaded from file: access_token={tokens.access_token[:10]}...")
                    return tokens
            else:
                print(f"[get_tokens] No tokens file found at {self.tokens_file}")
                return None
        except Exception as e:
            print(f"[get_tokens] Error loading tokens: {e}")
            return None
    
    async def set_tokens(self, tokens: OAuthToken) -> None:
        """Save tokens to file"""
        try:
            data = {
                'access_token': tokens.access_token,
                'token_type': tokens.token_type,
                'expires_in': tokens.expires_in,
                'refresh_token': tokens.refresh_token,
                'scope': tokens.scope
            }
            
            # Ensure directory exists
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Write to file with secure permissions (readable only by owner)
            with open(self.tokens_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set secure file permissions (600 = owner read/write only)
            os.chmod(self.tokens_file, 0o600)
            
            print(f"[set_tokens] Saved to file: access_token={tokens.access_token[:10]}...")
        except Exception as e:
            print(f"[set_tokens] Error saving tokens: {e}")
    
    async def get_client_info(self) -> Optional[OAuthClientInformationFull]:
        """Load client info from file"""
        try:
            if os.path.exists(self.client_info_file):
                with open(self.client_info_file, 'r') as f:
                    data = json.load(f)
                    client_info = OAuthClientInformationFull(
                        client_id=data['client_id'],
                        client_secret=data.get('client_secret'),
                        client_id_issued_at=data.get('client_id_issued_at'),
                        client_secret_expires_at=data.get('client_secret_expires_at'),
                        registration_access_token=data.get('registration_access_token'),
                        registration_client_uri=data.get('registration_client_uri'),
                        client_name=data['client_name'],
                        redirect_uris=data['redirect_uris'],
                        grant_types=data.get('grant_types', []),
                        response_types=data.get('response_types', []),
                        scope=data.get('scope'),
                        token_endpoint_auth_method=data.get('token_endpoint_auth_method')
                    )
                    print(f"[get_client_info] Loaded from file: client_id={client_info.client_id}")
                    return client_info
            else:
                print(f"[get_client_info] No client info file found at {self.client_info_file}")
                return None
        except Exception as e:
            print(f"[get_client_info] Error loading client info: {e}")
            return None
    
    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        """Save client info to file"""
        try:
            data = {
                'client_id': client_info.client_id,
                'client_secret': client_info.client_secret,
                'client_id_issued_at': client_info.client_id_issued_at,
                'client_secret_expires_at': client_info.client_secret_expires_at,
                'registration_access_token': client_info.registration_access_token,
                'registration_client_uri': client_info.registration_client_uri,
                'client_name': client_info.client_name,
                'redirect_uris': client_info.redirect_uris,
                'grant_types': client_info.grant_types,
                'response_types': client_info.response_types,
                'scope': client_info.scope,
                'token_endpoint_auth_method': client_info.token_endpoint_auth_method
            }
            
            # Ensure directory exists
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Write to file with secure permissions
            with open(self.client_info_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set secure file permissions (600 = owner read/write only)
            os.chmod(self.client_info_file, 0o600)
            
            print(f"[set_client_info] Saved to file: client_id={client_info.client_id}")
        except Exception as e:
            print(f"[set_client_info] Error saving client info: {e}")

    def clear_tokens(self) -> None:
        """Clear stored tokens (useful for testing or logout)"""
        try:
            if os.path.exists(self.tokens_file):
                os.remove(self.tokens_file)
                print(f"[clear_tokens] Removed tokens file")
            if os.path.exists(self.client_info_file):
                os.remove(self.client_info_file)
                print(f"[clear_tokens] Removed client info file")
        except Exception as e:
            print(f"[clear_tokens] Error clearing tokens: {e}")
