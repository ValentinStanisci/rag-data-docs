import json

import boto3
from sentence_transformers import SentenceTransformer

BUCKET = "rag-data-docs"
PREFIX = "rag-docs/raw/"
MODEL_NAME = "intfloat/multilingual-e5-base"
CHUNK_SIZE = 1000
OVERLAP = 200

s3 = boto3.client("s3")


def leer_docs():
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
        for obj in page.get("Contents", []):
            body = s3.get_object(Bucket=BUCKET, Key=obj["Key"])["Body"].read()
            yield json.loads(body)


def dividir(texto, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks, actual = [], ""
    for linea in texto.split("\n"):
        if actual and len(actual) + len(linea) + 1 > size:
            chunks.append(actual.strip())
            actual = actual[-overlap:]
        actual += linea + "\n"
    if actual.strip():
        chunks.append(actual.strip())
    return chunks


if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)

    todos = []
    for doc in leer_docs():
        for i, contenido in enumerate(dividir(doc["texto"])):
            todos.append(
                {
                    "url": doc["url"],
                    "titulo": doc["titulo"],
                    "chunk_index": i,
                    "contenido": contenido,
                }
            )

    print("Chunks:", len(todos))

    vectores = model.encode(
        ["passage: " + c["contenido"] for c in todos],
        normalize_embeddings=True,
    )
    print("Shape:", vectores.shape)
    print("--- Primer chunk ---")
    print(todos[0]["contenido"][:300])