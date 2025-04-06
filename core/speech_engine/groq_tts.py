"""
Groq TTS module for the Tesseract Project
Provides Text-to-Speech functionality using Groq's API.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, Union, IO

# Import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: Groq package not installed. TTS functionality will be disabled.")

class GroqTTSProcessor:
    """Provides Text-to-Speech functionality using Groq's API."""
    
    def __init__(self):
        """Initialize the Groq TTS processor."""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.available = GROQ_AVAILABLE and self.api_key is not None
        
        if self.available:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            if GROQ_AVAILABLE and self.api_key is None:
                print("Warning: GROQ_API_KEY not found in environment variables. TTS will be disabled.")
    
    def text_to_speech(
        self, 
        text: str, 
        voice: str = "Aaliyah-PlayAI", 
        model: str = "playai-tts",
        response_format: str = "wav",
        output_path: Optional[Union[str, Path, IO]] = None
    ) -> Optional[str]:
        """
        Convert text to speech using Groq's API.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use
            model: The model to use
            response_format: The output format (wav or mp3)
            output_path: Optional path to save the audio file
            
        Returns:
            Path to the output file if output_path is None, otherwise None
        """
        if not self.available:
            print("Groq TTS is not available. Check API key and dependencies.")
            return None
        
        # Validate text
        if not text or not text.strip():
            print("Error: Empty text provided for TTS")
            return None
            
        try:
            # Create response
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                response_format=response_format,
                input=text
            )
            
            # Handle output
            if output_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=f".{response_format}"
                )
                output_path = temp_file.name
                temp_file.close()
                
            # Stream to file
            if isinstance(output_path, (str, Path)):
                response.stream_to_file(output_path)
                return str(output_path)
            else:
                # Stream to file-like object
                response.stream_to_file(output_path)
                return None
                
        except Exception as e:
            print(f"Error in Groq TTS: {str(e)}")
            return None
    
    def get_available_voices(self) -> list:
        """
        Get list of available voices.
        
        Returns:
            List of available voice names
        """
        # This is a placeholder - Groq might provide an API for this in the future
        # For now, return the known voices
        return [
            "Aaliyah-PlayAI",
            "Aaron-PlayAI",
            "Antonio-PlayAI",
            "Avery-PlayAI",
            "Daniel-PlayAI",
            "Davis-PlayAI",
            "Isabella-PlayAI",
            "Jackson-PlayAI", 
            "Olivia-PlayAI",
            "Thomas-PlayAI"
        ]
    
    def is_available(self) -> bool:
        """
        Check if Groq TTS is available.
        
        Returns:
            True if available, False otherwise
        """
        return self.available

# Create a singleton instance
tts_processor = None

def get_tts_processor() -> GroqTTSProcessor:
    """
    Get or create the TTS processor instance.
    
    Returns:
        GroqTTSProcessor instance
    """
    global tts_processor
    if tts_processor is None:
        tts_processor = GroqTTSProcessor()
    return tts_processor