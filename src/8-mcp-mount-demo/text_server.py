"""
Text Utility MCP Server - provides text processing tools.
This server can be mounted to an existing ASGI application.
"""

import re
import hashlib
from typing import Dict, Any
from fastmcp import FastMCP

# Create the text utility MCP server
text_mcp = FastMCP("TextUtilityServer")

@text_mcp.tool()
def count_words(text: str) -> Dict[str, Any]:
    """Count words, characters, and lines in text."""
    lines = text.split('\n')
    words = text.split()
    characters = len(text)
    characters_no_spaces = len(text.replace(' ', ''))
    
    return {
        "words": len(words),
        "characters": characters,
        "characters_without_spaces": characters_no_spaces,
        "lines": len(lines),
        "paragraphs": len([line for line in lines if line.strip()])
    }

@text_mcp.tool()
def transform_text(text: str, operation: str) -> str:
    """Transform text using various operations: uppercase, lowercase, title, reverse."""
    operations = {
        "uppercase": text.upper(),
        "lowercase": text.lower(),
        "title": text.title(),
        "reverse": text[::-1],
        "capitalize": text.capitalize(),
        "swapcase": text.swapcase()
    }
    
    if operation not in operations:
        available = ", ".join(operations.keys())
        raise ValueError(f"Unknown operation '{operation}'. Available: {available}")
    
    return operations[operation]

@text_mcp.tool()
def extract_emails(text: str) -> list:
    """Extract email addresses from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails

@text_mcp.tool()
def extract_urls(text: str) -> list:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls

@text_mcp.tool()
def generate_hash(text: str, algorithm: str = "sha256") -> str:
    """Generate hash of text using specified algorithm (md5, sha1, sha256, sha512)."""
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    if algorithm not in algorithms:
        available = ", ".join(algorithms.keys())
        raise ValueError(f"Unknown algorithm '{algorithm}'. Available: {available}")
    
    hash_obj = algorithms[algorithm]()
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()

@text_mcp.tool()
def find_and_replace(text: str, find: str, replace: str, case_sensitive: bool = True) -> str:
    """Find and replace text with optional case sensitivity."""
    if case_sensitive:
        return text.replace(find, replace)
    else:
        # Case-insensitive replacement
        pattern = re.compile(re.escape(find), re.IGNORECASE)
        return pattern.sub(replace, text)

@text_mcp.resource("text://regex/common")
def get_common_regex_patterns() -> str:
    """Get common regex patterns for text processing."""
    return """
Common Regular Expression Patterns:

Email: \\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b
Phone (US): \\(\\d{3}\\)\\s?\\d{3}-\\d{4}|\\d{3}-\\d{3}-\\d{4}
URL: http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\\\(\\\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
IPv4: \\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b
Date (MM/DD/YYYY): \\b\\d{1,2}/\\d{1,2}/\\d{4}\\b
Time (HH:MM): \\b\\d{1,2}:\\d{2}\\b
Credit Card: \\b(?:\\d{4}[-\\s]?){3}\\d{4}\\b
Social Security: \\b\\d{3}-\\d{2}-\\d{4}\\b
"""

@text_mcp.resource("text://encoding/info")
def get_encoding_info() -> str:
    """Get information about text encoding."""
    return """
Text Encoding Information:

Common Encodings:
- UTF-8: Universal encoding supporting all Unicode characters
- ASCII: Basic 7-bit encoding for English characters
- Latin-1 (ISO-8859-1): Western European characters
- Windows-1252: Windows default for Western languages

Hash Algorithms:
- MD5: 128-bit hash (not cryptographically secure)
- SHA-1: 160-bit hash (deprecated for security)
- SHA-256: 256-bit hash (recommended)
- SHA-512: 512-bit hash (highest security)
"""

@text_mcp.prompt()
def text_analysis_prompt(text: str) -> str:
    """Create a prompt for comprehensive text analysis."""
    return f"""
Please perform a comprehensive analysis of the following text:

TEXT:
{text}

Please analyze:
1. Word and character counts
2. Reading level and complexity
3. Sentiment and tone
4. Key themes and topics
5. Writing style and structure
6. Any notable patterns or characteristics

Provide insights and suggestions for improvement if applicable.
"""

if __name__ == "__main__":
    # This allows the server to run standalone
    text_mcp.run(transport="sse", port=8003)