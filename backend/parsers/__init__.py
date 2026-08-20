"""
Document parser module for the backend server.
Handles parsing of PDF, DOCX, Markdown, and Text files.
"""

from backend.document_parser import DocumentParser, ParseResult

# Create singleton instance
parser = DocumentParser()
