"""
test_embedding.py

Temporary test script to verify Gemini embedding generation.
"""

from app.services.embedding_service import get_embedding


def test():
    sample_text = "The checkout page is very slow on mobile"
    print(f"Generating embedding for text: '{sample_text}'...")

    embedding = get_embedding(sample_text)

    print(f"\nSuccess! Embedding generated.")
    print(f"Total vector length (dimensions): {len(embedding)}")
    print(f"First 5 vector values: {embedding[:5]}")


if __name__ == "__main__":
    test()
