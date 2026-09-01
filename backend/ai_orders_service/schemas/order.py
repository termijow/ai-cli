"""Pydantic schemas for AI Orders."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict

# Order request schema (input to the service)
class OrderRequest(BaseModel):
    """Request schema for audio ingestion."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "audio_url": "https://example.com/audio.mp3",
                    "audio_filename": "whatsapp_message_12345.mp3",
                    "message_id": "WA_1234567890",
                    "validation_config": {
                        "min_items": 1,
                        "max_items": 10,
                        "allowed_currencies": ["USD", "EUR", "GBP"]
                    }
                }
            ]
        }
    )
    
    audio_url: Optional[str] = Field(
        ...,
        description="URL of the audio file from WhatsApp Web",
        example="https://example.com/audio.mp3"
    )
    audio_path: Optional[str] = Field(
        None,
        description="Local path to audio file (alternative to URL)"
    )
    message_id: Optional[str] = Field(
        None,
        description="WhatsApp message ID for tracking"
    )
    catalog_url: Optional[str] = Field(
        None,
        description="URL to the product catalog (for fuzzy matching)"
    )
    validation_config: Optional[dict] = Field(
        None,
        description="Validation configuration (min/max items, allowed currencies)"
    )


class ExtractedOrder(BaseModel):
    """Schema for extracted order information."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                "order_id": "ORD_20240115_001",
                "extracted_at": "2024-01-15T10:30:00Z",
                "items": [
                    {"name": "Pizza Margarita", "quantity": 2, "unit_price": 12.99, "confidence": 0.95},
                    {"name": "Coca Cola 500ml", "quantity": 2, "unit_price": 1.50, "confidence": 0.88},
                    {"name": "Cheesecake", "quantity": 1, "unit_price": 8.99, "confidence": 0.75}
                ],
                "subtotal": 39.47,
                "currency": "USD",
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "delivery_address": "123 Main St",
                "total": 52.45,
                "confidence": 0.82
            }
            ]
        }
    )
    
    order_id: str = Field(..., description="Generated order ID")
    extracted_at: datetime = Field(..., description="Extraction timestamp")
    items: list = Field(..., description="List of ordered items")
    subtotal: float = Field(..., description="Subtotal amount")
    currency: str = Field(..., description="Currency code (e.g., USD, EUR)")
    customer_name: Optional[str] = Field(None, description="Extracted customer name")
    customer_phone: Optional[str] = Field(None, description="Extracted customer phone")
    delivery_address: Optional[str] = Field(None, description="Extracted delivery address")
    total: Optional[float] = Field(None, description="Final total with tax/delivery")
    confidence: float = Field(0.0, description="Overall extraction confidence (0-1)")
    
    class Item(BaseModel):
        """Schema for a single order item."""
        name: str = Field(..., description="Item name")
        quantity: int = Field(..., description="Quantity")
        unit_price: float = Field(..., description="Unit price")
        confidence: float = Field(..., description="Item-level confidence")


class OrderValidationResult(BaseModel):
    """Schema for the validation result."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "order_id": "ORD_20240115_001",
                    "validated_at": "2024-01-15T10:30:00Z",
                    "items": [
                        {"name": "Pizza Margarita", "catalog_id": "PMG_001", "in_stock": True},
                        {"name": "Coca Cola 500ml", "catalog_id": "CCO_002", "in_stock": True},
                        {"name": "Cheesecake", "catalog_id": "CES_003", "in_stock": True}
                    ],
                    "messages": ["All items found in catalog", "Order validated successfully"],
                    "warnings": ["Cheesecake confidence is low (0.75)"],
                    "recommendations": ["Consider using more common terms for better accuracy"]
                }
            ]
        }
    )
    
    success: bool = Field(..., description="Whether the order was successfully validated")
    order_id: str = Field(..., description="The validated order ID")
    validated_at: datetime = Field(..., description="Validation timestamp")
    items: list = Field(..., description="List of matched items with catalog references")
    messages: list = Field([], description="Validation messages")
    warnings: list = Field([], description="Warnings about the order")
    recommendations: list = Field([], description="Recommendations for improvement")
