FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install -e .

# Copy application
COPY server.py ./

# Run the MCP server
CMD ["python", "server.py"] 