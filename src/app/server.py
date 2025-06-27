from fastapi import FastAPI

from src.app.voice import router as voice_router
from src.mock.customer_sessions import customer_session_store
from src.app.voice.router import generate_response

app = FastAPI()

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():

    session = customer_session_store.get_session_by_phone_and_channel("+14803828571", "voice")
    if not session:
        session = customer_session_store.create_session("+14803828571", "voice")
    
    await generate_response("hey", session, print)
    

    """Simple liveness probe endpoint."""
    return {"status": "ok"}

# Include routers
app.include_router(voice_router, prefix="/voice")
