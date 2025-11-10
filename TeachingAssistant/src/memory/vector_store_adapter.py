# TeachingAssistant/src/memory/vector_store_adapter.py
import os
from typing import List, Dict, Any

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except Exception:
    chromadb = None
    SentenceTransformer = None

class VectorStoreAdapter:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_chroma: bool = False, persist_dir: str = "./.chroma"):
        self.use_chroma = use_chroma and chromadb is not None and SentenceTransformer is not None
        self.model_name = model_name
        self.persist_dir = persist_dir
        if self.use_chroma:
            self.client = chromadb.Client()
            self.model = SentenceTransformer(model_name)
            try:
                self.col = self.client.get_collection("conversation")
            except Exception:
                self.col = self.client.create_collection("conversation")
        else:
            self._docs = []
            self._embs = []

    def _embed(self, texts: List[str]):
        if self.use_chroma:
            return self.model.encode(texts).tolist()
        else:
            # cheap mock embedding: [length, checksum]
            return [[float(len(t)), sum(ord(c) for c in t) % 997] for t in texts]

    def add_documents(self, docs: List[Dict[str, Any]]):
        texts = [d["text"] for d in docs]
        embs = self._embed(texts)
        if self.use_chroma:
            ids = [d["id"] for d in docs]
            metadatas = [d.get("metadata", {}) for d in docs]
            self.col.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embs)
        else:
            for d,e in zip(docs, embs):
                self._docs.append(d)
                self._embs.append(e)

    def search_similar(self, query: str, limit: int = 3) -> Dict[str, Any]:
        q_emb = self._embed([query])[0]
        if self.use_chroma:
            results = self.col.query(query_embeddings=[q_emb], n_results=limit)
            return {"documents": results.get("documents", []), "metadatas": results.get("metadatas", []), "distances": results.get("distances", [])}
        else:
            from math import sqrt
            def dist(a,b): return sqrt(sum((x-y)**2 for x,y in zip(a,b)))
            scored = []
            for doc, emb in zip(self._docs, self._embs):
                scored.append((doc, dist(q_emb, emb)))
            scored.sort(key=lambda x: x[1])
            docs = [[s[0]["text"] for s in scored[:limit]]]
            metadatas = [[s[0].get("metadata", {}) for s in scored[:limit]]]
            distances = [[s[1] for s in scored[:limit]]]
            return {"documents": docs, "metadatas": metadatas, "distances": distances}
