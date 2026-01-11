"""
Production-Ready Chat Manager with Session Reuse
Fixes the storage duplication issue by reusing sessions per user
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional
from multi_doc_chat.src.document_ingestion.data_ingestion import ChatIngestor
from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import json
from datetime import datetime

load_dotenv()


class ProductionChatManager:
    """
    Production-ready chat manager that reuses sessions and FAISS indexes.
    
    Key Features:
    - One session per user (not per chat)
    - Reuses FAISS index across multiple conversations
    - Separates document ingestion from chatting
    - Persistent chat history storage
    """
    
    def __init__(self, user_id: str, temp_base: str = "data", faiss_base: str = "faiss_index"):
        self.user_id = user_id
        self.session_id = f"user_{user_id}"
        self.temp_base = temp_base
        self.faiss_base = faiss_base
        
        # Paths
        self.faiss_path = Path(faiss_base) / self.session_id
        self.data_path = Path(temp_base) / self.session_id
        self.history_path = Path("chat_history") / f"{self.session_id}.json"
        
        # Check if user already has indexed documents
        self.has_existing_index = self.faiss_path.exists()
        
        self.rag: Optional[ConversationalRAG] = None
        
        print(f"📁 Session ID: {self.session_id}")
        print(f"📊 Existing index: {'✅ Yes' if self.has_existing_index else '❌ No'}")
    
    def ingest_documents(self, file_paths: List[str], chunk_size: int = 1000, 
                        chunk_overlap: int = 200, k: int = 5) -> bool:
        """
        Ingest documents and create/update FAISS index.
        Call this ONLY when uploading new documents, not for every chat!
        
        Args:
            file_paths: List of document paths to ingest
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            k: Number of documents to retrieve
            
        Returns:
            bool: True if successful
        """
        print(f"\n🔄 Ingesting documents for user {self.user_id}...")
        
        try:
            # Open files
            uploaded_files = []
            for file_path in file_paths:
                if Path(file_path).exists():
                    uploaded_files.append(open(file_path, "rb"))
                else:
                    print(f"⚠️  File not found: {file_path}")
            
            if not uploaded_files:
                print("❌ No valid files to ingest")
                return False
            
            # Create/update index with FIXED session ID
            ci = ChatIngestor(
                temp_base=self.temp_base,
                faiss_base=self.faiss_base,
                use_session_dirs=True,
                session_id=self.session_id  # 🔑 KEY FIX: Reuse same session ID
            )
            
            ci.built_retriver(
                uploaded_files,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                k=k,
                search_type="mmr",
                fetch_k=20,
                lambda_mult=0.5
            )
            
            # Close files
            for f in uploaded_files:
                try:
                    f.close()
                except:
                    pass
            
            self.has_existing_index = True
            print(f"✅ Documents ingested successfully!")
            print(f"📁 Index stored at: {self.faiss_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error ingesting documents: {e}")
            return False
    
    def initialize_rag(self, k: int = 5) -> bool:
        """
        Initialize or load RAG system with existing FAISS index.
        This is lightweight - just loads existing index, no re-processing!
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            bool: True if successful
        """
        if not self.has_existing_index:
            print("❌ No existing index found. Please call ingest_documents() first!")
            return False
        
        try:
            print(f"\n🔄 Loading RAG system for user {self.user_id}...")
            
            # Create RAG instance
            self.rag = ConversationalRAG(session_id=self.session_id)
            
            # Load existing FAISS index (no re-processing!)
            self.rag.load_retriever_from_faiss(
                index_path=str(self.faiss_path),
                k=k,
                index_name=os.getenv("FAISS_INDEX_NAME", "index"),
                search_type="mmr",
                fetch_k=20,
                lambda_mult=0.5
            )
            
            print(f"✅ RAG system loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading RAG system: {e}")
            return False
    
    def chat(self, user_message: str, save_history: bool = True) -> str:
        """
        Chat with the documents using existing index.
        
        Args:
            user_message: User's question
            save_history: Whether to save chat history to disk
            
        Returns:
            str: AI's answer
        """
        if self.rag is None:
            raise ValueError("RAG not initialized. Call initialize_rag() first!")
        
        # Load chat history
        chat_history = self.load_chat_history()
        
        # Get answer
        print(f"\n💬 User: {user_message}")
        answer = self.rag.invoke(user_message, chat_history=chat_history)
        print(f"🤖 Assistant: {answer}")
        
        # Save to history
        if save_history:
            chat_history.append(HumanMessage(content=user_message))
            chat_history.append(AIMessage(content=answer))
            self.save_chat_history(chat_history)
        
        return answer
    
    def load_chat_history(self) -> List[BaseMessage]:
        """Load chat history from disk"""
        if not self.history_path.exists():
            return []
        
        try:
            with open(self.history_path, 'r') as f:
                data = json.load(f)
                
            history = []
            for msg in data:
                if msg['type'] == 'human':
                    history.append(HumanMessage(content=msg['content']))
                else:
                    history.append(AIMessage(content=msg['content']))
            
            return history
            
        except Exception as e:
            print(f"⚠️  Error loading chat history: {e}")
            return []
    
    def save_chat_history(self, history: List[BaseMessage]) -> None:
        """Save chat history to disk"""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = []
            for msg in history:
                if isinstance(msg, HumanMessage):
                    data.append({'type': 'human', 'content': msg.content})
                elif isinstance(msg, AIMessage):
                    data.append({'type': 'ai', 'content': msg.content})
            
            with open(self.history_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Error saving chat history: {e}")
    
    def clear_chat_history(self) -> None:
        """Clear chat history"""
        if self.history_path.exists():
            self.history_path.unlink()
            print("✅ Chat history cleared")
    
    def get_session_info(self) -> dict:
        """Get session information"""
        info = {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'has_index': self.has_existing_index,
            'index_path': str(self.faiss_path) if self.has_existing_index else None,
            'data_path': str(self.data_path) if self.data_path.exists() else None,
            'history_path': str(self.history_path) if self.history_path.exists() else None,
        }
        
        # Calculate storage
        if self.has_existing_index:
            index_size = sum(f.stat().st_size for f in self.faiss_path.rglob('*') if f.is_file())
            info['index_size_mb'] = round(index_size / (1024 * 1024), 2)
        
        if self.data_path.exists():
            data_size = sum(f.stat().st_size for f in self.data_path.rglob('*') if f.is_file())
            info['data_size_mb'] = round(data_size / (1024 * 1024), 2)
        
        return info


def example_first_time_user():
    """Example: First time user uploads documents"""
    print("\n" + "="*60)
    print("EXAMPLE 1: First-time user - Document upload and chat")
    print("="*60)
    
    user_id = "alice_2024"
    manager = ProductionChatManager(user_id)
    
    # First time: Ingest documents
    if not manager.has_existing_index:
        print("\n📤 Uploading documents...")
        success = manager.ingest_documents(
            file_paths=["./data/NIPS-2017-attention-is-all-you-need-Paper.pdf"],
            chunk_size=1000,
            chunk_overlap=200,
            k=5
        )
        
        if not success:
            print("❌ Failed to ingest documents")
            return
    
    # Initialize RAG
    manager.initialize_rag(k=5)
    
    # Multiple chats - SAME SESSION!
    manager.chat("What is attention mechanism?")
    manager.chat("How does it work?")
    manager.chat("What are the benefits?")
    
    # Show session info
    print("\n📊 Session Info:")
    info = manager.get_session_info()
    for key, value in info.items():
        print(f"   {key}: {value}")


def example_returning_user():
    """Example: Returning user continues conversation"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Returning user - Load existing index")
    print("="*60)
    
    user_id = "alice_2024"  # Same user as before
    manager = ProductionChatManager(user_id)
    
    # Load existing index (NO re-processing!)
    if manager.has_existing_index:
        print("\n✅ Found existing index, loading...")
        manager.initialize_rag(k=5)
        
        # Continue chatting - loads previous history
        manager.chat("Can you summarize what we discussed?")
        manager.chat("Tell me more about transformers")
    else:
        print("❌ No existing index found. User needs to upload documents first.")


def example_multiple_users():
    """Example: Multiple users, each with their own session"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Multiple users - Separate sessions")
    print("="*60)
    
    users = ["alice_2024", "bob_2024", "charlie_2024"]
    
    for user_id in users:
        print(f"\n👤 User: {user_id}")
        manager = ProductionChatManager(user_id)
        
        # Each user has their own session and index
        if not manager.has_existing_index:
            manager.ingest_documents(
                file_paths=["./data/NIPS-2017-attention-is-all-you-need-Paper.pdf"]
            )
        
        manager.initialize_rag()
        manager.chat(f"Hello, I'm {user_id}. What is this paper about?")


def compare_storage():
    """Compare storage usage between approaches"""
    print("\n" + "="*60)
    print("STORAGE COMPARISON")
    print("="*60)
    
    # Count session directories
    old_sessions = list(Path("data").glob("session_*"))
    user_sessions = list(Path("data").glob("user_*"))
    
    print(f"\n📁 Old approach (session per chat): {len(old_sessions)} sessions")
    print(f"📁 New approach (session per user): {len(user_sessions)} sessions")
    
    # Calculate storage
    if old_sessions:
        old_storage = sum(
            sum(f.stat().st_size for f in s.rglob('*') if f.is_file())
            for s in old_sessions
        ) / (1024 * 1024)
        print(f"💾 Old approach storage: {old_storage:.2f} MB")
    
    if user_sessions:
        new_storage = sum(
            sum(f.stat().st_size for f in s.rglob('*') if f.is_file())
            for s in user_sessions
        ) / (1024 * 1024)
        print(f"💾 New approach storage: {new_storage:.2f} MB")
        
        if old_sessions:
            savings = ((old_storage - new_storage) / old_storage) * 100
            print(f"💰 Storage savings: {savings:.1f}%")


if __name__ == "__main__":
    print("🚀 Production Chat Manager - Fixed Session Management")
    print("=" * 60)
    
    # Run examples
    example_first_time_user()
    # example_returning_user()  # Uncomment to test returning user
    # example_multiple_users()  # Uncomment to test multiple users
    # compare_storage()  # Uncomment to compare storage
