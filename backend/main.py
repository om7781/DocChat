import os
import uuid
import shutil
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError


from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Path to locally downloaded Qwen2.5-1.5B-Instruct in user's HuggingFace cache
LOCAL_QWEN_SNAPSHOT = Path(r"E:\Huggingface_cache\hub\models--Qwen--Qwen2.5-1.5B-Instruct\snapshots\989aa7980e4cf806f80c7fef2b1adb7bc71aa306")

# Singleton for lazy loading local model into memory only once
_LOCAL_QWEN_MODEL = None
_LOCAL_QWEN_TOKENIZER = None

def get_local_qwen():
    global _LOCAL_QWEN_MODEL, _LOCAL_QWEN_TOKENIZER
    if _LOCAL_QWEN_MODEL is None:
        print("[Local Model] Loading Qwen2.5-1.5B tokenizer from local cache...")
        _LOCAL_QWEN_TOKENIZER = AutoTokenizer.from_pretrained(str(LOCAL_QWEN_SNAPSHOT), local_files_only=True)
        print("[Local Model] Loading Qwen2.5-1.5B model in bfloat16 on CPU...")
        _LOCAL_QWEN_MODEL = AutoModelForCausalLM.from_pretrained(
            str(LOCAL_QWEN_SNAPSHOT),
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            local_files_only=True,
        )
        print("[Local Model] Qwen2.5-1.5B is ready for offline inference!")
    return _LOCAL_QWEN_TOKENIZER, _LOCAL_QWEN_MODEL


# ─── Local Qwen LangChain LLM ──────────────────────────────────────────────────
class LocalQwenLLM(LLM):
    """
    LangChain LLM wrapper for locally cached Qwen 2.5-1.5B-Instruct model.
    Runs 100% offline on CPU using bfloat16. No HuggingFace API key or credits needed.
    """
    max_new_tokens: int = Field(default=384)
    temperature: float = Field(default=0.3)

    @property
    def _llm_type(self) -> str:
        return "local_qwen_1.5b_instruct"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        tokenizer, model = get_local_qwen()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers questions strictly based on the provided document context. "
                    "If the answer is not in the context, say: 'I couldn't find that information in the uploaded document.'"
                ),
            },
            {"role": "user", "content": prompt},
        ]
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(input_text, return_tensors="pt")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
        response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return response.strip()


# ─── Cloud Hugging Face LangChain LLM (Fallback) ──────────────────────────────
class HuggingFaceChatLLM(LLM):
    """
    LangChain LLM wrapper for Hugging Face Inference API.
    Uses InferenceClient with provider="auto".
    """
    model_id: str = Field(default=os.getenv("HF_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct"))
    provider: str = Field(default="auto")
    api_token: str = Field(default="")
    max_new_tokens: int = Field(default=512)
    temperature: float = Field(default=0.3)

    @property
    def _llm_type(self) -> str:
        return "huggingface_chat_llm"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        client = InferenceClient(provider=self.provider, token=self.api_token)
        try:
            response = client.chat_completion(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except HfHubHTTPError as e:
            err_str = str(e)
            if "402" in err_str or "Payment Required" in err_str:
                fallback = self._extract_context_answer(prompt)
                return (
                    f"[Hugging Face Notice: Monthly inference credits exhausted on this account]\n\n"
                    f"**Answer based on document context:**\n{fallback}"
                )
            raise e

    def _extract_context_answer(self, prompt: str) -> str:
        if "Document Context:" in prompt and "Question:" in prompt:
            parts = prompt.split("Document Context:")
            if len(parts) > 1:
                ctx_and_q = parts[1].split("Question:")
                context = ctx_and_q[0].strip()
                question = ctx_and_q[1].split("Answer:")[0].strip() if len(ctx_and_q) > 1 else ""
                q_words = set(w.lower() for w in question.split() if len(w) > 3)
                lines = [l.strip() for l in context.split("\n") if l.strip()]
                scored = []
                for line in lines:
                    score = sum(1 for w in q_words if w in line.lower())
                    if score > 0:
                        scored.append((score, line))
                if scored:
                    scored.sort(key=lambda x: x[0], reverse=True)
                    return "\n".join(item[1] for item in scored[:3])
                return context[:500]
        return "Information found in the document."


def get_llm():
    """
    Returns LocalQwenLLM if the local snapshot exists in E:/Huggingface_cache,
    otherwise falls back to HuggingFaceChatLLM using the Hugging Face API.
    """
    use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() in ("true", "1", "yes")
    if use_local and LOCAL_QWEN_SNAPSHOT.exists():
        print("[DocChat] Using local offline model: Qwen2.5-1.5B-Instruct")
        return LocalQwenLLM()

    print("[DocChat] Using Hugging Face Inference API (provider='auto')")
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    model_name = os.getenv("HF_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")
    return HuggingFaceChatLLM(
        model_id=model_name,
        provider="auto",
        api_token=hf_token,
        temperature=0.3,
        max_new_tokens=512,
    )

load_dotenv()

app = FastAPI(title="DocChat API")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory session store ───────────────────────────────────────────────────
# { session_id: { "chain": chain, "filename": str } }
sessions: dict = {}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".csv", ".md"}

# ─── Embeddings (loaded once at startup) ──────────────────────────────────────
print("Loading embedding model (this may take a moment the first time)...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
print("Embedding model ready.")



# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_loader(file_path: str, extension: str):
    """Return the appropriate LangChain document loader."""
    loaders = {
        ".pdf":  lambda: PyPDFLoader(file_path),
        ".txt":  lambda: TextLoader(file_path, encoding="utf-8"),
        ".docx": lambda: Docx2txtLoader(file_path),
        ".csv":  lambda: CSVLoader(file_path, encoding="utf-8"),
        ".md":   lambda: TextLoader(file_path, encoding="utf-8"),  # MD is plain text
    }
    if extension not in loaders:
        raise ValueError(f"Unsupported file type: {extension}")
    return loaders[extension]()


def build_chain(file_path: str, extension: str):
    """Load → split → embed → build ConversationalRetrievalChain."""
    loader = get_loader(file_path, extension)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    if not chunks:
        raise ValueError("Document appears to be empty or could not be parsed.")

    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = get_llm()

    qa_prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template=(
            "You are a helpful assistant that answers questions strictly based on "
            "the provided document context.\n"
            "If the answer is not found in the context, say: "
            "\"I couldn't find that information in the uploaded document.\"\n\n"
            "Chat History:\n{chat_history}\n\n"
            "Document Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        ),
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": qa_prompt},
    )

    return chain


# ─── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[str]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document and return a session_id for chat."""
    extension = Path(file.filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{extension}'. "
                f"Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    session_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{session_id}{extension}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chain = build_chain(str(save_path), extension)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

    sessions[session_id] = {"chain": chain, "filename": file.filename}

    return {
        "session_id": session_id,
        "filename": file.filename,
        "message": "File processed successfully!",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Ask a question about the uploaded document."""
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload a file first.",
        )

    try:
        result = session["chain"].invoke({"question": req.question})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    answer = result.get("answer", "")
    source_docs = result.get("source_documents", [])

    # Collect unique source references (page number or filename)
    seen = set()
    sources = []
    for doc in source_docs:
        ref = doc.metadata.get("source") or doc.metadata.get("page")
        label = str(ref) if ref is not None else ""
        if label and label not in seen:
            seen.add(label)
            sources.append(label)

    return ChatResponse(answer=answer, session_id=req.session_id, sources=sources)


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clear a session and delete the uploaded file."""
    sessions.pop(session_id, None)
    for ext in SUPPORTED_EXTENSIONS:
        p = UPLOAD_DIR / f"{session_id}{ext}"
        p.unlink(missing_ok=True)
    return {"message": "Session cleared."}


@app.get("/health")
async def health():
    return {"status": "ok"}
