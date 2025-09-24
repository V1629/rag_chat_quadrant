import streamlit as st
import requests
import uuid
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import plotly.express as px
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class RAGChatApp:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="PDF RAG Chat",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main {
            padding-top: 1rem;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #1f77b4;
            color: #000000 !important;  /* Force black text */
        }
        .user-message {
            background-color: #f0f8ff;
            border-left-color: #1f77b4;
            color: #000000 !important;  /* Force black text */
        }
        .assistant-message {
            background-color: #f8f9fa;
            border-left-color: #28a745;
            color: #000000 !important;  /* Force black text */
        }
        .source-citation {
            background-color: #fff3cd;
            padding: 0.5rem;
            border-radius: 0.25rem;
            margin: 0.25rem 0;
            font-size: 0.85em;
            color: #000000 !important;  /* Force black text */
        }
        .context-chunk {
            background-color: #e9ecef;
            padding: 0.75rem;
            border-radius: 0.25rem;
            margin: 0.5rem 0;
            border-left: 3px solid #6c757d;
            color: #000000 !important;  /* Force black text */
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'user_session_id' not in st.session_state:
            st.session_state.user_session_id = str(uuid.uuid4())
        
        if 'current_chat_session' not in st.session_state:
            st.session_state.current_chat_session = None
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'documents' not in st.session_state:
            st.session_state.documents = []
        
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = []
        
        # Settings
        if 'top_k' not in st.session_state:
            st.session_state.top_k = 5
        
        if 'document_filter' not in st.session_state:
            st.session_state.document_filter = []
        
        if 'model_selector' not in st.session_state:
            st.session_state.model_selector = "gemini-pro"
        
        if 'only_answer_if_sources' not in st.session_state:
            st.session_state.only_answer_if_sources = False
    
    def create_user(self):
        """Create or get user"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/users",
                params={"session_id": st.session_state.user_session_id}
            )
            if response.status_code == 200:
                user_data = response.json()
                # Store user information in session state
                st.session_state.user_id = user_data.get("user_id")
                return user_data
            return None
        except Exception as e:
            st.error(f"Error creating user: {e}")
            return None
    
    def create_chat_session(self, session_name: str = None):
        """Create a new chat session with auto-naming if needed"""
        try:
            # Auto-generate name if not provided
            if not session_name:
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                session_name = f"Chat {timestamp}"
            
            response = requests.post(
                f"{self.backend_url}/api/sessions",
                params={"session_id": st.session_state.user_session_id},
                json={"session_name": session_name}
            )
            if response.status_code == 200:
                session_data = response.json()
                st.session_state.current_chat_session = session_data["id"]
                
                # Load the updated sessions list
                self.load_chat_sessions()
                
                # Clear any existing chat history for the new session
                st.session_state.chat_history = []
                
                st.success(f"✨ Created new thread: **{session_data.get('session_name', session_name)}**")
                return session_data
            else:
                st.error(f"❌ Failed to create chat thread: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error creating chat thread: {e}")
            return None
        return None
    
    def load_chat_sessions(self):
        """Load all chat sessions and auto-select the most recent if none selected"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/sessions",
                params={"session_id": st.session_state.user_session_id}
            )
            if response.status_code == 200:
                sessions = response.json()
                st.session_state.chat_sessions = sessions
                
                # Auto-select the most recent session if none is currently selected
                if sessions and not st.session_state.current_chat_session:
                    # Sort by updated_at or created_at to get the most recent
                    sorted_sessions = sorted(
                        sessions, 
                        key=lambda x: x.get('updated_at', x.get('created_at', '')), 
                        reverse=True
                    )
                    most_recent = sorted_sessions[0]
                    st.session_state.current_chat_session = most_recent['id']
                    self.load_chat_history(most_recent['id'])
                    st.success(f"🔄 Loaded recent thread: {most_recent.get('session_name', 'Untitled')}")
                
                if sessions:
                    st.success(f"📂 Loaded {len(sessions)} chat thread(s)")
                else:
                    st.info("📝 No previous chat threads found. Create your first thread!")
            else:
                st.warning(f"Could not load chat sessions: {response.status_code}")
                st.session_state.chat_sessions = []
        except Exception as e:
            st.error(f"Error loading chat sessions: {e}")
            st.session_state.chat_sessions = []
    
    def load_chat_history(self, session_id: str):
        """Load chat history for a session"""
        try:
            response = requests.get(f"{self.backend_url}/api/sessions/{session_id}/messages")
            if response.status_code == 200:
                st.session_state.chat_history = response.json()
            else:
                st.session_state.chat_history = []
        except Exception as e:
            st.error(f"Error loading chat history: {e}")
            st.session_state.chat_history = []
    
    def delete_chat_session(self, session_id: str):
        """Delete a chat session"""
        try:
            response = requests.delete(f"{self.backend_url}/api/sessions/{session_id}")
            if response.status_code == 200:
                self.load_chat_sessions()
                if st.session_state.current_chat_session == session_id:
                    st.session_state.current_chat_session = None
                    st.session_state.chat_history = []
                return True
        except Exception as e:
            st.error(f"Error deleting chat session: {e}")
        return False
    
    def upload_document(self, uploaded_file):
        """Upload a document"""
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(f"{self.backend_url}/api/documents/upload", files=files)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"Error uploading document: {e}")
            return None
    
    def load_documents(self):
        """Load all documents"""
        try:
            response = requests.get(f"{self.backend_url}/api/documents")
            if response.status_code == 200:
                st.session_state.documents = response.json()
        except Exception as e:
            st.error(f"Error loading documents: {e}")
    
    def delete_document(self, document_id: str):
        """Delete a document"""
        try:
            response = requests.delete(f"{self.backend_url}/api/documents/{document_id}")
            if response.status_code == 200:
                self.load_documents()
                return True
        except Exception as e:
            st.error(f"Error deleting document: {e}")
        return False
    
    def send_message(self, message: str):
        """Send a chat message"""
        if not st.session_state.current_chat_session:
            st.error("Please create or select a chat session first")
            return None
        
        try:
            payload = {
                "message": message,
                "session_id": st.session_state.current_chat_session,
                "top_k": st.session_state.top_k,
                "document_filter": st.session_state.document_filter if st.session_state.document_filter else None,
                "only_answer_if_sources": st.session_state.only_answer_if_sources
            }
            
            response = requests.post(f"{self.backend_url}/api/chat", json=payload)
            if response.status_code == 200:
                self.load_chat_history(st.session_state.current_chat_session)
                return response.json()
        except Exception as e:
            st.error(f"Error sending message: {e}")
        return None
    
    def get_stats(self):
        """Get system statistics"""
        try:
            response = requests.get(f"{self.backend_url}/api/stats")
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    def render_sidebar(self):
        """Render the sidebar with enhanced chat thread management"""
        with st.sidebar:
            st.title("📚 PDF RAG Chat")
            
            # Chat Thread Management
            st.header("💬 Chat Threads")
            
            # Create new thread
            with st.expander("➕ New Chat Thread", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    new_thread_name = st.text_input(
                        "Thread name", 
                        placeholder="e.g., Document Analysis, Q&A Session...",
                        key="new_thread_name"
                    )
                with col2:
                    st.write("")  # Spacing
                    if st.button("Create", key="create_thread_btn"):
                        if new_thread_name:
                            new_session = self.create_chat_session(new_thread_name)
                            if new_session:
                                st.success(f"Created: {new_thread_name}")
                                st.rerun()
                        else:
                            # Create with auto-generated name
                            timestamp = datetime.now().strftime("%m/%d %H:%M")
                            auto_name = f"Chat {timestamp}"
                            new_session = self.create_chat_session(auto_name)
                            if new_session:
                                st.success(f"Created: {auto_name}")
                                st.rerun()
            
            # Display existing threads
            if st.session_state.chat_sessions:
                st.subheader("Recent Threads")
                
                # Sort sessions by last activity (most recent first)
                sorted_sessions = sorted(
                    st.session_state.chat_sessions, 
                    key=lambda x: x.get('updated_at', x.get('created_at', '')), 
                    reverse=True
                )
                
                for i, session in enumerate(sorted_sessions):
                    session_id = session['id']
                    session_name = session.get('session_name', 'Untitled')
                    message_count = session.get('message_count', 0)
                    created_at = session.get('created_at', '')
                    
                    # Format creation date
                    try:
                        if created_at:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            date_str = dt.strftime("%m/%d %H:%M")
                        else:
                            date_str = "Unknown"
                    except:
                        date_str = "Unknown"
                    
                    # Current thread indicator
                    is_current = (session_id == st.session_state.current_chat_session)
                    thread_prefix = "🟢 " if is_current else "⚪ "
                    
                    with st.container():
                        col1, col2, col3 = st.columns([6, 2, 1])
                        
                        with col1:
                            # Thread selector button
                            if st.button(
                                f"{thread_prefix}{session_name}",
                                key=f"select_thread_{session_id}",
                                help=f"Messages: {message_count} | Created: {date_str}",
                                use_container_width=True
                            ):
                                if not is_current:
                                    st.session_state.current_chat_session = session_id
                                    self.load_chat_history(session_id)
                                    st.rerun()
                        
                        with col2:
                            # Message count
                            st.caption(f"{message_count} msgs")
                        
                        with col3:
                            # Delete button
                            if st.button(
                                "🗑️", 
                                key=f"delete_thread_{session_id}",
                                help="Delete thread"
                            ):
                                if st.session_state.get('confirm_delete_thread') == session_id:
                                    if self.delete_chat_session(session_id):
                                        st.success("Thread deleted!")
                                        st.session_state.pop('confirm_delete_thread', None)
                                        st.rerun()
                                else:
                                    st.session_state.confirm_delete_thread = session_id
                                    st.warning("Click delete again to confirm")
                        
                        # Show confirmation warning
                        if st.session_state.get('confirm_delete_thread') == session_id:
                            st.warning("⚠️ Click delete again to confirm")
                        
                        # Thread preview (first message)
                        if message_count > 0:
                            st.caption(f"📅 {date_str}")
                
                # Load more threads option
                if len(sorted_sessions) >= 10:
                    if st.button("Load More Threads"):
                        # In a real implementation, you'd load more with pagination
                        st.info("Loading more threads...")
                        
            else:
                st.info("No chat threads yet. Create your first thread above!")
            
            # Quick actions for current thread
            if st.session_state.current_chat_session:
                st.divider()
                st.subheader("Current Thread Actions")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Refresh", help="Reload thread history"):
                        self.load_chat_history(st.session_state.current_chat_session)
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Clear", help="Clear thread history"):
                        st.session_state.chat_history = []
                        st.rerun()
            
            st.divider()
            
            # Settings
            st.header("⚙️ Chat Settings")
            
            st.session_state.top_k = st.slider("Retrieval Results", 1, 20, st.session_state.top_k)
            
            # Document filter
            if st.session_state.documents:
                doc_options = {doc['original_filename']: doc['id'] for doc in st.session_state.documents 
                             if doc['processing_status'] == 'completed'}
                if doc_options:
                    selected_docs = st.multiselect(
                        "Filter by Documents",
                        options=list(doc_options.keys()),
                        default=[name for name in doc_options.keys() if doc_options[name] in st.session_state.document_filter],
                        help="Select specific documents to search in"
                    )
                    st.session_state.document_filter = [doc_options[name] for name in selected_docs]
            
            st.session_state.model_selector = st.selectbox(
                "AI Model", 
                ["gemini-pro", "gemini-pro-vision"], 
                index=0 if st.session_state.model_selector == "gemini-pro" else 1
            )
            
            st.session_state.only_answer_if_sources = st.checkbox(
                "Require source documents", 
                value=st.session_state.only_answer_if_sources,
                help="Only answer if relevant sources are found"
            )
            
            st.divider()
            
            # System Stats
            stats = self.get_stats()
            if stats:
                st.header("📊 System Stats")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Documents", stats.get("documents", {}).get("total", 0))
                    st.metric("Total Threads", stats.get("chat", {}).get("sessions", 0))
                with col2:
                    st.metric("Total Chunks", stats.get("vector_db", {}).get("total_chunks", 0))
                    st.metric("Total Messages", stats.get("chat", {}).get("messages", 0))
                with col2:
                    st.metric("Chunks", stats.get("chunks", {}).get("total", 0))
                    st.metric("Messages", stats.get("chat", {}).get("messages", 0))
    
    def render_file_upload(self):
        """Render file upload area"""
        st.header("📁 Document Upload")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Upload PDF documents",
                type=['pdf'],
                accept_multiple_files=True,
                help="Upload one or more PDF files to add to your knowledge base"
            )
            
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    with st.spinner(f"Uploading {uploaded_file.name}..."):
                        result = self.upload_document(uploaded_file)
                        if result:
                            if result['status'] == 'uploaded':
                                st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                            elif result['status'] == 'already_exists':
                                st.info(f"ℹ️ {uploaded_file.name} already exists")
                        else:
                            st.error(f"❌ Failed to upload {uploaded_file.name}")
                
                # Refresh documents after upload
                time.sleep(1)
                self.load_documents()
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh Documents"):
                self.load_documents()
                st.rerun()
    
    def render_documents_panel(self):
        """Render documents panel"""
        st.header("📚 Documents")
        
        if not st.session_state.documents:
            st.info("No documents uploaded yet. Upload some PDF files to get started!")
            return
        
        for doc in st.session_state.documents:
            with st.expander(f"📄 {doc['original_filename']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Size:** {doc['file_size'] / 1024 / 1024:.1f} MB")
                    st.write(f"**Pages:** {doc['page_count'] or 'N/A'}")
                    st.write(f"**Chunks:** {doc['chunk_count']}")
                    st.write(f"**Uploaded:** {doc['upload_timestamp'][:19]}")
                
                with col2:
                    status = doc['processing_status']
                    if status == 'completed':
                        st.success("✅ Ready")
                    elif status == 'processing':
                        st.warning("⏳ Processing...")
                    elif status == 'failed':
                        st.error("❌ Failed")
                        if doc.get('error_message'):
                            st.error(f"Error: {doc['error_message']}")
                    else:
                        st.info("⏸️ Pending")
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}"):
                        if self.delete_document(doc['id']):
                            st.success("Document deleted!")
                            st.rerun()
    
    def render_chat_message(self, message: Dict):
        """Render a single chat message"""
        if message['message_type'] == 'user':
            # Use Streamlit's built-in chat message component
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            # Assistant message using built-in component
            with st.chat_message("assistant"):
                st.write(message['content'])
                
                # Sources and context
                if message.get('sources'):
                    with st.expander(f"📚 Sources ({len(message['sources'])})", expanded=False):
                        for i, source in enumerate(message['sources']):
                            st.markdown(f"""
                            <div class="source-citation">
                                <strong>Source {i+1}:</strong> {source['document_name']} (Page {source['page_number']})
                                <br><em>Relevance: {source['relevance_score']:.3f}</em>
                                <br>{source['content'][:200]}...
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with st.expander("🔍 Show Context", expanded=False):
                        context_chunks = json.loads(message.get('context_chunks', '[]')) if isinstance(message.get('context_chunks'), str) else message.get('context_chunks', [])
                        for i, chunk in enumerate(context_chunks):
                            st.markdown(f"""
                            <div class="context-chunk">
                                <strong>Chunk {i+1}:</strong> {chunk.get('filename', 'Unknown')} (Page {chunk.get('page_number', 'N/A')})
                                <br>{chunk.get('content', '')[:300]}...
                            </div>
                            """, unsafe_allow_html=True)
    
    def render_chat_interface(self):
        """Render main chat interface with thread context"""
        if not st.session_state.current_chat_session:
            st.info("👈 Create or select a chat thread from the sidebar to start chatting!")
            return
        
        # Thread header with context
        current_thread = None
        for session in st.session_state.chat_sessions:
            if session['id'] == st.session_state.current_chat_session:
                current_thread = session
                break
        
        if current_thread:
            st.header(f"💬 {current_thread.get('session_name', 'Untitled Thread')}")
            
            # Thread info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Messages", current_thread.get('message_count', 0))
            with col2:
                created_date = current_thread.get('created_at', '')
                if created_date:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        date_str = dt.strftime("%m/%d/%Y")
                    except:
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"
                st.metric("Created", date_str)
            with col3:
                doc_count = len(st.session_state.document_filter) if st.session_state.document_filter else len([d for d in st.session_state.documents if d['processing_status'] == 'completed'])
                st.metric("Documents", doc_count)
            with col4:
                st.metric("Model", st.session_state.model_selector)
        else:
            st.header("💬 Chat Thread")
        
        st.divider()
        
        # Chat history container with improved rendering
        if st.session_state.chat_history:
            st.subheader("Conversation History")
            
            # Use Streamlit's native chat message components
            for message in st.session_state.chat_history:
                if message.get('message_type') == 'user':
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(message.get('content', ''))
                        
                        # Show timestamp
                        timestamp = message.get('timestamp', '')
                        if timestamp:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                time_str = dt.strftime("%H:%M")
                                st.caption(f"🕐 {time_str}")
                            except:
                                pass
                
                else:  # Assistant message
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message.get('content', ''))
                        
                        # Show timestamp
                        timestamp = message.get('timestamp', '')
                        if timestamp:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                time_str = dt.strftime("%H:%M")
                                st.caption(f"🕐 {time_str}")
                            except:
                                pass
                        
                        # Sources section
                        if message.get('sources'):
                            with st.expander(f"📚 Sources ({len(message['sources'])})", expanded=False):
                                for i, source in enumerate(message['sources']):
                                    st.markdown(f"""
                                    **📄 Source {i+1}:** `{source.get('document_name', 'Unknown')}`  
                                    **📍 Page:** {source.get('page_number', 'N/A')} | **🎯 Relevance:** {source.get('relevance_score', 0):.3f}  
                                    **💬 Content:**  
                                    > {source.get('content', '')[:300]}{'...' if len(source.get('content', '')) > 300 else ''}
                                    """)
                                    st.divider()
                        
                        # Context section
                        if message.get('context_chunks'):
                            context_chunks = json.loads(message.get('context_chunks', '[]')) if isinstance(message.get('context_chunks'), str) else message.get('context_chunks', [])
                            if context_chunks:
                                with st.expander(f"🔍 Retrieved Context ({len(context_chunks)} chunks)", expanded=False):
                                    for i, chunk in enumerate(context_chunks):
                                        st.markdown(f"""
                                        **📄 Chunk {i+1}:** `{chunk.get('filename', 'Unknown')}`  
                                        **📍 Page:** {chunk.get('page_number', 'N/A')} | **🎯 Score:** {chunk.get('score', 0):.3f}  
                                        **💬 Content:**  
                                        > {chunk.get('content', '')[:250]}{'...' if len(chunk.get('content', '')) > 250 else ''}
                                        """)
                                        if i < len(context_chunks) - 1:
                                            st.divider()
        else:
            st.info("👋 Start the conversation by asking a question about your documents!")
        
        st.divider()
        
        # Chat input area
        st.subheader("💭 Ask a Question")
        
        # Show current filter info
        if st.session_state.document_filter:
            filtered_docs = [doc['original_filename'] for doc in st.session_state.documents if doc['id'] in st.session_state.document_filter]
            st.info(f"🔍 Searching in: {', '.join(filtered_docs)}")
        elif st.session_state.documents:
            completed_docs = [doc for doc in st.session_state.documents if doc['processing_status'] == 'completed']
            if completed_docs:
                st.info(f"🔍 Searching in all {len(completed_docs)} documents")
            else:
                st.warning("⚠️ No processed documents available for search")
        else:
            st.warning("⚠️ No documents uploaded yet")
        
        # Chat input form
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Your question:",
                placeholder="e.g., What are the main topics discussed? Can you summarize the key findings? What does the document say about...?",
                height=100,
                help="Ask questions about your uploaded documents. The AI will search through them to provide relevant answers."
            )
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                submit_button = st.form_submit_button("💬 Send Message", use_container_width=True)
            with col2:
                clear_button = st.form_submit_button("🗑️ Clear Thread", use_container_width=True)
            with col3:
                refresh_button = st.form_submit_button("� Refresh", use_container_width=True)
            
            if submit_button and user_input.strip():
                # Check if we have documents to search
                if not st.session_state.documents:
                    st.error("❌ Please upload some documents first!")
                elif not any(doc['processing_status'] == 'completed' for doc in st.session_state.documents):
                    st.error("❌ Please wait for documents to finish processing!")
                else:
                    with st.spinner("🤔 Thinking... Searching through documents and generating response..."):
                        response = self.send_message(user_input.strip())
                        if response:
                            st.success("✅ Message sent!")
                            time.sleep(0.5)  # Brief pause for better UX
                            st.rerun()
                        else:
                            st.error("❌ Failed to send message. Please try again.")
            
            elif clear_button:
                st.session_state.chat_history = []
                st.success("🗑️ Thread history cleared!")
                st.rerun()
            
            elif refresh_button:
                if st.session_state.current_chat_session:
                    self.load_chat_history(st.session_state.current_chat_session)
                    st.success("🔄 Thread refreshed!")
                    st.rerun()
    
    def run(self):
        """Main application runner"""
        # Initialize user
        self.create_user()
        
        # Load initial data
        self.load_chat_sessions()
        self.load_documents()
        
        # Render sidebar
        self.render_sidebar()
        
        # Main content
        main_tab1, main_tab2 = st.tabs(["💬 Chat", "📁 Documents"])
        
        with main_tab1:
            self.render_chat_interface()
        
        with main_tab2:
            self.render_file_upload()
            st.divider()
            self.render_documents_panel()

if __name__ == "__main__":
    app = RAGChatApp()
    app.run()
