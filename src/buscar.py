import sys

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from chunking import MODEL_NAME

DSN = "postgresql://rag:rag@localhost:5433/ragdb"
_model = None


def buscar_chunks(pregunta, k=4):
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    vec = _model.encode("query: " + pregunta, normalize_embeddings=True)
    with psycopg.connect(DSN) as conn:
        register_vector(conn)
        return conn.execute(
            """
            SELECT titulo, url, contenido, embedding <=> %s AS distancia
            FROM chunks
            ORDER BY distancia
            LIMIT %s
            """,
            (vec, k),
        ).fetchall()


if __name__ == "__main__":
    for titulo, url, contenido, dist in buscar_chunks(" ".join(sys.argv[1:]), 3):
        print(f"\n[{dist:.3f}] {titulo}\n{url}\n{contenido[:300]}")