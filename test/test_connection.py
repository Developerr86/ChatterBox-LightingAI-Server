#!/usr/bin/env python3
"""
Simple connection test for the streaming WebSocket endpoint.
"""

import asyncio
import websockets
import json

async def test_connection(server_url):
    """Test basic WebSocket connection."""
    
    # Convert HTTP URL to WebSocket URL
    if server_url.startswith("https://"):
        ws_url = server_url.replace("https://", "wss://").replace("/tts", "/tts-stream")
    elif server_url.startswith("http://"):
        ws_url = server_url.replace("http://", "ws://").replace("/tts", "/tts-stream")
    else:
        ws_url = server_url
    
    print(f"Testing connection to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✓ Connection established successfully!")
            
            # Send a simple test message
            test_request = {
                "text": "Hello world!",
                "language": "en"
            }
            
            print("Sending test request...")
            await websocket.send(json.dumps(test_request))
            
            # Wait for responses
            response_count = 0
            async for message in websocket:
                try:
                    response = json.loads(message)
                    response_count += 1
                    
                    print(f"Response {response_count}: {response.get('type', 'unknown')}")
                    
                    if response.get("type") == "audio_chunk" and response.get("is_final"):
                        print("✓ Received final chunk - test successful!")
                        break
                    elif response.get("type") == "error":
                        print(f"✗ Server error: {response.get('error')}")
                        break
                        
                    if response_count > 10:  # Safety limit
                        print("✓ Received multiple responses - connection working")
                        break
                        
                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON response: {message}")
                    break
                    
    except websockets.exceptions.InvalidURI:
        print("✗ Invalid WebSocket URL")
    except websockets.exceptions.ConnectionClosed:
        print("✗ Connection closed unexpectedly")
    except Exception as e:
        print(f"✗ Connection failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_connection.py <server_url>")
        print("Example: python test_connection.py https://your-lightning-url/tts")
        sys.exit(1)
    
    server_url = sys.argv[1]
    asyncio.run(test_connection(server_url))