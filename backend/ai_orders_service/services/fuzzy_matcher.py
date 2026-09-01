"""Fuzzy matching service for product catalog using embeddings."""

import json
from typing import Optional
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel


class FuzzyMatcher:
    """Service for fuzzy matching extracted items with product catalog using embeddings."""
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        similarity_threshold: float = 0.75,
        top_k_matches: int = 5,
    ):
        """
        Initialize the fuzzy matcher.
        
        Args:
            embedding_model: Sentence transformer model name
            similarity_threshold: Minimum similarity threshold for matches
            top_k_matches: Number of top matches to return
        """
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        self.top_k_matches = top_k_matches
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
    def compute_embedding(self, text: str) -> list:
        """
        Compute embedding for a text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        return self.embedding_model.encode(text).tolist()
    
    def match_item(
        self,
        extracted_item_name: str,
        catalog_items: list,
        catalog_embeddings: dict,
    ) -> Optional[list]:
        """
        Match an extracted item with catalog items.
        
        Args:
            extracted_item_name: Name of the extracted item
            catalog_items: List of catalog items with names
            catalog_embeddings: Dictionary of catalog item names to embeddings
            
        Returns:
            List of matched items with similarity scores
        """
        # Compute embedding for extracted item
        extracted_embedding = self.compute_embedding(extracted_item_name)
        
        # Compute similarities
        similarities = self.embedding_model.similarity(extracted_embedding, catalog_embeddings)
        
        # Get top matches
        top_indices = torch.topk(similarities, k=self.top_k_matches).indices.tolist()
        
        matches = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= self.similarity_threshold:
                matches.append({
                    "name": catalog_items[idx]["name"],
                    "similarity": similarity,
                    "catalog_id": catalog_items[idx].get("catalog_id"),
                    "in_stock": catalog_items[idx].get("in_stock", True),
                })
        
        return matches if matches else None
    
    def match_items(
        self,
        extracted_items: list,
        catalog_items: list,
    ) -> list:
        """
        Match multiple extracted items with catalog.
        
        Args:
            extracted_items: List of extracted items
            catalog_items: List of catalog items with embeddings
            
        Returns:
            List of matched items with scores
        """
        matched_items = []
        
        for extracted in extracted_items:
            name = extracted["name"]
            matches = self.match_item(
                name,
                catalog_items,
                {item["name"]: item for item in catalog_items}
            )
            
            matched_items.append({
                "original_name": name,
                "extracted_name": name,
                "matches": matches,
                "confidence": matches[0]["similarity"] if matches else 0.0,
            })
        
        return matched_items
    
    async def fetch_catalog_embeddings(self, catalog_url: str) -> dict:
        """
        Fetch product catalog and compute embeddings.
        
        Args:
            catalog_url: URL to the catalog
            
        Returns:
            Dictionary of item names to embeddings
        """
        # This would be implemented based on your actual catalog format
        # For now, return empty dict
        return {}


def init_fuzzy_matcher(
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    similarity_threshold: float = 0.75,
    top_k_matches: int = 5,
) -> FuzzyMatcher:
    """
    Initialize and return a fuzzy matcher.
    
    Args:
        embedding_model: Sentence transformer model
        similarity_threshold: Threshold for matches
        top_k_matches: Number of top matches
        
    Returns:
        Configured FuzzyMatcher instance
    """
    return FuzzyMatcher(embedding_model, similarity_threshold, top_k_matches)
