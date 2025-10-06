#!/usr/bin/env python3
"""
Test script to demonstrate the streaming TTS functionality.
This script can be used to test the streaming endpoint locally or with Lightning AI.
"""

import asyncio
import json
from streaming_client import StreamingTTSClient

async def test_streaming():
    """Test the streaming functionality with sample text."""
    
    # Replace with your actual Lightning AI URL
    server_url = "https://7860-01k6maprxpehcykhskfne1wyer.cloudspaces.litng.ai/tts"  # Update this!
    
    # Sample long text for testing
    test_text = """
    Welcome to the ChatterBox streaming TTS demonstration. This is a longer text that will be 
    broken down into smaller chunks for faster processing. Each sentence will be processed 
    separately and streamed back to the client as soon as it's ready. This approach provides 
    a much better user experience, especially for longer texts, as users can start hearing 
    the audio output while the rest is still being processed. The streaming functionality 
    uses WebSocket connections to maintain a persistent channel between the client and server.
    """
    
    print("Testing Streaming TTS...")
    print(f"Text length: {len(test_text)} characters")
    print("-" * 50)
    
    client = StreamingTTSClient(server_url)
    
    try:
        await client.stream_tts(
            text=test_text.strip(),
            language="en",
            output_file="test_streaming_output.wav"
        )
        print("\nStreaming test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        print("\nMake sure to:")
        print("1. Update the server_url in this script")
        print("2. Ensure your Lightning AI server is running")
        print("3. Check that websockets are supported")

if __name__ == "__main__":
    print("ChatterBox Streaming TTS Test")
    print("=" * 40)
    asyncio.run(test_streaming())