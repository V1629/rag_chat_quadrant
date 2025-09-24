import os
import hashlib
import asyncio
import uuid
from typing import List, Dict, Optional
from pathlib import Path
import logging

# PDF processing
import pypdf
from sentence_transformers import SentenceTransformer

# Vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Database
from sqlalchemy.orm import Session
from models import Document, DocumentChunk, get_db
from config import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize Qdrant client with or without API key
        if settings.QDRANT_API_KEY:
            # Use Qdrant Cloud with API key
            self.qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
            logger.info("Connected to Qdrant Cloud with API key")
        else:
            # Use local Qdrant instance
            self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
            logger.info("Connected to local Qdrant instance")
        
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the Qdrant collection exists"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, any]]:
        """Extract text from PDF file, returning list of page content"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                pages = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():  # Only include pages with text
                        pages.append({
                            'page_number': page_num + 1,
                            'content': text.strip()
                        })
                
                return pages
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks"""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings
                for punct in ['. ', '! ', '? ']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < len(text) else len(text)
            
            if start >= len(text):
                break
        
        return chunks

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise

    async def process_pdf(self, file_path: str, document_id: str, db: Session) -> bool:
        """Process a PDF file: extract text, chunk, embed, and store in vector DB"""
        try:
            # Update document status
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            document.processing_status = 'processing'
            db.commit()
            
            # Extract text from PDF
            pages = self.extract_text_from_pdf(file_path)
            document.page_count = len(pages)
            
            # Process each page
            all_chunks = []
            chunk_metadata = []
            
            for page in pages:
                page_chunks = self.chunk_text(page['content'])
                
                for chunk_idx, chunk in enumerate(page_chunks):
                    # Generate a proper UUID for Qdrant point ID
                    chunk_uuid = str(uuid.uuid4())
                    
                    # Create a readable chunk identifier for database storage
                    chunk_id = f"{document_id}_{page['page_number']}_{chunk_idx}"
                    
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        'chunk_uuid': chunk_uuid,  # UUID for Qdrant
                        'chunk_id': chunk_id,      # Readable ID for database
                        'document_id': document_id,
                        'page_number': page['page_number'],
                        'chunk_index': len(all_chunks) - 1,
                        'content': chunk
                    })
            
            # Create embeddings
            embeddings = self.create_embeddings(all_chunks)
            
            # Store in Qdrant
            points = []
            for i, (metadata, embedding) in enumerate(zip(chunk_metadata, embeddings)):
                point = PointStruct(
                    id=metadata['chunk_uuid'],  # Use UUID for Qdrant
                    vector=embedding,
                    payload={
                        'document_id': document_id,
                        'page_number': metadata['page_number'],
                        'chunk_index': metadata['chunk_index'],
                        'content': metadata['content'],
                        'filename': document.filename,
                        'chunk_id': metadata['chunk_id']  # Keep readable ID in payload
                    }
                )
                points.append(point)
            
            # Batch upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=points
            )
            
            # Store chunk metadata in PostgreSQL
            for metadata in chunk_metadata:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=metadata['chunk_index'],
                    page_number=metadata['page_number'],
                    content_preview=metadata['content'][:200] + "..." if len(metadata['content']) > 200 else metadata['content'],
                    vector_id=metadata['chunk_uuid']  # Use UUID to match Qdrant point ID
                )
                db.add(chunk)
            
            # Update document status
            document.processing_status = 'completed'
            document.chunk_count = len(all_chunks)
            db.commit()
            
            logger.info(f"Successfully processed document {document_id}: {len(all_chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            # Update document status to failed
            document.processing_status = 'failed'
            document.error_message = str(e)
            db.commit()
            return False

    def search_similar_chunks(self, query: str, top_k: int = 5, document_filter: Optional[List[str]] = None) -> List[Dict]:
        """Search for similar chunks in the vector database"""
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Prepare filter
            search_filter = None
            if document_filter:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=doc_id)
                        ) for doc_id in document_filter
                    ]
                )
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    'id': hit.id,
                    'score': hit.score,
                    'document_id': hit.payload['document_id'],
                    'page_number': hit.payload['page_number'],
                    'chunk_index': hit.payload['chunk_index'],
                    'content': hit.payload['content'],
                    'filename': hit.payload['filename']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            raise

    def get_document_stats(self) -> Dict:
        """Get statistics about processed documents"""
        try:
            # Try a simpler approach first - just count points using scroll
            try:
                scroll_result = self.qdrant_client.scroll(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                # If scroll works, the collection exists and connection is good
                # For large collections, we'll get an approximate count
                points_count = 0
                if scroll_result and len(scroll_result[0]) > 0:
                    # Try to get a more accurate count with a larger scroll
                    try:
                        count_result = self.qdrant_client.count(
                            collection_name=settings.QDRANT_COLLECTION_NAME,
                            exact=False  # Use approximate count for performance
                        )
                        if hasattr(count_result, 'count'):
                            points_count = count_result.count
                        else:
                            points_count = count_result  # In case it returns just the number
                    except:
                        # Fallback: estimate by scrolling
                        points_count = 0
                
                return {
                    'total_chunks': points_count,
                    'vector_dimension': 384  # Known dimension for all-MiniLM-L6-v2
                }
                
            except Exception as scroll_error:
                # If scroll fails, try the original method with better error handling
                collection_info = self.qdrant_client.get_collection(settings.QDRANT_COLLECTION_NAME)
                
                # Extract points count safely
                points_count = 0
                vector_dimension = 384
                
                if hasattr(collection_info, 'points_count'):
                    points_count = collection_info.points_count
                elif hasattr(collection_info, 'result') and hasattr(collection_info.result, 'points_count'):
                    points_count = collection_info.result.points_count
                    
                return {
                    'total_chunks': points_count,
                    'vector_dimension': vector_dimension
                }
                
        except Exception as e:
            # Log as warning instead of error since this is just stats gathering
            logger.warning(f"Could not get collection stats from Qdrant Cloud (connection works, stats unavailable): {e}")
            # Return minimal stats - the connection works, just stats parsing failed
            return {'total_chunks': 0, 'vector_dimension': 384}

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Global instance
pdf_processor = PDFProcessor()
