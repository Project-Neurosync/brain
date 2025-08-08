#!/usr/bin/env python3
"""
Test the chat endpoint to verify our HTTP fallback is working.
"""

import asyncio
import aiohttp
import json

async def test_chat_endpoint():
    """Test our chat endpoint with the updated HTTP fallback."""
    
    url = "http://localhost:8000/api/v1/chat/test"
    
    data = {
        "message": "Hello, can you help me with my project?",
        "project_id": None,
        "conversation_id": None,
        "stream": False
    }
    
    print("🔥 Testing chat endpoint with HTTP fallback...")
    print(f"URL: {url}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                print(f"🔥 Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("🔥 SUCCESS! Chat endpoint is working!")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
                    # Check if we got a real AI response (not an error message)
                    message = result.get("message", "")
                    if "DEBUG:" in message and "error" not in message.lower():
                        print("✅ HTTP fallback is working and Groq API responded!")
                        return True
                    elif "DEBUG:" in message:
                        print("⚠️ HTTP fallback triggered but encountered an error")
                        print(f"Error message: {message}")
                        return False
                    else:
                        print("⚠️ Unexpected response format")
                        return False
                else:
                    error_text = await response.text()
                    print(f"🔥 ERROR! HTTP {response.status}: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"🔥 EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat_endpoint())
    if success:
        print("✅ Chat endpoint test PASSED!")
    else:
        print("❌ Chat endpoint test FAILED!")
