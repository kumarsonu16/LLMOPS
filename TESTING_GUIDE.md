# 🧪 Python Testing Guide for Node.js Developers

> **Your Background**: You're familiar with Jest/Mocha/Chai in Node.js  
> **Python Testing**: Uses pytest (like Jest for Python)

---

## 📚 Table of Contents
1. [Python vs Node.js Testing Comparison](#comparison)
2. [Project Structure Explained](#structure)
3. [Pytest Basics](#pytest-basics)
4. [Fixtures - The Magic of Pytest](#fixtures)
5. [Your Test Files Explained Step-by-Step](#your-tests)
6. [Running Tests](#running-tests)
7. [Common Patterns](#patterns)

---

## 🔄 Python vs Node.js Testing Comparison {#comparison}

| Concept | Node.js (Jest/Mocha) | Python (pytest) |
|---------|---------------------|-----------------|
| **Test Framework** | `jest` or `mocha` | `pytest` |
| **Test Files** | `*.test.js` or `*.spec.js` | `test_*.py` or `*_test.py` |
| **Test Functions** | `test('description', () => {})` | `def test_description():` |
| **Setup/Teardown** | `beforeEach()`, `afterEach()` | `@pytest.fixture` with `yield` |
| **Mocking** | `jest.mock()` or `sinon` | `monkeypatch` (pytest) or `unittest.mock` |
| **Assertions** | `expect(x).toBe(y)` | `assert x == y` |
| **HTTP Client** | `supertest` | `TestClient` (FastAPI) |
| **Running Tests** | `npm test` | `pytest` |

### Node.js Example:
```javascript
// user.test.js
const request = require('supertest');
const app = require('./app');

describe('User API', () => {
  beforeEach(() => {
    // setup
  });

  test('should create user', async () => {
    const res = await request(app)
      .post('/users')
      .send({ name: 'John' });
    
    expect(res.status).toBe(201);
    expect(res.body.name).toBe('John');
  });
});
```

### Python Equivalent:
```python
# test_user.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_should_create_user(client):
    res = client.post('/users', json={'name': 'John'})
    
    assert res.status_code == 201
    assert res.json()['name'] == 'John'
```

---

## 📁 Project Structure Explained {#structure}

```
tests/
├── conftest.py          # Global fixtures (like setupTests.js in Jest)
├── integration/         # Tests that test multiple components together
│   ├── test_upload_route.py
│   └── test_chat_route.py
└── unit/               # Tests for individual functions/classes
    ├── test_data_ingestion.py
    └── test_retrieval.py
```

### What is `conftest.py`?
Think of it as your **test setup file** (like `setupTests.js` or `jest.config.js`):
- Defines **fixtures** (reusable setup code)
- Runs before tests start
- Available to ALL test files automatically
- You don't need to import it!

**Node.js equivalent:**
```javascript
// setupTests.js (Jest)
beforeEach(() => {
  // runs before each test
});

global.mockUser = { id: 1, name: 'Test' };
```

**Python equivalent:**
```python
# conftest.py
import pytest

@pytest.fixture
def mock_user():
    return {'id': 1, 'name': 'Test'}
```

---

## 🎯 Pytest Basics {#pytest-basics}

### 1. **Test Discovery**
Pytest automatically finds and runs tests:
- Files named `test_*.py` or `*_test.py`
- Functions named `test_*()`
- Classes named `Test*`

### 2. **Writing Tests**

**Node.js:**
```javascript
test('adds 1 + 2 to equal 3', () => {
  expect(1 + 2).toBe(3);
});
```

**Python:**
```python
def test_adds_1_plus_2_equals_3():
    assert 1 + 2 == 3
```

### 3. **Assertions**

| Node.js (Jest) | Python (pytest) |
|---------------|-----------------|
| `expect(x).toBe(y)` | `assert x == y` |
| `expect(x).toBeTruthy()` | `assert x` |
| `expect(x).toBeNull()` | `assert x is None` |
| `expect(arr).toContain(item)` | `assert item in arr` |
| `expect(str).toMatch(/pattern/)` | `assert "substring" in str` |

### 4. **Test Organization**

**Node.js:**
```javascript
describe('Calculator', () => {
  describe('add', () => {
    test('should add two numbers', () => {
      expect(add(1, 2)).toBe(3);
    });
  });
});
```

**Python (using classes - optional):**
```python
class TestCalculator:
    class TestAdd:
        def test_should_add_two_numbers(self):
            assert add(1, 2) == 3

# OR just use functions (simpler):
def test_calculator_add_should_add_two_numbers():
    assert add(1, 2) == 3
```

---

## 🪄 Fixtures - The Magic of Pytest {#fixtures}

Fixtures are pytest's superpower! They're like **beforeEach/afterEach but WAY more flexible**.

### Node.js Way:
```javascript
let db;

beforeEach(() => {
  db = connectToDatabase();
});

afterEach(() => {
  db.disconnect();
});

test('should query users', () => {
  const users = db.query('SELECT * FROM users');
  expect(users).toBeDefined();
});
```

### Python Way (Better!):
```python
import pytest

@pytest.fixture
def db():
    database = connect_to_database()
    yield database  # This is like "return" but allows cleanup
    database.disconnect()  # This runs after the test

def test_should_query_users(db):  # Just add 'db' as parameter!
    users = db.query('SELECT * FROM users')
    assert users is not None
```

### Key Fixture Concepts:

#### 1. **Fixture as Function Parameter**
```python
@pytest.fixture
def user():
    return {'id': 1, 'name': 'Alice'}

def test_user_has_name(user):  # 'user' fixture injected automatically
    assert user['name'] == 'Alice'
```

#### 2. **Fixture with Setup & Teardown**
```python
@pytest.fixture
def temp_file():
    # Setup
    file = open('test.txt', 'w')
    file.write('test')
    
    yield file  # Give the file to the test
    
    # Teardown (runs after test completes)
    file.close()
    os.remove('test.txt')
```

#### 3. **Fixture Composition** (Fixtures can use other fixtures!)
```python
@pytest.fixture
def db():
    return Database()

@pytest.fixture
def user_repo(db):  # Uses 'db' fixture
    return UserRepository(db)

def test_create_user(user_repo):  # Uses 'user_repo' which uses 'db'
    user = user_repo.create('Alice')
    assert user.name == 'Alice'
```

#### 4. **Fixture Scope**
```python
@pytest.fixture(scope="function")  # Default: runs before EACH test
def fresh_db():
    return Database()

@pytest.fixture(scope="module")  # Runs once per TEST FILE
def shared_db():
    return Database()

@pytest.fixture(scope="session")  # Runs once for ENTIRE test run
def config():
    return load_config()
```

---

## 📝 Your Test Files Explained Step-by-Step {#your-tests}

### 1️⃣ **conftest.py** - The Foundation

Let's break down YOUR conftest.py:

```python
import pytest
from fastapi.testclient import TestClient

# Import your main FastAPI app
import main

# 🔧 FIXTURE 1: HTTP Client for testing FastAPI
@pytest.fixture
def client():
    """
    Creates a test client for making HTTP requests to your FastAPI app.
    
    Node.js equivalent:
    const request = require('supertest');
    const client = request(app);
    """
    return TestClient(main.app)


# 🔧 FIXTURE 2: Clear session data between tests
@pytest.fixture
def clear_sessions():
    """
    Clears the SESSIONS dict before and after each test.
    Prevents test pollution (one test affecting another).
    
    Node.js equivalent:
    beforeEach(() => {
        sessions.clear();
    });
    afterEach(() => {
        sessions.clear();
    });
    """
    main.SESSIONS.clear()  # Clear before test
    yield                   # Run the test
    main.SESSIONS.clear()  # Clear after test


# 🔧 FIXTURE 3: Temporary directories for testing
@pytest.fixture
def tmp_dirs(tmp_path):  # tmp_path is a built-in pytest fixture!
    """
    Creates temporary data and faiss directories for testing.
    Automatically cleaned up after tests.
    
    Node.js equivalent:
    const tmp = require('tmp');
    const tmpDir = tmp.dirSync();
    """
    data_dir = tmp_path / "data"
    faiss_dir = tmp_path / "faiss_index"
    data_dir.mkdir(parents=True, exist_ok=True)
    faiss_dir.mkdir(parents=True, exist_ok=True)
    
    cwd = pathlib.Path.cwd()
    try:
        os.chdir(tmp_path)  # Change to temp directory
        yield {"data": data_dir, "faiss": faiss_dir}
    finally:
        os.chdir(cwd)  # Change back to original directory


# 🔧 FIXTURE 4: Stub/Mock Embeddings (fake AI model)
class _StubEmbeddings:
    """
    Fake embeddings model for testing.
    Returns dummy vectors instead of calling real AI APIs.
    
    Node.js equivalent:
    const mockEmbeddings = {
        embed_query: jest.fn().mockReturnValue([0.0, 0.1, 0.2])
    };
    """
    def embed_query(self, text: str):
        return [0.0, 0.1, 0.2]
    
    def embed_documents(self, texts):
        return [[0.0, 0.1, 0.2] for _ in texts]


# 🔧 FIXTURE 5: Stub/Mock LLM (fake AI chatbot)
class _StubLLM:
    """
    Fake LLM for testing.
    Always returns "stubbed answer" instead of calling real API.
    """
    def invoke(self, input):
        return "stubbed answer"


# 🔧 FIXTURE 6: Mock the entire model loader
@pytest.fixture
def stub_model_loader(monkeypatch):
    """
    Replaces the real ModelLoader with a fake one.
    This prevents:
    - Calling real APIs (costs money, slow, unreliable)
    - Needing API keys in tests
    - Tests failing due to network issues
    
    Node.js equivalent:
    jest.mock('./model_loader', () => ({
        ModelLoader: {
            load_embeddings: () => mockEmbeddings,
            load_llm: () => mockLLM
        }
    }));
    """
    import multi_doc_chat.utils.model_loader as ml_mod
    
    class FakeModelLoader:
        def load_embeddings(self):
            return _StubEmbeddings()
        
        def load_llm(self):
            return _StubLLM()
    
    # monkeypatch = pytest's way to mock/replace objects
    monkeypatch.setattr(ml_mod, "ModelLoader", FakeModelLoader)
    yield FakeModelLoader


# 🔧 FIXTURE 7: Mock the ChatIngestor
@pytest.fixture
def stub_ingestor(monkeypatch):
    """
    Replaces the real document ingestion with a fake one.
    
    Node.js equivalent:
    jest.mock('./data_ingestion', () => ({
        ChatIngestor: jest.fn().mockImplementation(() => ({
            built_retriver: jest.fn().mockResolvedValue(null)
        }))
    }));
    """
    import multi_doc_chat.src.document_ingestion.data_ingestion as di
    
    class FakeIngestor:
        def __init__(self, use_session_dirs=True, **kwargs):
            self.session_id = "sess_test"
        
        def built_retriver(self, uploaded_files, **kwargs):
            return None  # Fake processing
    
    monkeypatch.setattr(di, "ChatIngestor", FakeIngestor)
    monkeypatch.setattr(main, "ChatIngestor", FakeIngestor)
    yield FakeIngestor


# 🔧 FIXTURE 8: Mock the RAG (Retrieval-Augmented Generation)
@pytest.fixture
def stub_rag(monkeypatch):
    """
    Replaces real AI chat with fake one.
    Always returns "stubbed answer" for testing.
    """
    import multi_doc_chat.src.document_chat.retrieval as r
    
    class FakeRAG:
        def __init__(self, session_id=None, retriever=None):
            self.session_id = session_id
            self.retriever = retriever
        
        def load_retriever_from_faiss(self, index_path, **kwargs):
            return None
        
        def invoke(self, user_input, chat_history=None):
            return "stubbed answer"
    
    monkeypatch.setattr(r, "ConversationalRAG", FakeRAG)
    monkeypatch.setattr(main, "ConversationalRAG", FakeRAG)
    yield FakeRAG
```

---

### 2️⃣ **test_chat_route.py** - Integration Tests

```python
import pytest

# TEST 1: Invalid session should return 404
def test_chat_invalid_session_returns_400(client, clear_sessions, stub_rag):
    """
    What it tests: Sending a message with a non-existent session ID
    Expected: Server returns 404 error
    
    Node.js equivalent:
    test('should return 404 for invalid session', async () => {
        const res = await request(app)
            .post('/chat')
            .send({ session_id: 'nope', message: 'hi' });
        expect(res.status).toBe(404);
        expect(res.body.detail).toContain('Invalid or expired');
    });
    
    Breakdown:
    1. client - HTTP test client from fixture
    2. clear_sessions - ensures clean state
    3. stub_rag - uses fake AI instead of real one
    """
    body = {"session_id": "nope", "message": "hi"}
    resp = client.post("/chat", json=body)
    assert resp.status_code == 404
    assert "Invalid or expired" in resp.json()["detail"]


# TEST 2: Empty message should return 400
def test_chat_empty_message_returns_400(client, clear_sessions, stub_rag):
    """
    What it tests: Sending empty/whitespace-only message
    Expected: Server returns 400 error
    
    Steps:
    1. Create a test session
    2. Send empty message
    3. Check for 400 error
    """
    sid = "sess_test"
    import main
    main.SESSIONS[sid] = []  # Create session with empty history
    
    body = {"session_id": sid, "message": "   "}  # Whitespace message
    resp = client.post("/chat", json=body)
    
    assert resp.status_code == 400
    assert "Message cannot be empty" in resp.json()["detail"]


# TEST 3: Successful chat should return answer and update history
def test_chat_success_returns_answer_and_appends_history(client, clear_sessions, stub_rag):
    """
    What it tests: Normal successful chat interaction
    Expected: 
    - Returns 200 status
    - Returns AI answer
    - Adds user message + AI response to chat history (2 messages)
    
    Node.js equivalent:
    test('should handle successful chat', async () => {
        sessions['sess_test'] = [];
        const res = await request(app)
            .post('/chat')
            .send({ session_id: 'sess_test', message: 'Hello' });
        
        expect(res.status).toBe(200);
        expect(res.body.answer).toBe('stubbed answer');
        expect(sessions['sess_test'].length).toBe(2);
    });
    """
    sid = "sess_test"
    import main
    main.SESSIONS[sid] = []  # Start with empty history
    
    body = {"session_id": sid, "message": "Hello"}
    resp = client.post("/chat", json=body)
    
    assert resp.status_code == 200
    assert resp.json()["answer"] == "stubbed answer"
    assert len(main.SESSIONS[sid]) == 2  # User message + AI response


# TEST 4: RAG failure should return 500
def test_chat_failure_returns_500(client, clear_sessions, monkeypatch):
    """
    What it tests: What happens when the AI system crashes
    Expected: Server returns 500 error with error message
    
    This test REPLACES the fake RAG with a BROKEN fake RAG!
    (Yes, we're faking a fake to test error handling)
    
    Node.js equivalent:
    test('should handle RAG failure', async () => {
        const BrokenRAG = jest.fn().mockImplementation(() => {
            throw new Error('fail load');
        });
        jest.mock('./retrieval', () => ({ ConversationalRAG: BrokenRAG }));
        
        const res = await request(app)
            .post('/chat')
            .send({ session_id: 'sess_test', message: 'hi' });
        
        expect(res.status).toBe(500);
        expect(res.body.detail).toContain('fail load');
    });
    """
    sid = "sess_test"
    import main
    main.SESSIONS[sid] = []
    
    # Create a BROKEN fake RAG that throws errors
    class BoomRAG:
        def __init__(self, session_id=None):
            pass
        
        def load_retriever_from_faiss(self, *a, **k):
            from multi_doc_chat.exception.custom_exception import DocumentPortalException
            raise DocumentPortalException("fail load", None)
    
    # Replace the working fake RAG with broken fake RAG
    monkeypatch.setattr(main, "ConversationalRAG", BoomRAG)
    
    resp = client.post("/chat", json={"session_id": sid, "message": "hi"})
    
    assert resp.status_code == 500
    assert "fail load" in resp.json()["detail"].lower()
```

---

### 3️⃣ **test_upload_route.py** - File Upload Tests

```python
import io
import pytest

# TEST 1: Successful file upload
def test_upload_success_returns_session_and_indexed(client, clear_sessions, stub_ingestor, tmp_dirs):
    """
    What it tests: Uploading a file successfully
    Expected:
    - Returns 200 status
    - Returns session_id
    - Returns indexed=True
    
    Node.js equivalent:
    test('should upload file successfully', async () => {
        const res = await request(app)
            .post('/upload')
            .attach('files', Buffer.from('hello world'), 'note.txt');
        
        expect(res.status).toBe(200);
        expect(res.body.indexed).toBe(true);
        expect(res.body.session_id).toBeDefined();
    });
    
    Key concept: io.BytesIO()
    - In Python, files are bytes
    - io.BytesIO(b"hello world") creates a fake file in memory
    - Like Buffer.from() in Node.js
    """
    # Create fake file: (filename, file_content, content_type)
    files = {"files": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    
    resp = client.post("/upload", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["indexed"] is True
    assert data["session_id"]


# TEST 2: No files should fail validation
def test_upload_no_files_validation_error(client, clear_sessions, stub_ingestor):
    """
    What it tests: Uploading without files
    Expected: FastAPI's automatic validation returns 422
    
    422 = Unprocessable Entity (validation error)
    """
    resp = client.post("/upload", files=[])
    assert resp.status_code == 422


# TEST 3: Ingestor failure should return 500
def test_upload_ingestor_failure_returns_500(client, clear_sessions, monkeypatch, tmp_dirs):
    """
    What it tests: What happens when document processing fails
    Expected: Server returns 500 error
    
    This creates a BROKEN ingestor that always crashes.
    """
    import multi_doc_chat.src.document_ingestion.data_ingestion as di
    import main
    
    # Create broken ingestor
    class Boom:
        def __init__(self, *a, **k):
            self.session_id = "sess_test"
        
        def built_retriver(self, *a, **k):
            from multi_doc_chat.exception.custom_exception import DocumentPortalException
            raise DocumentPortalException("boom", None)
    
    # Replace real ingestor with broken one
    monkeypatch.setattr(di, "ChatIngestor", Boom)
    monkeypatch.setattr(main, "ChatIngestor", Boom)
    
    files = {"files": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    resp = client.post("/upload", files=files)
    
    assert resp.status_code == 500
    assert "boom" in resp.json()["detail"].lower()
```

---

### 4️⃣ **test_data_ingestion.py** - Unit Tests

```python
import pathlib
import pytest
from langchain.schema import Document

from multi_doc_chat.src.document_ingestion.data_ingestion import (
    generate_session_id,
    ChatIngestor,
    FaissManager,
)

# TEST 1: Test session ID generation
def test_generate_session_id_format_and_uniqueness():
    """
    What it tests: Session ID generator creates unique IDs
    Expected:
    - Two calls return different IDs
    - IDs follow format: session_YYYYMMDD_HHMMSS_XXXXXXXX
    
    Node.js equivalent:
    test('should generate unique session IDs', () => {
        const a = generateSessionId();
        const b = generateSessionId();
        expect(a).not.toBe(b);
        expect(a).toMatch(/^session_\\d{8}_\\d{6}_[a-f0-9]{8}$/);
    });
    """
    a = generate_session_id()
    b = generate_session_id()
    
    assert a != b  # Different IDs
    assert a.startswith("session_") and b.startswith("session_")
    assert len(a.split("_")) == 4  # 4 parts separated by underscores


# TEST 2: Test directory structure
def test_chat_ingestor_resolve_dir_uses_session_dirs(tmp_dirs, stub_model_loader):
    """
    What it tests: ChatIngestor creates session-specific directories
    Expected:
    - temp_dir includes session_id in path
    - faiss_dir includes session_id in path
    """
    ing = ChatIngestor(
        temp_base="data", 
        faiss_base="faiss_index", 
        use_session_dirs=True
    )
    
    assert ing.session_id
    assert str(ing.temp_dir).endswith(ing.session_id)
    assert str(ing.faiss_dir).endswith(ing.session_id)


# TEST 3: Test document splitting
def test_split_chunks_respect_size_and_overlap(tmp_dirs, stub_model_loader):
    """
    What it tests: Document splitting into chunks
    Expected:
    - Long document (1200 chars) split into multiple chunks
    - Each chunk ≤ 500 chars
    
    Node.js equivalent:
    test('should split documents into chunks', () => {
        const ingestor = new ChatIngestor();
        const docs = [{ content: 'A'.repeat(1200) }];
        const chunks = ingestor.split(docs, { size: 500, overlap: 100 });
        
        expect(chunks.length).toBeGreaterThanOrEqual(2);
        expect(chunks[0].content.length).toBeLessThanOrEqual(500);
    });
    """
    ing = ChatIngestor(
        temp_base="data",
        faiss_base="faiss_index",
        use_session_dirs=True
    )
    
    # Create a long document (1200 'A's)
    docs = [Document(page_content="A" * 1200, metadata={"source": "x.txt"})]
    
    # Split with 500 char chunks, 100 char overlap
    chunks = ing._split(docs, chunk_size=500, chunk_overlap=100)
    
    assert len(chunks) >= 2  # Should create at least 2 chunks
    assert len(chunks[0].page_content) <= 500  # Chunks not too big


# TEST 4: Test FAISS index deduplication
def test_faiss_manager_add_documents_idempotent(tmp_dirs, stub_model_loader):
    """
    What it tests: Adding same document twice doesn't duplicate
    Expected:
    - First add returns count ≥ 0
    - Second add returns 0 (already exists)
    
    "Idempotent" means: doing it multiple times has same effect as doing it once
    
    Node.js equivalent:
    test('should not duplicate documents in index', () => {
        const manager = new FaissManager('faiss_index/test');
        manager.loadOrCreate(['hello', 'world']);
        
        const first = manager.addDocuments([{ content: 'hello' }]);
        const second = manager.addDocuments([{ content: 'hello' }]);
        
        expect(first).toBeGreaterThanOrEqual(0);
        expect(second).toBe(0); // Not added again
    });
    """
    fm = FaissManager(index_dir=pathlib.Path("faiss_index/test"))
    fm.load_or_create(
        texts=["hello", "world"],
        metadatas=[{"source": "a"}, {"source": "b"}]
    )
    
    docs = [Document(page_content="hello", metadata={"source": "a"})]
    
    first = fm.add_documents(docs)  # Add document
    second = fm.add_documents(docs)  # Try to add same document again
    
    assert first >= 0  # First time: document added
    assert second == 0  # Second time: already exists, not added
```

---

## 🏃 Running Tests {#running-tests}

### Basic Commands

```bash
# Run all tests
pytest

# Run specific file
pytest tests/integration/test_chat_route.py

# Run specific test
pytest tests/integration/test_chat_route.py::test_chat_success_returns_answer_and_appends_history

# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s

# Run and stop at first failure
pytest -x

# Run with coverage report
pytest --cov=multi_doc_chat --cov-report=html
```

### Node.js Comparison

| Node.js | Python |
|---------|--------|
| `npm test` | `pytest` |
| `npm test -- user.test.js` | `pytest tests/test_user.py` |
| `npm test -- --verbose` | `pytest -v` |
| `npm test -- --watch` | `pytest-watch` (needs install) |
| `npm test -- --coverage` | `pytest --cov` |

---

## 🎨 Common Testing Patterns {#patterns}

### Pattern 1: Testing API Endpoints

```python
def test_endpoint(client):
    # Arrange (setup)
    data = {"name": "Alice"}
    
    # Act (do the thing)
    response = client.post("/users", json=data)
    
    # Assert (check results)
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"
```

### Pattern 2: Testing with Mocks

```python
def test_with_mock(monkeypatch):
    # Create mock
    def fake_function():
        return "mocked value"
    
    # Replace real function with mock
    monkeypatch.setattr(module, "real_function", fake_function)
    
    # Test code that uses the mocked function
    result = module.real_function()
    assert result == "mocked value"
```

### Pattern 3: Testing Exceptions

```python
def test_raises_error():
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("Something went wrong")
    
    assert "Something went wrong" in str(exc_info.value)
```

**Node.js equivalent:**
```javascript
test('should raise error', () => {
    expect(() => {
        throw new Error('Something went wrong');
    }).toThrow('Something went wrong');
});
```

### Pattern 4: Parametrized Tests (DRY testing!)

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

**Node.js equivalent:**
```javascript
test.each([
    [1, 2],
    [2, 4],
    [3, 6],
])('should double %i to %i', (input, expected) => {
    expect(double(input)).toBe(expected);
});
```

---

## 🎓 Key Takeaways

1. **Fixtures are powerful** - They replace beforeEach/afterEach and can be composed
2. **Monkeypatch for mocking** - Similar to jest.mock() but more explicit
3. **Assert is simple** - Just use `assert` with Python expressions
4. **Test discovery is automatic** - Name files/functions correctly and pytest finds them
5. **conftest.py is magic** - Fixtures defined there are available everywhere
6. **Integration vs Unit** - Separate folder structure keeps tests organized

---

## 📚 Further Reading

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures Guide](https://docs.pytest.org/en/stable/fixture.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Monkeypatch Guide](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)

---

## 💡 Quick Reference

```python
# Import test tools
import pytest
from fastapi.testclient import TestClient

# Create fixture
@pytest.fixture
def my_fixture():
    return "value"

# Use fixture in test
def test_something(my_fixture):
    assert my_fixture == "value"

# Mock/patch something
def test_with_mock(monkeypatch):
    monkeypatch.setattr(module, "function", lambda: "mocked")

# Test exceptions
def test_error():
    with pytest.raises(ValueError):
        raise ValueError("error")

# Parametrize tests
@pytest.mark.parametrize("x,y", [(1, 2), (3, 4)])
def test_params(x, y):
    assert x < y
```

---

**Happy Testing! 🎉**
