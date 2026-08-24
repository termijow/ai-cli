#!/usr/bin/env python3
"""Comprehensive Unit Tests for DocumentParser and WhatsAppParser"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from backend.document_parser import DocumentParser, parser
from backend.whatsapp_parser import WhatsAppParser, whatsapp_parser


class TestDocumentParser(unittest.TestCase):
    def setUp(self):
        self.parser = DocumentParser()

    def test_parse_text_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hola Mundo!\nEsta es una prueba de texto.")
            temp_path = f.name

        try:
            res = self.parser.parse(temp_path, document_type="text")
            self.assertTrue(res.success)
            self.assertIn("Hola Mundo!", res.content)
            self.assertEqual(res.metadata.get("type"), "text")
            self.assertGreater(res.metadata.get("word_count", 0), 0)
        finally:
            os.unlink(temp_path)

    def test_parse_markdown_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Titulo Principal\n\n## Subtitulo\n\n- Elemento 1\n- Elemento 2\n")
            temp_path = f.name

        try:
            res = self.parser.parse(temp_path, document_type="md")
            self.assertTrue(res.success)
            self.assertIn("Titulo Principal", res.content)
            self.assertEqual(res.metadata.get("type"), "markdown")
            self.assertEqual(res.metadata.get("heading_count"), 2)
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        res = self.parser.parse("/nonexistent_file_path_12345.txt", document_type="text")
        self.assertFalse(res.success)
        self.assertIn("File not found", res.error)

    def test_parse_content_in_memory(self):
        res = self.parser.parse_content("Documento en memoria de prueba", document_type="text")
        self.assertTrue(res.success)
        self.assertEqual(res.content, "Documento en memoria de prueba")
        self.assertEqual(res.metadata["word_count"], 5)


class TestWhatsAppParser(unittest.TestCase):
    def setUp(self):
        self.parser = WhatsAppParser()

    def test_parse_android_chat(self):
        chat_text = """15/01/24, 10:30 - Juan: Hola Carlos, ¿cómo estás?
15/01/24, 10:31 - Carlos: Todo bien Juan! Mi cumpleaños es el 25 de mayo, ¿nos vemos en la oficina?
15/01/24, 10:32 - Juan: Claro que sí, en Calle 10 #45.
15/01/24, 10:33 - Carlos: Perfecto, llevo el pastel.
"""
        parsed = self.parser.parse_text(chat_text)
        self.assertEqual(parsed["total_messages"], 4)
        self.assertEqual(len(parsed["participants"]), 2)
        names = [p["name"] for p in parsed["participants"]]
        self.assertIn("Juan", names)
        self.assertIn("Carlos", names)

    def test_parse_ios_chat(self):
        chat_text = """[15/01/24, 10:30:15] María: Hola a todos
[15/01/24, 10:31:00] Pedro: Hola María!
"""
        parsed = self.parser.parse_text(chat_text)
        self.assertEqual(parsed["total_messages"], 2)
        self.assertEqual(len(parsed["participants"]), 2)

    def test_build_analysis_prompt(self):
        chat_text = """15/01/24, 10:30 - Juan: Hola
15/01/24, 10:31 - Carlos: Hola
"""
        parsed = self.parser.parse_text(chat_text)
        prompt = self.parser.build_analysis_prompt(parsed)
        self.assertIn("JSON", prompt)
        self.assertIn("Juan", prompt)
        self.assertIn("Carlos", prompt)


if __name__ == "__main__":
    unittest.main()
