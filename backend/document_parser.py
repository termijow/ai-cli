#!/usr/bin/env python3
"""
document_parser.py - Document parsing utilities
Supports PDF, Word (DOCX), and Markdown file parsing
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("WARNING: pdfplumber not installed. Install with: pip install pdfplumber")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("WARNING: python-docx not installed. Install with: pip install python-docx")

try:
    import markdown
    MARKDOWN_SUPPORT = True
except ImportError:
    MARKDOWN_SUPPORT = False
    print("WARNING: markdown library not installed. Install with: pip install markdown")


@dataclass
class ParseResult:
    """Result of parsing a document."""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentParser:
    """Document parser supporting multiple formats."""
    
    def __init__(self):
        self.supported_formats = {
            "pdf": "PDF",
            "docx": "Word (DOCX)",
            "md": "Markdown",
            "txt": "Text",
        }
    
    def parse(self, file_path: str, document_type: str = "text") -> ParseResult:
        """
        Parse a document of the specified type.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (pdf, docx, md, text)
        
        Returns:
            ParseResult with content and metadata
        """
        full_path = Path(file_path)
        
        if not full_path.exists():
            return ParseResult(
                success=False,
                content="",
                error=f"File not found: {file_path}"
            )
        
        if document_type not in self.supported_formats:
            return ParseResult(
                success=False,
                content="",
                error=f"Unsupported document type: {document_type}"
            )
        
        try:
            if document_type == "pdf" and PDF_SUPPORT:
                content = self.parse_pdf(file_path)
            elif document_type == "docx" and DOCX_SUPPORT:
                content = self.parse_docx(file_path)
            elif document_type == "md" and MARKDOWN_SUPPORT:
                content = self.parse_markdown(file_path)
            elif document_type == "text":
                content = self.parse_text(file_path)
            else:
                return ParseResult(
                    success=False,
                    content="",
                    error=f"Parser not implemented for type: {document_type}"
                )
            
            # Extract metadata if available
            metadata = self.extract_metadata(file_path, document_type)
            
            return ParseResult(success=True, content=content, metadata=metadata)
        
        except Exception as e:
            return ParseResult(
                success=False,
                content="",
                error=f"Error parsing document: {str(e)}"
            )
    
    def parse_pdf(self, file_path: str) -> str:
        """Parse a PDF file and return text content."""
        if not PDF_SUPPORT:
            raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")
        
        full_path = Path(file_path)
        content_parts = []
        
        with pdfplumber.open(full_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text from page
                text = page.extract_text()
                if text:
                    content_parts.append(f"--- Page {page_num} ---\n{text}")
        
        return "\n\n".join(content_parts)
    
    def parse_docx(self, file_path: str) -> str:
        """Parse a DOCX file and return text content."""
        if not DOCX_SUPPORT:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
        
        full_path = Path(file_path)
        doc = docx.Document(full_path)
        
        content_parts = []
        for para in doc.paragraphs:
            content_parts.append(para.text)
        
        return "\n\n".join(content_parts)
    
    def parse_markdown(self, file_path: str) -> str:
        """Parse a Markdown file and return formatted content."""
        if not MARKDOWN_SUPPORT:
            raise ImportError("markdown library not installed. Install with: pip install markdown")
        
        full_path = Path(file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Parse markdown to HTML-like structure
        try:
            html = markdown.markdown(raw_content, extensions=['extra', 'codehilite'])
            # Convert HTML-like structure to text with markers
            result = []
            for line in html.split('\n'):
                if line.startswith('<h') and 'class="">' in line:
                    # Heading
                    if 'level=1' in line:
                        result.append("### " + line.replace('<h', '### ').replace('>', ''))
                    elif 'level=2' in line:
                        result.append("## " + line.replace('<h', '## ').replace('>', ''))
                    elif 'level=3' in line:
                        result.append("### " + line.replace('<h', '### ').replace('>', ''))
                elif line.startswith('<p') and 'class="">' in line:
                    # Paragraph
                    result.append(line.replace('<p', ' ').replace('>', ''))
                else:
                    result.append(line)
            
            return "\n".join(result)
        except Exception as e:
            return raw_content
    
    def parse_text(self, file_path: str) -> str:
        """Parse a plain text file."""
        full_path = Path(file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_metadata(self, file_path: str, document_type: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from a document."""
        metadata = {}
        full_path = Path(file_path)
        
        try:
            # Basic file metadata
            stat = full_path.stat()
            metadata.update({
                "name": full_path.name,
                "size_bytes": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "type": document_type,
            })
        except Exception:
            pass
        
        # Type-specific metadata
        if document_type == "pdf" and PDF_SUPPORT:
            try:
                with pdfplumber.open(full_path) as pdf:
                    metadata.update({
                        "num_pages": len(pdf.pages),
                        "title": pdf.metadata.get('Title', ''),
                        "author": pdf.metadata.get('Author', ''),
                        "creator": pdf.metadata.get('Creator', ''),
                        "producer": pdf.metadata.get('Producer', ''),
                        "subject": pdf.metadata.get('Subject', ''),
                    })
            except Exception:
                pass
        
        elif document_type == "docx" and DOCX_SUPPORT:
            try:
                doc = docx.Document(full_path)
                metadata.update({
                    "title": doc.core_properties.title,
                    "author": doc.core_properties.author,
                    "subject": doc.core_properties.subject,
                    "created": doc.core_properties.created,
                    "modified": doc.core_properties.modified,
                    "pages": len(doc.paragraphs),
                })
            except Exception:
                pass
        
        elif document_type == "md":
            try:
                with open(full_path, 'r') as f:
                    raw = f.read()
                # Count headings
                metadata["heading_count"] = raw.count('#')
                metadata["line_count"] = len(raw.split('\n'))
            except Exception:
                pass
        
        return metadata if metadata else None


# Singleton instance
parser = DocumentParser()
