#!/usr/bin/env python3
"""
Test script for Patra Unified Server tools
"""

import os
import sys
import json

# Add server directory to path
sys.path.append('server')

def test_tools_import():
    """Test that tools can be imported."""
    try:
        from patra_tools import get_patra_tools, PatraToolsClient
        print("✅ Successfully imported Patra tools")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Patra tools: {e}")
        return False

def test_tools_creation():
    """Test that tools can be created."""
    try:
        from patra_tools import get_patra_tools
        
        # Set mock environment variables
        os.environ["NEO4J_URI"] = "bolt://localhost:7687"
        os.environ["NEO4J_USER"] = "neo4j"
        os.environ["NEO4J_PWD"] = "password"
        
        tools = get_patra_tools()
        print(f"✅ Successfully created {len(tools)} tools")
        
        # Print tool information
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create tools: {e}")
        return False

def test_tool_schemas():
    """Test that tools have proper schemas."""
    try:
        from patra_tools import get_patra_tools
        
        tools = get_patra_tools()
        
        for tool in tools:
            # Check that tool has required attributes
            assert hasattr(tool, 'name'), f"Tool {tool} missing 'name' attribute"
            assert hasattr(tool, 'description'), f"Tool {tool} missing 'description' attribute"
            assert hasattr(tool, '_run'), f"Tool {tool} missing '_run' method"
            
            # Check that name and description are not empty
            assert tool.name, f"Tool {tool} has empty name"
            assert tool.description, f"Tool {tool} has empty description"
            
            print(f"✅ Tool '{tool.name}' has valid schema")
        
        return True
    except Exception as e:
        print(f"❌ Tool schema validation failed: {e}")
        return False

def test_server_import():
    """Test that server can be imported."""
    try:
        from server.server import get_langgraph_tools
        tools = get_langgraph_tools()
        print(f"✅ Successfully imported server with {len(tools)} tools")
        return True
    except Exception as e:
        print(f"❌ Failed to import server: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Patra Server Tools")
    print("=" * 50)
    
    tests = [
        ("Import Tools", test_tools_import),
        ("Create Tools", test_tools_creation),
        ("Validate Schemas", test_tool_schemas),
        ("Import Server", test_server_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Patra Unified Server is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
