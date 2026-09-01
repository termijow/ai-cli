"""LLM client for order extraction."""

import json
from typing import Any, Optional

try:
    from litellm import completion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


class LLMClient:
    """Client for LLM API calls."""
    
    def __init__(
        self,
        model: str = "google/gemma-2-9b-it",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        proxy_urls: Optional[list] = None,
    ):
        """
        Initialize the LLM client.
        
        Args:
            model: LLM model name
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            api_key: API key for the model
            base_url: Base URL for the API
            proxy_urls: List of proxy URLs
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.base_url = base_url
        self.proxy_urls = proxy_urls or []
    
    def extract_order(
        self,
        prompt: str,
        system_prompt: str = None,
    ) -> str:
        """
        Extract order from text using LLM.
        
        Args:
            prompt: User prompt with text to extract from
            system_prompt: Optional system prompt
            
        Returns:
            LLM response text
        """
        if not HAS_LITELLM:
            raise ImportError(
                "litellm is not installed. Install with: pip install litellm"
            )
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            base_url=self.base_url,
            proxy_urls=self.proxy_urls,
        )
        
        return response.choices[0].message.content
    
    def extract_order_json(
        self,
        prompt: str,
        system_prompt: str = None,
    ) -> dict:
        """
        Extract order from text using LLM and parse JSON response.
        
        Args:
            prompt: User prompt with text to extract from
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response
        """
        response_text = self.extract_order(prompt, system_prompt)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            import re
            pattern = r"\{.*\}"
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            raise ValueError(f"Failed to parse JSON from response: {response_text}") from e


def create_llm_client(
    model: str = "google/gemma-2-9b-it",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
) -> LLMClient:
    """
    Create and return an LLM client.
    
    Args:
        model: LLM model name
        temperature: Sampling temperature
        max_tokens: Maximum output tokens
        api_key: API key for the model
        
    Returns:
        Configured LLMClient instance
    """
    return LLMClient(model, temperature, max_tokens, api_key)
