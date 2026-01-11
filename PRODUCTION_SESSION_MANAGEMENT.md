# Production Session Management - Best Practices

## Problem Statement

Your current implementation creates a **new session for every chat interaction**, leading to:

1. **Massive Storage Waste**: Duplicate copies of documents and FAISS indexes
2. **Performance Degradation**: Re-processing same documents repeatedly
3. **Cost Issues**: Unnecessary embedding generation (API costs if using paid embeddings)
4. **Scalability Problems**: Storage grows linearly with chat interactions

### Example Storage Growth
```
10 users × 100 chats each = 1,000 sessions
1 session = 60 MB (10 MB document + 50 MB FAISS index)
Total = 60 GB for the SAME document set!
```

---

## Solution Approaches

### **Approach 1: User-Based Sessions (Recommended for Multi-User Apps)**

Store one session per user, reuse FAISS index across chats.

#### Architecture
```
data/
  user_<user_id>/
    documents/
      doc1.pdf
      doc2.pdf
    
faiss_index/
  user_<user_id>/
    index.faiss
    index.pkl
    
chat_history/
  user_<user_id>/
    conversation_1.json
    conversation_2.json
```

#### Implementation

```python
# Production-ready session management
class ProductionChatManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_id = f"user_{user_id}"
        
        # Check if user already has indexed documents
        self.faiss_path = Path(f"faiss_index/{self.session_id}")
        self.has_existing_index = self.faiss_path.exists()
        
    def initialize_or_load_index(self, uploaded_files=None):
        """Initialize new index or load existing one"""
        
        if self.has_existing_index and not uploaded_files:
            # Load existing index - NO re-processing!
            print(f"Loading existing index for user {self.user_id}")
            self.rag = ConversationalRAG(session_id=self.session_id)
            self.rag.load_retriever_from_faiss(
                index_path=str(self.faiss_path),
                k=5,
                search_type="mmr"
            )
            return self.rag
            
        elif uploaded_files:
            # New documents uploaded - create/update index
            print(f"Creating/updating index for user {self.user_id}")
            ci = ChatIngestor(
                temp_base="data",
                faiss_base="faiss_index",
                use_session_dirs=True,
                session_id=self.session_id  # Reuse same session ID!
            )
            ci.built_retriver(uploaded_files, chunk_size=1000, chunk_overlap=200, k=5)
            
            self.rag = ConversationalRAG(session_id=self.session_id)
            self.rag.load_retriever_from_faiss(
                index_path=str(self.faiss_path),
                k=5
            )
            return self.rag
        else:
            raise ValueError("No existing index and no documents provided!")
    
    def chat(self, user_message: str, chat_history: List = None):
        """Chat without creating new session"""
        if not hasattr(self, 'rag'):
            raise ValueError("Index not initialized. Call initialize_or_load_index first!")
        
        return self.rag.invoke(user_message, chat_history or [])


# Usage Example
def production_usage():
    # User logs in
    user_id = "user_12345"
    chat_manager = ProductionChatManager(user_id)
    
    # First time: Upload documents
    if not chat_manager.has_existing_index:
        uploaded_files = [open("document.pdf", "rb")]
        chat_manager.initialize_or_load_index(uploaded_files)
    else:
        # Subsequent chats: Just load existing index
        chat_manager.initialize_or_load_index()
    
    # Multiple chats - same session, same index!
    chat_history = []
    
    # Chat 1
    answer1 = chat_manager.chat("What is attention?", chat_history)
    chat_history.append(HumanMessage(content="What is attention?"))
    chat_history.append(AIMessage(content=answer1))
    
    # Chat 2
    answer2 = chat_manager.chat("Tell me more", chat_history)
    # Uses SAME index - no duplication!
```

---

### **Approach 2: Document-Based Sessions (For Shared Documents)**

Store one session per unique document set, shared across users.

#### Architecture
```
data/
  shared/
    doc_<hash>/
      document.pdf
      
faiss_index/
  doc_<hash>/
    index.faiss
    index.pkl
    
user_sessions/
  user_<user_id>/
    active_document: doc_<hash>
    chat_history.json
```

#### Implementation

```python
import hashlib

class DocumentBasedSessionManager:
    def __init__(self):
        self.document_cache = {}  # Cache document hashes -> session IDs
    
    def get_document_hash(self, file_path: str) -> str:
        """Create hash of document content"""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    
    def get_or_create_session(self, document_paths: List[str]) -> str:
        """Get existing session or create new one for document set"""
        
        # Create combined hash for document set
        doc_hashes = [self.get_document_hash(p) for p in document_paths]
        combined_hash = hashlib.sha256(''.join(sorted(doc_hashes)).encode()).hexdigest()[:16]
        
        session_id = f"doc_{combined_hash}"
        index_path = Path(f"faiss_index/{session_id}")
        
        if index_path.exists():
            print(f"Reusing existing index: {session_id}")
            return session_id
        else:
            print(f"Creating new index: {session_id}")
            # Process documents and create index
            ci = ChatIngestor(
                temp_base="data",
                faiss_base="faiss_index",
                use_session_dirs=True,
                session_id=session_id
            )
            uploaded_files = [open(p, 'rb') for p in document_paths]
            ci.built_retriver(uploaded_files, chunk_size=1000, chunk_overlap=200, k=5)
            
            for f in uploaded_files:
                f.close()
            
            return session_id
    
    def chat_with_documents(self, user_id: str, document_paths: List[str], message: str):
        """Chat with specific documents"""
        
        # Get or create shared session
        session_id = self.get_or_create_session(document_paths)
        
        # Create RAG instance (lightweight - just loads existing index)
        rag = ConversationalRAG(session_id=session_id)
        rag.load_retriever_from_faiss(
            index_path=f"faiss_index/{session_id}",
            k=5
        )
        
        # Load user's chat history (stored separately)
        chat_history = self.load_user_history(user_id, session_id)
        
        # Generate answer
        answer = rag.invoke(message, chat_history)
        
        # Save user's history
        self.save_user_history(user_id, session_id, message, answer)
        
        return answer
    
    def load_user_history(self, user_id: str, session_id: str) -> List:
        """Load user-specific chat history"""
        history_path = Path(f"user_sessions/{user_id}/{session_id}_history.json")
        if history_path.exists():
            import json
            with open(history_path, 'r') as f:
                data = json.load(f)
                # Convert to LangChain message objects
                return [
                    HumanMessage(content=msg['content']) if msg['type'] == 'human'
                    else AIMessage(content=msg['content'])
                    for msg in data
                ]
        return []
    
    def save_user_history(self, user_id: str, session_id: str, message: str, answer: str):
        """Save user-specific chat history"""
        history_path = Path(f"user_sessions/{user_id}/{session_id}_history.json")
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        history = []
        if history_path.exists():
            import json
            with open(history_path, 'r') as f:
                history = json.load(f)
        
        # Append new messages
        history.append({'type': 'human', 'content': message})
        history.append({'type': 'ai', 'content': answer})
        
        # Save
        import json
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)


# Usage Example
manager = DocumentBasedSessionManager()

# User 1 chats with document
answer1 = manager.chat_with_documents(
    user_id="user_123",
    document_paths=["report.pdf"],
    message="What is the summary?"
)

# User 2 chats with SAME document - reuses index!
answer2 = manager.chat_with_documents(
    user_id="user_456",
    document_paths=["report.pdf"],
    message="What are the key findings?"
)
# No duplicate index created!
```

---

### **Approach 3: Global Document Store (Enterprise)**

Central document repository with reference counting.

#### Architecture
```
documents/
  <doc_hash>.pdf
  
embeddings/
  <doc_hash>/
    index.faiss
    metadata.json
    
users/
  <user_id>/
    workspace/
      - doc_ref: <doc_hash>
      - doc_ref: <doc_hash>
    conversations/
      conv_1.json
      conv_2.json
```

#### Benefits
- **Zero Duplication**: Each document stored once
- **Shared Embeddings**: Multiple users share same FAISS index
- **Efficient Updates**: Update document once, all users benefit
- **Reference Counting**: Delete when no users reference it

---

## Recommended Implementation Changes

### **1. Modify ChatIngestor to Accept Session ID**

Already supported! Just pass `session_id` parameter:

```python
# GOOD: Reuse session
ci = ChatIngestor(
    temp_base="data",
    faiss_base="faiss_index",
    use_session_dirs=True,
    session_id="user_12345"  # ✅ Fixed session ID
)
```

### **2. Separate Ingestion from Chatting**

```python
# Ingestion (one-time or on document upload)
def ingest_documents(user_id: str, files: List):
    session_id = f"user_{user_id}"
    ci = ChatIngestor(session_id=session_id)
    ci.built_retriver(files, chunk_size=1000, chunk_overlap=200, k=5)
    return session_id

# Chatting (reuses existing index)
def chat_with_documents(user_id: str, message: str, history: List):
    session_id = f"user_{user_id}"
    rag = ConversationalRAG(session_id=session_id)
    rag.load_retriever_from_faiss(
        index_path=f"faiss_index/{session_id}",
        k=5
    )
    return rag.invoke(message, history)
```

### **3. Add Session Cleanup**

```python
import shutil
from datetime import datetime, timedelta

def cleanup_old_sessions(max_age_days: int = 30):
    """Delete sessions older than max_age_days"""
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    for session_dir in Path("data").glob("session_*"):
        # Parse session timestamp from directory name
        # session_20260104_120000_abc123
        parts = session_dir.name.split("_")
        if len(parts) >= 3:
            date_str = parts[1]  # 20260104
            time_str = parts[2]  # 120000
            
            session_date = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            
            if session_date < cutoff_date:
                print(f"Deleting old session: {session_dir}")
                shutil.rmtree(session_dir)
                
                # Also delete corresponding FAISS index
                faiss_dir = Path("faiss_index") / session_dir.name
                if faiss_dir.exists():
                    shutil.rmtree(faiss_dir)
```

---

## Storage Comparison

### Current Approach (Session Per Chat)
```
Users: 100
Chats per user: 50
Document size: 10 MB
FAISS index: 50 MB

Total storage: 100 × 50 × 60 MB = 300 GB
```

### Recommended Approach (Session Per User)
```
Users: 100
Chats per user: 50
Document size: 10 MB
FAISS index: 50 MB

Total storage: 100 × 60 MB = 6 GB
Savings: 98% reduction!
```

### Optimal Approach (Shared Documents)
```
Users: 100
Unique documents: 10
Document size: 10 MB
FAISS index: 50 MB

Total storage: 10 × 60 MB = 600 MB
Savings: 99.8% reduction!
```

---

## Implementation Checklist

- [ ] **Modify test.py** to use fixed session IDs
- [ ] **Add session management logic** (user-based or doc-based)
- [ ] **Implement session reuse** in ConversationalRAG
- [ ] **Add cleanup jobs** for old sessions
- [ ] **Implement user authentication** to track sessions
- [ ] **Add session metadata** (creation time, last accessed, document list)
- [ ] **Monitor storage usage** with metrics/alerts
- [ ] **Add session expiration** policies
- [ ] **Implement backup strategy** for important indexes
- [ ] **Add index versioning** for updates

---

## Best Practices Summary

1. **Session = User or Document Set, NOT Chat**
2. **Reuse FAISS indexes** across multiple chats
3. **Hash documents** to detect duplicates
4. **Implement cleanup** for old/unused sessions
5. **Monitor storage** and set limits
6. **Use reference counting** in enterprise scenarios
7. **Separate ingestion** from querying
8. **Cache embeddings** for frequently accessed documents
9. **Implement lazy loading** for indexes
10. **Add expiration policies** (7 days, 30 days, etc.)

---

## Production Metrics to Track

```python
# Add to your application
class SessionMetrics:
    def __init__(self):
        self.total_sessions = 0
        self.active_sessions = 0
        self.total_storage_mb = 0
        self.avg_session_size_mb = 0
        self.duplicate_prevention_savings_mb = 0
    
    def calculate_metrics(self):
        # Count sessions
        sessions = list(Path("faiss_index").glob("*"))
        self.total_sessions = len(sessions)
        
        # Calculate storage
        total_size = sum(
            sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file())
            for session_dir in sessions
        )
        self.total_storage_mb = total_size / (1024 * 1024)
        
        if self.total_sessions > 0:
            self.avg_session_size_mb = self.total_storage_mb / self.total_sessions
        
        return {
            'total_sessions': self.total_sessions,
            'total_storage_gb': self.total_storage_mb / 1024,
            'avg_session_size_mb': self.avg_session_size_mb
        }
```

---

## Conclusion

Your observation is **100% correct** - the current implementation would be **disastrous for production**. The recommended fixes will:

- **Reduce storage by 98-99%**
- **Improve performance** (no re-processing)
- **Lower costs** (fewer API calls)
- **Enable scalability** (thousands of users)

Implement **Approach 1** (User-Based Sessions) as a starting point, then evolve to **Approach 2** or **3** as your application scales.