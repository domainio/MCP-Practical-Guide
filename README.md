# MCP Practical Examples

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
Basic MCP server with weather and stock tools, demonstrating fundamental client-server communication.
```bash
# Terminal 1: Run server
python src/1-mcp-simple-client-server/server.py

# Terminal 2: Run client  
python src/1-mcp-simple-client-server/client.py
```

### 2. MCP Client Agent
Integration of MCP client with LangGraph agents for conversational AI interactions.
```bash
# Terminal 1: Run server (from example 1)
python src/1-mcp-simple-client-server/server.py

# Terminal 2: Run agent client
python src/2-mcp-client-agent/agent.py
```

### 3. MCP Inspector (Debug Tool)
Use the MCP inspector to debug and explore your MCP servers.
```bash
mcp dev src/1-mcp-simple-client-server/server.py
# Open http://127.0.0.1:6274
```

### 4. Resources Example
MCP resources with MinIO storage backend for file and data management.
```bash
# Start MinIO storage
docker compose -f src/3-mcp-resource/resources/docker-compose.minio.yml up

# Terminal 1: Run server
python src/3-mcp-resource/server.py

# Terminal 2: Run resource client
python src/3-mcp-resource/client.py
```

### 5. Context & Progress Tracking
Advanced MCP server with context features including progress reporting and logging.
```bash
# Terminal 1: Run context server
python src/4-mcp-context/server.py

# Terminal 2: Run context client
python src/4-mcp-context/client.py
```

### 6. Prompts & Browser Automation
MCP server with custom prompts and browser automation capabilities.
```bash
# Terminal 1: Run prompt server
python src/5-mcp-prompt/server.py

# Terminal 2: Install browser dependencies
npx playwright install chromium

# Run browser automation
python src/5-mcp-prompt/browser_use.py

# Or run prompt client
python src/5-mcp-prompt/client.py
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

### 6. MCP Scale
Demonstrates scaling MCP servers with Redis state management and load balancing.
- **Stateless**: Simple scaling example
- **DB-State**: Redis-backed stateful scaling with Docker composition

### 7. Context Window Management
Advanced context window management techniques for large conversations.

### 8. MCP Semantics
Advanced AI patterns including agent elicitation and sampling techniques.

### 9. MCP Authentication
OAuth authentication flows and protected MCP servers.
- **9-mcp-auth**: General OAuth implementation
- **9-auth-google**: Google-specific OAuth integration

### 10. MCP Topology
Multi-server setups with registry patterns and nested server mounting.

---

**Need help?** Check individual example directories for specific instructions and additional documentation.

