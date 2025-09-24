import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from backend.pdf_processor import PDFProcessor, calculate_file_hash

class TestPDFProcessor:
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = PDFProcessor()
    
    def test_calculate_file_hash(self):
        """Test file hash calculation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = calculate_file_hash(temp_path)
            hash2 = calculate_file_hash(temp_path)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)
    
    def test_chunk_text(self):
        """Test text chunking functionality"""
        text = "This is a test. This is another sentence. And here's a third one."
        chunks = self.processor.chunk_text(text, chunk_size=30, overlap=10)
        
        assert len(chunks) > 0
        assert all(len(chunk) <= 40 for chunk in chunks)  # Allow some flexibility
    
    def test_chunk_text_short(self):
        """Test chunking with text shorter than chunk size"""
        text = "Short text"
        chunks = self.processor.chunk_text(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    @patch('backend.pdf_processor.SentenceTransformer')
    def test_create_embeddings(self, mock_transformer):
        """Test embedding creation"""
        # Mock the sentence transformer
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_transformer.return_value = mock_model
        
        processor = PDFProcessor()
        texts = ["Hello world", "Another text"]
        embeddings = processor.create_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3
        mock_model.encode.assert_called_once_with(texts, convert_to_tensor=False)

class TestFileUtils:
    def test_file_hash_different_files(self):
        """Test that different files produce different hashes"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("content1")
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("content2")
            path2 = f2.name
        
        try:
            hash1 = calculate_file_hash(path1)
            hash2 = calculate_file_hash(path2)
            assert hash1 != hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)
