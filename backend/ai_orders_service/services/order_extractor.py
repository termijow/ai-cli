"""Order extraction service using LLM with structured output."""

import json
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field

from ..schemas.order import ExtractedOrder


class OrderExtractor:
    """Service for extracting order information from transcribed text using LLM."""
    
    def __init__(
        self,
        model: str = "google/gemma-2-9b-it",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        prompt_template: Optional[str] = None,
    ):
        """
        Initialize the order extractor.
        
        Args:
            model: LLM model name
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            prompt_template: Custom prompt template
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template
        
        # Load custom prompt if provided
        if prompt_template:
            with open(prompt_template, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
    
    def extract_from_text(
        self,
        text: str,
        catalog_items: Optional[list] = None,
        validation_config: Optional[dict] = None,
    ) -> ExtractedOrder:
        """
        Extract order from transcribed text.
        
        Args:
            text: Transcribed text from audio
            catalog_items: List of available catalog items (optional, for matching)
            validation_config: Validation configuration (min/max items, currencies)
            
        Returns:
            ExtractedOrder object
        """
        from ..utils.prompt import generate_extraction_prompt
        
        prompt = generate_extraction_prompt(
            text=text,
            catalog_items=catalog_items,
            validation_config=validation_config,
        )
        
        # Extract using LLM
        extracted = self._extract_with_llm(prompt)
        
        return extracted
    
    def _extract_with_llm(self, prompt: str) -> ExtractedOrder:
        """
        Extract order from text using LLM.
        
        Note: This is a placeholder - actual LLM integration needed.
        For now, return a sample structure.
        """
        return ExtractedOrder(
            order_id="ORD_20240115_001",
            extracted_from_text=prompt,
            items=[],
            subtotal=0.0,
            currency="USD",
            customer_name=None,
            customer_phone=None,
            delivery_address=None,
            total=None,
            confidence=0.0,
        )


# Placeholder for actual LLM extraction
# This needs to be implemented with the actual LLM client


def extract_order(
    text: str,
    catalog_items: Optional[list] = None,
    validation_config: Optional[dict] = None,
) -> ExtractedOrder:
    """
    Extract order from text (wrapper function).
    
    Args:
        text: Transcribed text
        catalog_items: Catalog items for matching
        validation_config: Validation configuration
        
    Returns:
        ExtractedOrder object
    """
    extractor = OrderExtractor()
    return extractor.extract_from_text(text, catalog_items, validation_config)
