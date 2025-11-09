# tools/fast_retrieval_demo.py
import asyncio
from app.memory.session_store import get_recent
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

async def run():
    sess = "testsession"
    turns = await get_recent(sess, n=200)
    docs = [t["text"] for t in turns if t["speaker"] == "tutor"]
    if not docs:
        print("No tutor docs found in Redis. Run a test conversation first.")
        return
    vectorizer = TfidfVectorizer().fit(docs)
    X = vectorizer.transform(docs)
    query = input("Enter query: ")
    qv = vectorizer.transform([query])
    sims = (X @ qv.T).toarray().squeeze()
    idx = np.argsort(-sims)[:5]
    for i in idx:
        if sims[i] > 0:
            print(f"SCORE: {sims[i]:.3f} DOC: {docs[i]}\n")

if __name__ == "__main__":
    asyncio.run(run())
