import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
import os

from chunking import MODEL_NAME, dividir, leer_docs

DSN = os.getenv("RAG_DSN", "postgresql://rag:rag@localhost:5433/ragdb")


def main():
    model = SentenceTransformer(MODEL_NAME)

    filas = []
    for doc in leer_docs():
        for i, contenido in enumerate(dividir(doc["texto"])):
            filas.append((doc["fuente"], doc["url"], doc["titulo"], i, contenido))

    vectores = model.encode(
        [f"passage: {f[2]}\n{f[4]}" for f in filas], normalize_embeddings=True
    )

    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        conn.execute("DROP TABLE IF EXISTS chunks")
        conn.execute(
            """
            CREATE TABLE chunks (
                id SERIAL PRIMARY KEY,
                fuente TEXT,
                url TEXT,
                titulo TEXT,
                chunk_index INT,
                contenido TEXT,
                embedding vector(768)
            )
            """
        )
        with conn.cursor() as cur:
            for fila, vec in zip(filas, vectores):
                cur.execute(
                    """
                    INSERT INTO chunks
                        (fuente, url, titulo, chunk_index, contenido, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (*fila, vec),
                )
    print("Chunks insertados:", len(filas))


if __name__ == "__main__":
    main()