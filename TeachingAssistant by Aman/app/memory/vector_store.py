# app/memory/vector_store.py
import os
import pickle
import numpy as np
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# Try to import faiss and sentence-transformers
try:
    import faiss
    HAS_FAISS = True
except Exception:
    HAS_FAISS = False

from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer(MODEL_NAME)

class VectorStore:
    def __init__(self, dim=384):
        self.meta = []
        self.dim = dim
        if HAS_FAISS:
            self.index = faiss.IndexFlatL2(dim)
        else:
            self.index = None
            self.vectors = []

    def add(self, text, metadata):
        # compute embedding (blocking)
        vec = MODEL.encode([text])[0].astype("float32")
        if HAS_FAISS:
            self.index.add(np.array([vec]))
        else:
            self.vectors.append(vec)
        # store metadata (text + metadata)
        self.meta.append({"text": text, **(metadata or {})})

    def search(self, query, k=3):
        qv = MODEL.encode([query])[0].astype("float32")
        if HAS_FAISS and getattr(self.index, "ntotal", 0) > 0:
            D, I = self.index.search(np.array([qv]), k)
            return [self.meta[i] for i in I[0] if i < len(self.meta)]
        elif not HAS_FAISS and len(getattr(self, "vectors", [])) > 0:
            sims = np.dot(np.array(self.vectors), qv)
            top = np.argsort(-sims)[:k]
            return [self.meta[i] for i in top]
        else:
            return []

    def save(self, path_dir="data"):
        os.makedirs(path_dir, exist_ok=True)
        if HAS_FAISS:
            faiss.write_index(self.index, f"{path_dir}/faiss.index")
        with open(f"{path_dir}/meta.pkl", "wb") as f:
            pickle.dump(self.meta, f)

    def load(self, path_dir="data"):
        try:
            with open(f"{path_dir}/meta.pkl", "rb") as f:
                self.meta = pickle.load(f)
            if HAS_FAISS:
                self.index = faiss.read_index(f"{path_dir}/faiss.index")
            else:
                self.vectors = [MODEL.encode([m["text"]])[0].astype("float32") for m in self.meta]
        except FileNotFoundError:
            pass

# Singleton
vector_store = VectorStore()
vector_store.load()
