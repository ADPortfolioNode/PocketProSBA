import re
import math
from collections import Counter

class SimpleEmbeddingFunction:
    """Simple embedding function that works without external dependencies"""
    def __call__(self, texts):
        embeddings = []
        all_words = set()
        text_words = []

        for text in texts:
            words = re.findall(r"\b\w+\b", str(text).lower())
            text_words.append(words)
            all_words.update(words)

        vocab = sorted(list(all_words))[:384]

        for words in text_words:
            word_counts = Counter(words)
            total_words = len(words)
            embedding = []
            for word in vocab:
                tf = word_counts.get(word, 0) / max(total_words, 1)
                embedding.append(float(tf))
            while len(embedding) < 384:
                embedding.append(0.0)
            embeddings.append(embedding[:384])

        return embeddings


class SimpleVectorStore:
    """Simple in-memory vector store for RAG functionality"""
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
        self.embedding_function = SimpleEmbeddingFunction()

    def add_document(self, doc_id, text, metadata=None):
        self.documents[doc_id] = {'text': text, 'metadata': metadata or {}}
        embedding = self.embedding_function([text])[0]
        self.embeddings[doc_id] = embedding
        return doc_id

    def search(self, query, n_results=5):
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
        query_embedding = self.embedding_function([query])[0]
        similarities = []
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc_id, similarity))
        similarities.sort(key=lambda x: x[1], reverse=True)
        top = similarities[:n_results]
        documents, metadatas, distances, ids = [], [], [], []
        for doc_id, sim in top:
            doc = self.documents[doc_id]
            documents.append(doc['text'])
            metadatas.append(doc['metadata'])
            distances.append(1.0 - sim)
            ids.append(doc_id)
        return {'documents': [documents], 'metadatas': [metadatas], 'distances': [distances], 'ids': [ids]}

    def delete_document(self, doc_id):
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.embeddings[doc_id]
            return True
        return False

    def count(self):
        return len(self.documents)

    def get_all_documents(self):
        return [{'id': doc_id, 'text': doc['text'], 'metadata': doc['metadata']} for doc_id, doc in self.documents.items()]

    def _cosine_similarity(self, vec1, vec2):
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)
