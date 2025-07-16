# MCP Workshop - Practical Examples

Hands-on examples for building AI applications with Model Context Protocol (MCP).

## Quick Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/domainio/MCP-Practical-Guide.git
   cd MCP-Practical-Guide
   ```

2. **Install dependencies**
   ```bash
   # Install uv if needed
   curl -sSf https://astral.sh/uv/install.sh | bash
   
   # Setup project
   uv venv && source .venv/bin/activate
   uv pip install -e .
   ```

3. **Configure environment**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_openai_api_key" > .env
   ```

## Examples

### 1. Simple Client-Server
```bash
# Terminal 1: Run server
python src/1-mcp-simple-client-server/server.py

# Terminal 2: Run client  
python src/1-mcp-simple-client-server/client.py
```

### 2. MCP Inspector (Debug Tool)
```bash
mcp dev src/1-mcp-simple-client-server/server.py
# Open http://127.0.0.1:6274
```

### 3. Resources Example
```bash
# Start MinIO storage
docker compose -f src/3-mcp-resource/resources/docker-compose.minio.yml up

# Run resource client
python src/3-mcp-resource/client.py
```

### 4. Browser Automation
```bash
# Install browser
npx playwright install chromium

# Run browser automation
python src/5-mcp-prompt/browser_use.py
```

## Alternative: Local Models

Use Ollama instead of OpenAI:

```bash
# Install and run Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2 && ollama run llama3.2

# Update .env
echo "OPENAI_API_BASE_URL=http://localhost:11434/v1" >> .env
echo "OPENAI_API_KEY=ollama-key" >> .env
```

## Challenges

Explore advanced examples in `src/challenges/`:
- **6-mcp-scale**: Scaling MCP servers
- **7-mcp-auth**: OAuth authentication  
- **8-mcp-topology**: Multi-server setups
- **9-mcp-semantics**: Advanced AI patterns
- **10-auth-google**: Google OAuth integration
- **11-context-window**: Context management

---

**Need help?** Check individual example directories for specific instructions.

