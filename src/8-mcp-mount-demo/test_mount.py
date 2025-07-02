#!/usr/bin/env python3
"""
Test script to verify the MCP mounting demo works correctly.

This script demonstrates the key concepts without external dependencies.
"""

import sys
import os

def test_server_files():
    """Test that all server files exist and have the expected structure."""
    print("🔍 Testing MCP Mount Demo Structure...")
    
    required_files = [
        "main.py",
        "math_server.py", 
        "weather_server.py",
        "text_server.py",
        "client_example.py",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_server_imports():
    """Test that server files have correct import structure."""
    print("🔍 Testing server import structure...")
    
    servers = ["math_server.py", "weather_server.py", "text_server.py"]
    
    for server_file in servers:
        try:
            with open(server_file, 'r') as f:
                content = f.read()
                
            # Check for FastMCP import
            if "from fastmcp import FastMCP" not in content:
                print(f"❌ {server_file} missing FastMCP import")
                return False
                
            # Check for server instance creation
            if "FastMCP(" not in content:
                print(f"❌ {server_file} missing FastMCP instance")
                return False
                
            # Check for at least one tool
            if "@" not in content or ".tool()" not in content:
                print(f"❌ {server_file} missing tool definitions")
                return False
                
            print(f"✅ {server_file} structure correct")
            
        except Exception as e:
            print(f"❌ Error reading {server_file}: {e}")
            return False
    
    return True

def test_main_structure():
    """Test that main.py has the correct mounting structure."""
    print("🔍 Testing main application structure...")
    
    try:
        with open("main.py", 'r') as f:
            content = f.read()
        
        # Check for key mounting concepts
        checks = [
            ("FastAPI import", "from fastapi import FastAPI"),
            ("Server imports", "from math_server import math_mcp"),
            ("Mount calls", "app.mount("),
            ("sse_app usage", ".sse_app()"),
            ("Lifespan context", "contextlib.asynccontextmanager"),
            ("Session managers", "session_manager.run()")
        ]
        
        for check_name, check_string in checks:
            if check_string not in content:
                print(f"❌ {check_name} not found in main.py")
                return False
            print(f"✅ {check_name} found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False

def show_demo_info():
    """Show information about the demo."""
    print("\n🎯 MCP Mount Demo Information")
    print("=" * 50)
    print("This demo showcases mounting multiple MCP servers to an existing ASGI application.")
    print("\nKey Features:")
    print("• Multiple independent MCP servers (Math, Weather, Text)")
    print("• Mounted at different paths (/math, /weather, /text)")
    print("• Shared lifecycle management")
    print("• Web interface showing all mounted servers")
    print("• Client examples for testing")
    
    print("\n🚀 To Run:")
    print("1. cd src/8-mcp-mount-demo")
    print("2. python main.py")
    print("3. Visit http://localhost:8000")
    print("4. Test with: python client_example.py")
    
    print("\n💡 This demonstrates the MCP Python SDK's mounting capability:")
    print("   https://github.com/modelcontextprotocol/python-sdk#mounting-to-an-existing-asgi-server")

def main():
    """Run all tests."""
    print("🧪 MCP Mount Demo Tests")
    print("=" * 30)
    
    tests = [
        test_server_files,
        test_server_imports, 
        test_main_structure
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All tests passed!")
        show_demo_info()
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())