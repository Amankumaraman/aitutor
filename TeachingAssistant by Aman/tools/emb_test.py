# tools/emb_test.py
from app.memory.vector_store import MODEL

def main():
    print("Model:", MODEL)
    v = MODEL.encode(["test sentence"])[0]
    print("Vector length:", len(v))
    print("First dims:", v[:6])

if __name__ == "__main__":
    main()
