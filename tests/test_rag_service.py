import pytest
from unittest.mock import Mock, patch
from backend.rag_service import RAGService

class TestRAGService:
    @patch('backend.rag_service.genai')
    def setup_method(self, mock_genai):
        """Setup test fixtures"""
        # Mock Gemini setup
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            self.service = RAGService()
    
    def test_create_rag_prompt_with_context(self):
        """Test RAG prompt creation with context chunks"""
        query = "What is the main topic?"
        context_chunks = [
            {
                'filename': 'doc1.pdf',
                'page_number': 1,
                'content': 'This document discusses artificial intelligence.'
            },
            {
                'filename': 'doc2.pdf',
                'page_number': 2,
                'content': 'Machine learning is a subset of AI.'
            }
        ]
        
        prompt = self.service.create_rag_prompt(query, context_chunks)
        
        assert query in prompt
        assert 'doc1.pdf' in prompt
        assert 'Page: 1' in prompt
        assert 'artificial intelligence' in prompt
        assert 'Machine learning' in prompt
    
    def test_create_rag_prompt_no_sources_strict_mode(self):
        """Test RAG prompt when no sources found in strict mode"""
        query = "What is the main topic?"
        context_chunks = []
        
        prompt = self.service.create_rag_prompt(query, context_chunks, only_answer_if_sources=True)
        
        assert "couldn't find any relevant information" in prompt
    
    def test_create_rag_prompt_no_sources_normal_mode(self):
        """Test RAG prompt when no sources found in normal mode"""
        query = "What is the main topic?"
        context_chunks = []
        
        prompt = self.service.create_rag_prompt(query, context_chunks, only_answer_if_sources=False)
        
        assert query in prompt
        assert "Context from PDF documents:" in prompt
    
    @patch('backend.rag_service.pdf_processor')
    def test_answer_question_success(self, mock_processor):
        """Test successful question answering"""
        # Mock PDF processor response
        mock_chunks = [
            {
                'document_id': '123',
                'filename': 'test.pdf',
                'page_number': 1,
                'chunk_index': 0,
                'content': 'Test content',
                'score': 0.9
            }
        ]
        mock_processor.search_similar_chunks.return_value = mock_chunks
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "This is the answer based on the context."
        self.service.model.generate_content.return_value = mock_response
        
        result = self.service.answer_question("What is this about?")
        
        assert 'response' in result
        assert 'sources' in result
        assert 'context_chunks' in result
        assert 'response_time_ms' in result
        assert result['response'] == "This is the answer based on the context."
        assert len(result['sources']) == 1
    
    @patch('backend.rag_service.pdf_processor')
    def test_answer_question_with_filters(self, mock_processor):
        """Test question answering with document filters"""
        mock_processor.search_similar_chunks.return_value = []
        
        mock_response = Mock()
        mock_response.text = "No relevant information found."
        self.service.model.generate_content.return_value = mock_response
        
        result = self.service.answer_question(
            "Test query",
            top_k=3,
            document_filter=['doc1', 'doc2'],
            only_answer_if_sources=True
        )
        
        # Verify processor was called with correct parameters
        mock_processor.search_similar_chunks.assert_called_once_with(
            query="Test query",
            top_k=3,
            document_filter=['doc1', 'doc2']
        )
        
        assert 'response' in result
