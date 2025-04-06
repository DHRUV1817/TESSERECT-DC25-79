"""
FastAPI application for the Tesseract Project
Provides API endpoints for core functionalities.
"""
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import logging
import os
import datetime
import uuid
import tempfile
from pathlib import Path

# Import core modules
from core.reasoning_engine.cot_processor import ChainOfThoughtProcessor
from core.reasoning_engine.argument_validator import ArgumentValidator
from core.speech_engine.filler_detector import FillerDetector
from core.debate_engine.counterpoint_engine import CounterpointEngine
from core.debate_engine.socratic_questioner import SocraticQuestioner
from core.rag_engine.rag_processor import RAGProcessor

# Import TTS processor
from core.speech_engine.groq_tts import get_tts_processor

# Check for API keys
openai_api_key = os.getenv("OPENAI_API_KEY", "")
use_ai = bool(openai_api_key)
if not use_ai:
    print("Warning: OpenAI API key not found. Using simplified analysis methods.")

# Create FastAPI app
app = FastAPI(
    title="Tesseract Project API",
    description="API for the Tesseract Project application",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize service instances
cot_processor = ChainOfThoughtProcessor(complexity_level=2, use_ai=use_ai)
argument_validator = ArgumentValidator(use_openai=use_ai)
filler_detector = FillerDetector(use_ai=use_ai)
counterpoint_engine = CounterpointEngine(level=2)
socratic_questioner = SocraticQuestioner()
rag_processor = RAGProcessor()

# Pydantic models for request/response
class ArgumentRequest(BaseModel):
    text: str
    complexity_level: Optional[int] = Field(1, ge=1, le=3)
    context: Optional[str] = None

class TranscriptRequest(BaseModel):
    text: str

class CounterpointRequest(BaseModel):
    argument: str
    topic: Optional[str] = ""
    level: Optional[int] = Field(1, ge=1, le=3)

class QuestionRequest(BaseModel):
    argument: str
    count: Optional[int] = Field(3, ge=1, le=5)

class RAGRequest(BaseModel):
    query: str
    context: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "Aaliyah-PlayAI"

class VoiceListResponse(BaseModel):
    voices: List[str]
    tts_available: bool

class VoiceDescriptionResponse(BaseModel):
    voice: str
    gender: str
    style: str
    description: str

# Custom exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."}
    )

# Performance middleware
@app.middleware("http")
async def add_performance_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log API request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time*1000:.2f}ms"
    )
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.datetime.now().isoformat(),
        "version": app.version,
        "ai_enabled": use_ai
    }

# Reasoning engine endpoints
@app.post("/reasoning/analyze-argument")
async def analyze_argument(request: ArgumentRequest):
    try:
        # Update complexity level if provided
        if request.complexity_level != 1:
            cot_processor.complexity_level = request.complexity_level
            
        # Use RAG if context provided
        if request.context:
            # Get enhanced information using RAG
            rag_result = rag_processor.retrieve_and_generate(request.text, request.context)
            
            # Process argument with additional context
            result = cot_processor.process_argument(request.text)
            
            # Add RAG information to the result
            result["retrieved_information"] = rag_result.get("retrieved_information", [])
            result["enhanced_response"] = rag_result.get("response", "")
            
            return result
        else:
            # Standard processing without RAG
            result = cot_processor.process_argument(request.text)
            return result
    except Exception as e:
        logger.error(f"Error analyzing argument: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reasoning/validate-argument")
async def validate_argument(request: ArgumentRequest):
    try:
        result = argument_validator.validate_argument(request.text)
        return result
    except Exception as e:
        logger.error(f"Error validating argument: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Speech engine endpoints
@app.post("/speech/analyze-transcript")
async def analyze_transcript(request: TranscriptRequest):
    try:
        result = filler_detector.analyze_transcript(request.text)
        return result
    except Exception as e:
        logger.error(f"Error analyzing transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/speech/highlight-fillers")
async def highlight_fillers(request: TranscriptRequest):
    try:
        highlighted = filler_detector.highlight_fillers(request.text)
        return {"original": request.text, "highlighted": highlighted}
    except Exception as e:
        logger.error(f"Error highlighting fillers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Debate engine endpoints
@app.post("/debate/generate-counterpoints")
async def generate_counterpoints(request: CounterpointRequest):
    try:
        # Update complexity level if provided
        if request.level != 1:
            counterpoint_engine.level = min(max(request.level, 1), 3)
            
        result = counterpoint_engine.generate_counterpoints(
            request.argument, 
            request.topic
        )
        return result
    except Exception as e:
        logger.error(f"Error generating counterpoints: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debate/generate-questions")
async def generate_questions(request: QuestionRequest):
    try:
        questions = socratic_questioner.generate_questions(
            request.argument,
            request.count
        )
        
        return questions
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# RAG endpoint
@app.post("/knowledge/query")
async def query_knowledge(request: RAGRequest):
    try:
        result = rag_processor.retrieve_and_generate(
            request.query,
            request.context
        )
        return result
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# TTS endpoints
@app.post("/speech/tts")
async def text_to_speech(request: TTSRequest):
    try:
        tts_processor = get_tts_processor()
        
        # Add debug logging
        logger.info(f"TTS Processor Available: {tts_processor.is_available()}")
        logger.info(f"Using voice: {request.voice}")
        
        if not tts_processor.is_available():
            error_msg = "TTS service unavailable - check GROQ_API_KEY and network"
            logger.error(error_msg)
            return JSONResponse(
                status_code=503,
                content={"error": error_msg}
            )

        # Create temporary file with proper naming
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir="temp") as temp_file:
            output_path = temp_file.name

        # Generate speech with error wrapping
        try:
            result_path = tts_processor.text_to_speech(
                text=request.text,
                voice=request.voice,
                output_path=output_path
            )
        except Exception as api_error:
            logger.error(f"Groq API Error: {str(api_error)}")
            return JSONResponse(
                status_code=502,
                content={"error": f"TTS API Error: {str(api_error)}"}
            )

        # Verify file creation
        if not Path(result_path).exists():
            logger.error(f"File not created at {result_path}")
            return JSONResponse(
                status_code=500,
                content={"error": "Audio file generation failed"}
            )

        return FileResponse(
            result_path,
            media_type="audio/wav",
            filename="response.wav"
        )

    except Exception as e:
        logger.error(f"TTS Processing Error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )
@app.get("/speech/voices")
async def get_available_voices():
    """Get list of available TTS voices."""
    try:
        tts_processor = get_tts_processor()
        voices = tts_processor.get_available_voices()
        
        return VoiceListResponse(
            voices=voices,
            tts_available=tts_processor.is_available()
        )
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

