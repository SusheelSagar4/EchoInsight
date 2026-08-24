"""
test_vector_store.py

Diagnostic script to inspect ChromaDB 'feedback_memory' collection count and stored items.
"""

from app.services.vector_store_service import collection


def test():
    print("--- ChromaDB 'feedback_memory' Collection Status ---")

    # 1. Print total items stored
    count = collection.count()
    print(f"Total items currently stored: {count}")

    # 2. Retrieve up to first 5 items
    if count > 0:
        items = collection.get(limit=5)
        print("\nFirst 5 stored items:")
        ids = items.get("ids", [])
        documents = items.get("documents", [])
        metadatas = items.get("metadatas", [])

        for i, (item_id, doc, meta) in enumerate(zip(ids, documents, metadatas), 1):
            print(f"\n[{i}] ID: {item_id}")
            print(f"    Document: {doc}")
            print(f"    Metadata: {meta}")
    else:
        print("\nThe collection is currently empty (0 items).")


if __name__ == "__main__":
    test()
