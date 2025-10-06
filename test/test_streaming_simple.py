#!/usr/bin/env python3
"""
Simple streaming test without audio playback - just saves the file.
"""

import asyncio
from streaming_client import StreamingTTSClient

async def test_simple_streaming():
    """Test streaming without real-time playback."""
    
    server_url = "https://7860-01k6maprxpehcykhskfne1wyer.cloudspaces.litng.ai/tts"
    
    test_text = """
    This is a test of the streaming functionality without real-time playback. 
    The audio chunks will be received and saved to a file, but not played in real-time.
    This helps us verify that the basic streaming communication works correctly.
    """
    
    print("Testing Streaming TTS (No Playback)")
    print("=" * 40)
    print(f"Text length: {len(test_text)} characters")
    print("-" * 40)
    
    # Create client with playback disabled
    client = StreamingTTSClient(server_url, enable_playback=False)
    
    try:
        await client.stream_tts(
            text=test_text.strip(),
            language="en",
            output_file="test_simple_output.wav",
            play_audio=False
        )
        print("\n✅ Simple streaming test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_streaming())