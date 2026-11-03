import os
import asyncio
import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types

app = FastAPI()

# Read your knowledge base if available
KNOWLEDGE_TEXT = ""
if os.path.exists("knowledge.txt"):
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        KNOWLEDGE_TEXT = f.read()

# Initialize Google GenAI Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = f"""
You are a friendly real-time voice customer support assistant.
Speak concisely in 1-2 sentences at a time.
Use the knowledge base below to answer questions:

--- KNOWLEDGE BASE ---
{KNOWLEDGE_TEXT}
--- END KNOWLEDGE BASE ---
"""

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Configure Gemini Live API Session
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],  # Native Audio Response
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=SYSTEM_INSTRUCTION)]
        )
    )

    # Use the live preview model endpoint optimized for low latency
    async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=config) as session:
        
        async def receive_from_client():
            """Receives audio chunks from browser mic and sends to Gemini."""
            try:
                while True:
                    data = await websocket.receive_text()
                    payload = json.loads(data)
                    
                    if "audio" in payload:
                        # Decode base64 16kHz PCM audio chunk from browser
                        raw_pcm = base64.b64decode(payload["audio"])
                        await session.send_realtime_input(
                            audio=types.Blob(data=raw_pcm, mime_type="audio/pcm;rate=16000")
                        )
            except WebSocketDisconnect:
                pass

        async def send_to_client():
            """Receives Gemini voice response and streams back to browser speakers."""
            try:
                async for response in session.receive():
                    server_content = response.server_content
                    if server_content is not None:
                        model_turn = server_content.model_turn
                        if model_turn is not None:
                            for part in model_turn.parts:
                                if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                                    # Base64 encode 24kHz PCM audio chunk for browser playback
                                    b64_audio = base64.b64encode(part.inline_data.data).decode("utf-8")
                                    await websocket.send_text(json.dumps({"audio": b64_audio}))
            except Exception as e:
                print(f"Streaming error: {e}")

        # Run both send and receive tasks concurrently
        await asyncio.gather(receive_from_client(), send_to_client())

@app.get("/")
async def get_index():
    """Serves the frontend WebRTC voice interface."""
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)