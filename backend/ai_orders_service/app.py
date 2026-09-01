"""AI Orders Microservice - FastAPI Application."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import Settings
from .handlers.whatsapp import WhatsAppHandler
from .services.order_extractor import OrderExtractor
from .services.fuzzy_matcher import FuzzyMatcher
from .schemas.order import OrderRequest, ExtractedOrder, OrderValidationResult


app = FastAPI(
    title="AI Orders Microservice",
    description="WhatsApp order processing service with audio transcription, LLM extraction, and fuzzy matching",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    settings = Settings()
    # Services will be initialized on-demand by handlers


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Orders Microservice",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            {"path": "/ingest", "method": "POST", "description": "Ingest WhatsApp audio message"},
            {"path": "/validate", "method": "POST", "description": "Validate extracted order"},
        ]
    }


@app.post("/ingest", response_model=OrderValidationResult)
async def ingest_audio(request: OrderRequest):
    """
    Ingest an audio message from WhatsApp.

    Expected payload:
    - audio_url: URL of the audio file (e.g., from WhatsApp Web download)
    - audio_filename: Original filename (optional)
    - message_id: WhatsApp message ID (optional)

    Flow:
    1. Download audio if URL provided
    2. Transcribe audio to text (Whisper)
    3. Extract order information (LLM with structured output)
    4. Match with product catalog (fuzzy matching with embeddings)
    5. Validate and return order
    """
    try:
        # Initialize services
        handler = WhatsAppHandler()
        extractor = OrderExtractor()
        matcher = FuzzyMatcher()

        # Process the audio message
        audio_url = request.audio_url
        message_id = request.message_id or "unknown"

        # Step 1: Download audio if URL provided
        if audio_url:
            audio_path = await handler.download_audio(audio_url)
        else:
            audio_path = request.audio_path

        # Step 2: Transcribe audio to text
        transcription = await handler.transcribe_audio(audio_path)

        # Step 3: Extract order information
        extracted = extractor.extract_from_transcription(transcription)

        # Step 4: Match with product catalog
        matched_products = matcher.match_products(extracted.items, request.catalog_url)

        # Step 5: Validate and return order
        result = handler.validate_order(extracted, matched_products, request.validation_config)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order ingestion failed: {str(e)}",
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3095)
