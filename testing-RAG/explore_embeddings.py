# From root: python ./testing-RAG/explore_embeddings.py

import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "The cat sat on the mat",
    "A kitten was resting on the rug",
    "The stock market crashed yesterday",
    "Financial markets experienced a sharp decline",
    "I enjoy eating pizza on Fridays",
    "I like sitting on the bank and watching the sunset",
    "Investment banks serve as crucial financial intermediaries that facilitate capital markets by underwriting securities offerings, providing merger and acquisition advisory services, conducting proprietary trading operations, managing institutional client portfolios, offering sophisticated risk management solutions, and delivering comprehensive research and analysis to institutional investors, corporations, and governments seeking to raise capital, restructure operations, or navigate complex financial transactions in global markets."
]

embeddings = model.encode(sentences)

print(f"Number of sentences: {len(embeddings)}")
print(f"Embedding dimension: {embeddings.shape[1]}")
print(f"First embedding (first 10 values): {embeddings[0][:10]}")
print(f"Embedding norm: {np.linalg.norm(embeddings[0]):.4f}")

def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


print("\nPairwise cosine similarities:")
print("-" * 50)
for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        sim = cosine_similarity(embeddings[i], embeddings[j])
        print(f"{sim:.4f}  |  '{sentences[i][:40]}' vs '{sentences[j][:40]}'")

# ADD QUERY HERE
query = "What happened in the financial markets?"
query_embedding = model.encode([query])[0]

print(f"\nQuery: '{query}'")
print("Similarities to each sentence:")
print("-" * 50)

similarities = []
for i, sentence in enumerate(sentences):
    sim = cosine_similarity(query_embedding, embeddings[i])
    similarities.append((sim, sentence))
    print(f"  {sim:.4f}  |  '{sentence}'")

# Sort by similarity (highest first)
similarities.sort(reverse=True)
print(f"\nBest match: '{similarities[0][1]}'")