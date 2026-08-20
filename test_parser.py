#!/usr/bin/env python3
"""Test script for DocumentParser"""

from backend.document_parser import DocumentParser

parser = DocumentParser()

# Test with a text file
test_content = """# Hello World

This is a test document.
It contains multiple paragraphs.
"""

# Test parsing text content
result = parser.parse("test_content", document_type="text")
print(f"Text parse result:")
print(f"  Success: {result.success}")
if result.content:
    print(f"  Content preview: {result.content[:100]}")
if result.error:
    print(f"  Error: {result.error}")

# Test with a sample markdown file
md_content = """## Test Markdown

- Item 1
- Item 2
- Item 3
"""

result = parser.parse("test_md", document_type="md")
print(f"\nMarkdown parse result:")
print(f"  Success: {result.success}")
if result.content:
    print(f"  Content preview: {result.content[:100]}")
if result.error:
    print(f"  Error: {result.error}")

# Test with file path that doesn't exist
result = parser.parse("nonexistent_file.txt", document_type="text")
print(f"\nNonexistent file parse result:")
print(f"  Success: {result.success}")
if result.error:
    print(f"  Error: {result.error}")

# Test unsupported document type
result = parser.parse("test.txt", document_type="pptx")
print(f"\nUnsupported type parse result:")
print(f"  Success: {result.success}")
if result.error:
    print(f"  Error: {result.error}")

print("\nAll tests completed!")
