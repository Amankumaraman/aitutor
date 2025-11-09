from app.memory.vector_store import vector_store

# Test the vector store retrieval
results = vector_store.search("gravity", k=3)
print("\nSearch Results for 'gravity':")
print("----------------------------")
for i, (score, text, metadata) in enumerate(results, 1):
    print(f"\n{i}. Score: {score:.4f}")
    print(f"Session: {metadata.get('session_id')}")
    print(f"Text: {text[:200]}...")