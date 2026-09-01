"""Prompt templates for order extraction."""

from typing import Optional


def generate_extraction_prompt(
    text: str,
    catalog_items: Optional[list] = None,
    validation_config: Optional[dict] = None,
) -> str:
    """
    Generate a prompt for order extraction from transcribed text.
    
    Args:
        text: Transcribed text from audio
        catalog_items: Available catalog items for reference
        validation_config: Validation configuration
        
    Returns:
        Prompt string for LLM
    """
    catalog_context = ""
    if catalog_items:
        catalog_context = "Available menu items:\n"
        for item in catalog_items:
            catalog_context += f"  - {item.get('name', 'Item')}\n"
    
    validation_rules = ""
    if validation_config:
        validation_rules = f"Validation rules:\n  - Minimum {validation_config.get('min_items', 1)} items\n  - Maximum {validation_config.get('max_items', 10)} items\n  - Allowed currencies: {', '.join(validation_config.get('allowed_currencies', []))}"
    
    prompt = f"""You are an order extraction assistant. Extract order information from the following WhatsApp customer message.

Customer message:
{text}

{catalog_context}

{validation_rules}

Extract the following fields:
1. order_id: Generate a unique order ID (format: ORD_YYYYMMDD_XXX)
2. customer_name: Extracted customer name (if present)
3. customer_phone: Extracted customer phone (if present)
4. delivery_address: Extracted delivery address (if present)
5. items: List of ordered items with:
   - name: Product name from catalog
   - quantity: Quantity ordered
   - unit_price: Unit price from catalog
   - confidence: Confidence score (0-1)
6. subtotal: Sum of item prices
7. currency: Currency code (USD, EUR, GBP, etc.)
8. total: Subtotal + any taxes/delivery fees
9. confidence: Overall confidence score (0-1)

Return ONLY valid JSON in this exact format:
{{
    "order_id": "string",
    "customer_name": "string or null",
    "customer_phone": "string or null",
    "delivery_address": "string or null",
    "items": [
        {{
            "name": "string",
            "quantity": number,
            "unit_price": number,
            "confidence": number
        }},
        ...
    ],
    "subtotal": number,
    "currency": "string",
    "total": number,
    "confidence": number
}}

If the message is unclear or doesn't contain order information, return an error object:
{{
    "error": "string describing the issue",
    "confidence": 0
}}

IMPORTANT: Use catalog items for item names when possible. If an item isn't in the catalog, mark it with lower confidence.
"""
    
    return prompt


def generate_validation_prompt(extracted_order: dict) -> str:
    """
    Generate a prompt for validating an extracted order.
    
    Args:
        extracted_order: The extracted order information
        
    Returns:
        Validation prompt string
    """
    return f"""Validate the following extracted order:

Order:
{json.dumps(extracted_order, indent=2)}

Check for:
1. Valid order ID format
2. Items have required fields (name, quantity, unit_price)
3. Prices are positive numbers
4. Subtotal matches sum of item prices
5. Currency is a valid code

Return validation result in JSON format.
"""
