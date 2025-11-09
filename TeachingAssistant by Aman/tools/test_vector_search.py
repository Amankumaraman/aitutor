# tools/test_vector_search.py
from app.memory.vector_store import vector_store

def main():
    res = vector_store.search("gravity", k=3)
    print("Search results:", res)

if __name__ == "__main__":
    main()
