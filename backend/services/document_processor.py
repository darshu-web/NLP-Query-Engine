import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pdfplumber
from docx import Document
from typing import List
import json
import tempfile
import csv
import requests

_TMP_DIR = tempfile.gettempdir()
INDEX_DIR = os.path.join(_TMP_DIR, "vec_index")
METADATA_PATH = os.path.join(_TMP_DIR, "vec_metadata.json")


def extract_text_from_pdf(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)


def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paras)


def extract_text_from_csv(path: str) -> str:
    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                lines.append(", ".join([c.strip() for c in row if str(c).strip()]))
        return "\n".join(lines)
    except Exception:
        # fallback to raw read
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def read_file_text(path: str) -> str:
    ext = path.lower().split(".")[-1]
    if ext == "pdf":
        return extract_text_from_pdf(path)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(path)
    elif ext in ("csv",):
        return extract_text_from_csv(path)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


class DocumentProcessor:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # Embedding backend selection: Gorq HTTP API if key provided, else local model
        self.groq_api_key = os.getenv("GORQ_API_KEY") or os.getenv("GROQ_API_KEY")
        self.groq_embed_url = os.getenv("GORQ_EMBED_URL", os.getenv("GROQ_EMBED_URL", "https://api.groq.com/openai/v1/embeddings"))
        self.groq_model = os.getenv("GORQ_EMBED_MODEL", os.getenv("GROQ_EMBED_MODEL", "text-embedding-3-small"))

        self.model = None
        if not self.groq_api_key:
            # ✅ local fallback (no auth)
            self.model = SentenceTransformer(model_name, use_auth_token=False)
            print(f"[Embedding] Using local SentenceTransformer: {model_name}")
        else:
            print(f"[Embedding] Using Gorq API at {self.groq_embed_url} with model {self.groq_model}")

        self.index = None
        self.metadata = []

        if os.path.exists(INDEX_DIR + "/index.faiss"):
            self._load_index()

        self.status = {}

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        if self.groq_api_key:
            # Gorq/Groq-compatible embeddings API (OpenAI-style)
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
            }
            payload = {"input": texts, "model": self.groq_model}
            resp = requests.post(self.groq_embed_url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            vectors = [np.array(item.get("embedding", []), dtype=np.float32) for item in data.get("data", [])]
            if not vectors:
                return np.zeros((len(texts), 384), dtype=np.float32)
            arr = np.vstack(vectors).astype("float32")
        else:
            # Local model
            arr = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        # L2-normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return arr / norms

    def dynamic_chunking(self, content: str, doc_type: str) -> List[str]:
        paras = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        max_chars = 250 * 4
        for p in paras:
            if len(current) + len(p) + 1 <= max_chars:
                current = (current + "\n\n" + p).strip()
            else:
                if current:
                    chunks.append(current)
                current = p
        if current:
            chunks.append(current)
        return chunks

    def _init_index(self, dim: int):
        self.index = faiss.IndexFlatIP(dim)
        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR, exist_ok=True)

    def _save_index(self):
        if self.index is None:
            return
        faiss.write_index(self.index, INDEX_DIR + "/index.faiss")
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f)

    def _load_index(self):
        if not os.path.exists(INDEX_DIR + "/index.faiss"):
            return
        self.index = faiss.read_index(INDEX_DIR + "/index.faiss")
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def process_documents(self, file_paths: List[str], job_id: str = None):
        if job_id is None:
            job_id = "job_local"
        self.status[job_id] = {"total": len(file_paths), "processed": 0, "vectors": 0, "errors": 0, "done": False}

        global_vectors = []
        for path in file_paths:
            try:
                text = read_file_text(path)
                if not text.strip():
                    self.status[job_id]["errors"] += 1
                    self.status[job_id]["processed"] += 1
                    continue
                doc_type = path.split(".")[-1]
                chunks = self.dynamic_chunking(text, doc_type)

                if not chunks:
                    self.status[job_id]["processed"] += 1
                    continue

                embs = self._embed_texts(chunks)

                for i, emb in enumerate(embs):
                    self.metadata.append({
                        "source": os.path.basename(path),
                        "chunk_id": f"{os.path.basename(path)}_chunk_{i}",
                        "text": chunks[i]
                    })
                    global_vectors.append(emb)
                self.status[job_id]["vectors"] += int(len(embs))
            except Exception:
                self.status[job_id]["errors"] += 1
            finally:
                self.status[job_id]["processed"] += 1

        if global_vectors:
            arr = np.vstack(global_vectors).astype("float32")
            dim = arr.shape[1]
            if self.index is None:
                self._init_index(dim)
            # guard against dimension mismatch by recreating index
            if self.index.d != dim:
                self._init_index(dim)
                self.metadata = []
            self.index.add(arr)
            self._save_index()

        self.status[job_id]["done"] = True

    def get_status(self, job_id: str):
        return self.status.get(job_id, {"total": 0, "processed": 0, "vectors": 0, "errors": 0, "done": False})

    def _keyword_overlap_score(self, query: str, text: str) -> float:
        q_words = {w.lower().strip(",.()\"'`") for w in query.split() if w.strip()}
        t_words = {w.lower().strip(",.()\"'`") for w in text.split() if w.strip()}
        if not q_words or not t_words:
            return 0.0
        overlap = q_words.intersection(t_words)
        return len(overlap) / (len(q_words) ** 0.5)

    def search(self, query: str, top_k: int = 5):
        if self.index is None:
            # attempt to load existing index if available
            self._load_index()
            if self.index is None:
                return []

        q_emb = self._embed_texts([query])

        D, I = self.index.search(q_emb.astype("float32"), max(1, top_k * 2))

        hits = []
        for idx, score in zip(I[0], D[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            rerank = self._keyword_overlap_score(query, meta["text"])  # simple lexical boost
            hits.append({
                "score": float(score) + 0.2 * float(rerank),
                "text": meta["text"],
                "source": meta["source"],
                "chunk_id": meta["chunk_id"]
            })
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:top_k]
