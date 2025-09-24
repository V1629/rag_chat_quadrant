import os
import time
import logging
from typing import List, Dict, Optional

import google.generativeai as genai
from config import settings
from pdf_processor import pdf_processor

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
    def create_rag_prompt(self, query: str, context_chunks: List[Dict], only_answer_if_sources: bool = False) -> str:
        """Create a RAG prompt with context and query"""
        
        if not context_chunks and only_answer_if_sources:
            return "I couldn't find any relevant information in the uploaded documents to answer your question. Please try rephrasing your question or upload relevant documents."
        
        context_text = ""
        if context_chunks:
            context_text = "\n\n".join([
                f"[Document: {chunk['filename']}, Page: {chunk['page_number']}]\n{chunk['content']}"
                for chunk in context_chunks
            ])
        
        prompt = f"""You are a helpful AI assistant that answers questions based on provided PDF document content. 

Your task is to:
1. Answer the user's question using ONLY the information provided in the context below
2. Be accurate and specific
3. Include citations in your response by referencing the document name and page number
4. If the context doesn't contain enough information to answer the question completely, say so clearly
5. Do not make up information that isn't in the provided context

Context from PDF documents:
{context_text}

User Question: {query}

Please provide a comprehensive answer based on the context above. Include specific citations (document name and page number) for each piece of information you reference."""

        return prompt

    def generate_response(self, query: str, context_chunks: List[Dict], only_answer_if_sources: bool = False) -> Dict:
        """Generate response using Gemini with RAG context"""
        start_time = time.time()
        
        try:
            prompt = self.create_rag_prompt(query, context_chunks, only_answer_if_sources)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Format sources
            sources = []
            for chunk in context_chunks:
                sources.append({
                    'document_id': chunk['document_id'],
                    'document_name': chunk['filename'],
                    'page_number': chunk['page_number'],
                    'chunk_index': chunk['chunk_index'],
                    'content': chunk['content'],
                    'relevance_score': chunk['score']
                })
            
            return {
                'response': response.text,
                'sources': sources,
                'context_chunks': context_chunks,
                'response_time_ms': response_time_ms,
                'tokens_used': len(response.text.split()) if response.text else 0  # Approximate token count
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': f"I encountered an error while generating the response: {str(e)}",
                'sources': [],
                'context_chunks': [],
                'response_time_ms': int((time.time() - start_time) * 1000),
                'tokens_used': 0
            }

    def answer_question(self, query: str, top_k: int = 5, document_filter: Optional[List[str]] = None, only_answer_if_sources: bool = False) -> Dict:
        """Complete RAG pipeline: retrieve context and generate answer"""
        try:
            # Retrieve relevant chunks
            context_chunks = pdf_processor.search_similar_chunks(
                query=query,
                top_k=top_k,
                document_filter=document_filter
            )
            
            # Generate response
            result = self.generate_response(query, context_chunks, only_answer_if_sources)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return {
                'response': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'context_chunks': [],
                'response_time_ms': 0,
                'tokens_used': 0
            }

# Global instance
rag_service = RAGService()
