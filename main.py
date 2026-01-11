from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from multi_doc_chat.model import UploadResponse, ChatRequest, ChatResponse
from multi_doc_chat.src.document_ingestion.data_ingestion import ChatIngestor
from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG
from langchain_core.messages import HumanMessage, AIMessage
from multi_doc_chat.exception.custom_exception import DocumentPortalException
from multi_doc_chat.utils.document_ops import FastAPIFileAdapter


# ----------------------------
# FastAPI initialization
# ----------------------------
app = FastAPI(title="MultiDocChat", version="0.1.0")

# CORS (optional for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Static and templates
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static") # serve static files
templates = Jinja2Templates(directory=str(templates_dir)) # help to bind dynamic data to html templates


# In-memory session store for chat history
SESSIONS: Dict[str, List[dict]] = {}



@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_model=UploadResponse)
async def upload_file(files: List[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    try:
        # wrap FastAPI UploadFile to preserve filename/extension and pass a read buffer

        wrapped_files = [FastAPIFileAdapter(file) for file in files]
        ingestor = ChatIngestor(use_session_dirs=True)
        session_id = ingestor.session_id

        # save, load, split, embed, and write FAISS index

        ingestor.built_retriver(uploaded_files=wrapped_files)
       
       # Initialize empty chat history for this session
        SESSIONS[session_id] = []

        return UploadResponse(session_id=session_id, indexed=True, message="Files uploaded and indexed successfully.")
    except DocumentPortalException as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document failed with error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat_with_documents(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id
    user_message = req.message
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid or expired session ID, Re-upload documents to start a new session.")
    
    if not user_message or user_message.strip() == "":
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Initialize ConversationalRAG with the session's index
        rag = ConversationalRAG(session_id=session_id)
        index_path= f"faiss_index/{session_id}"
        rag.load_retriever_from_faiss(index_path=index_path)

        # Use simple in-memory history and convert to BaseMessage list
        simple = SESSIONS.get(session_id, [])
        lc_history = []

        for msg in simple:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_history.append(AIMessage(content=content))

        answer = rag.invoke(user_input=user_message, chat_history=lc_history)

       # Update history
        simple.append({"role": "user", "content": user_message})
        simple.append({"role": "assistant", "content": answer})
        SESSIONS[session_id] = simple

        return ChatResponse(answer=answer)
    except DocumentPortalException as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed with error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)