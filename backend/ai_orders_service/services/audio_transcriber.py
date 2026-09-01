"""Audio transcription service using Whisper."""

import asyncio
import os
from typing import Optional
from pathlib import Path

import whisper
from huggingface_hub import hf_hub_download
from transformers import pipeline


class AudioTranscriber:
    """Service for transcribing audio files using Whisper."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        task: str = "transcribe",
        device: str = "auto",
        chunk_size: int = 512,
        use_gzip: bool = True,
    ):
        """
        Initialize the audio transcriber.
        
        Args:
            model: HuggingFace model name or local path
            task: Whisper task type (transcribe/translate)
            device: Device to use (auto/cpu/cuda)
            chunk_size: Chunk size for processing
            use_gzip: Whether to use gzip compression
        """
        self.model_name = model
        self.task = task
        self.device = device
        self.chunk_size = chunk_size
        self.use_gzip = use_gzip
        
        # Initialize Whisper model
        self.whisper = pipeline(
            "automatic-speech-recognition",
            model=model,
            task=task,
            device=device,
            chunk_size=chunk_size,
            return_tensors="pt",
            use_gzip=use_gzip,
        )
        
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """
        Transcribe audio from file.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es')
            verbose: Verbosity level
            
        Returns:
            Transcribed text
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get audio path relative to app root
        audio_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(audio_path)))),
            audio_path
        )
        
        if verbose:
            print(f"Transcribing audio: {audio_path}")
        
        # Transcribe
        transcription = self.whisper(audio_path)
        
        # Decode with language if specified
        if language:
            transcription = self.whisper(
                audio_path, 
                task="translate", 
                language=language
            )
        
        return transcription.get("text", "")
    
    def transcribe_from_url(
        self,
        url: str,
        language: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """
        Transcribe audio from URL.
        
        Args:
            url: URL of the audio file
            language: Language code
            verbose: Verbosity level
            
        Returns:
            Transcribed text
        """
        # Download audio file
        temp_path = Path(self._download_audio(url))
        
        # Transcribe
        transcription = self.transcribe(str(temp_path), language=language, verbose=verbose)
        
        # Clean up
        temp_path.unlink()
        
        return transcription
    
    def _download_audio(self, url: str) -> str:
        """Download audio from URL and return local path."""
        from huggingface_hub import hf_hub_download
        
        # Extract filename from URL
        filename = url.split("/")[-1]
        
        # Create temp directory
        temp_dir = Path(self._get_temp_dir())
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Download
        return str(hf_hub_download(
            repo_id=url,
            filename=filename,
            cache_dir=temp_dir,
            force_download=True,
        ))
    
    def _get_temp_dir(self) -> str:
        """Get or create temporary audio storage directory."""
        storage_path = os.getenv("AUDIO_STORAGE_PATH", "/tmp/ai_orders_audio")
        os.makedirs(storage_path, exist_ok=True)
        return storage_path
    
    async def transcribe_async(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> str:
        """
        Asynchronous transcription.
        
        Args:
            audio_path: Path to audio file
            language: Language code
            
        Returns:
            Transcribed text
        """
        return self.transcribe(audio_path, language=language)


async def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
) -> str:
    """
    Transcribe audio from file (async wrapper).
    
    Args:
        audio_path: Path to audio file
        language: Language code
        
    Returns:
        Transcribed text
    """
    transcriber = AudioTranscriber()
    return await transcriber.transcribe_async(audio_path, language)


def init_audio_transcriber(
    model: Optional[str] = None,
    task: str = "transcribe",
    device: str = "auto",
) -> AudioTranscriber:
    """
    Initialize and return an audio transcriber.
    
    Args:
        model: HuggingFace model name
        task: Whisper task type
        device: Device to use
        
    Returns:
        Configured AudioTranscriber instance
    """
    return AudioTranscriber(model, task, device)
