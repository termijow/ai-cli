"""WhatsApp message handler for order ingestion."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

import requests
import whisper


class WhatsAppHandler:
    """Handler for WhatsApp messages and order processing."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the WhatsApp handler.
        
        Args:
            storage_path: Path to store downloaded audio files
        """
        self.storage_path = storage_path or os.getenv("AUDIO_STORAGE_PATH", "/tmp/ai_orders_audio")
        os.makedirs(self.storage_path, exist_ok=True)
    
    def download_audio(self, url: str, filename: Optional[str] = None) -> str:
        """
        Download audio from URL and return local path.
        
        Args:
            url: URL of the audio file
            filename: Optional filename
            
        Returns:
            Local path to the downloaded file
        """
        if filename:
            audio_path = os.path.join(self.storage_path, filename)
        else:
            # Generate filename from URL
            filename = url.split("/")[-1]
            audio_path = os.path.join(self.storage_path, filename)
        
        # Create directory
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        # Download audio
        response = requests.get(url)
        response.raise_for_status()
        
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        
        return audio_path
    
    def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es')
            
        Returns:
            Transcribed text
        """
        # Use Whisper for transcription
        model = whisper.load_model("large", device="cpu")
        
        # Get audio path relative to app root
        audio_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(audio_path)))),
            audio_path
        )
        
        # Transcribe
        result = model.transcribe(audio_path, language=language)
        
        return result.get("text", "")
    
    def validate_order(
        self,
        extracted_order,
        matched_items,
        validation_config: Optional[dict] = None,
    ) -> dict:
        """
        Validate the extracted order.
        
        Args:
            extracted_order: Extracted order information
            matched_items: Matched items from catalog
            validation_config: Validation configuration
            
        Returns:
            Validation result
        """
        if not validation_config:
            validation_config = {
                "min_items": 1,
                "max_items": 10,
                "allowed_currencies": ["USD", "EUR", "GBP"],
            }
        
        # Validate item count
        item_count = len(matched_items)
        if item_count < validation_config["min_items"]:
            return {
                "success": False,
                "error": f"Minimum {validation_config['min_items']} items required, got {item_count}",
            }
        
        if item_count > validation_config["max_items"]:
            return {
                "success": False,
                "error": f"Maximum {validation_config['max_items']} items allowed, got {item_count}",
            }
        
        # Validate currency
        currency = extracted_order.get("currency")
        if currency and currency not in validation_config["allowed_currencies"]:
            return {
                "success": False,
                "error": f"Currency {currency} not in allowed list",
            }
        
        return {
            "success": True,
            "order_id": extracted_order.get("order_id"),
            "items": matched_items,
            "messages": ["Order validated successfully"],
            "warnings": [],
            "recommendations": [],
        }


async def ingest_whatsapp_message(
    audio_url: str,
    audio_filename: Optional[str] = None,
    message_id: Optional[str] = None,
    catalog_url: Optional[str] = None,
    validation_config: Optional[dict] = None,
) -> dict:
    """
    Ingest a WhatsApp message and process it.
    
    Args:
        audio_url: URL of the audio file
        audio_filename: Optional filename
        message_id: WhatsApp message ID
        catalog_url: URL to the product catalog
        validation_config: Validation configuration
        
    Returns:
        Processing result
    """
    handler = WhatsAppHandler()
    
    # Download audio
    audio_path = handler.download_audio(audio_url, audio_filename)
    
    # Transcribe audio
    transcription = handler.transcribe_audio(audio_path)
    
    # Clean up audio file
    audio_path.unlink()
    
    # Process transcription (would call order extractor and fuzzy matcher here)
    # This is a placeholder for the actual processing flow
    
    return {
        "status": "processed",
        "transcription": transcription,
        "message_id": message_id,
    }
