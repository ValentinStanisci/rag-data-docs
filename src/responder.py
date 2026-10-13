import sys

import ollama

from buscar import buscar_chunks

MODELO = "llama3.2:3b"

UMBRAL = 0.25  # distancia máxima aceptada para el mejor fragmento
MAX_CARACTERES = 500

SISTEMA = (
    "Sos un asistente que responde preguntas sobre documentación técnica de "
    "dbt y Airflow. Respondé en español, usando SOLO la información de los "
    "fragmentos provistos. REGLA OBLIGATORIA: al final de cada oración, "
    "indicá la fuente con su número entre corchetes, por ejemplo [1] o [2]. "
    "Si los fragmentos NO contienen la respuesta, respondé únicamente con la "
    "palabra SIN_INFO, sin agregar nada más ni usar conocimiento propio."
)


def responder(pregunta):
    pregunta = pregunta.strip()
    if not pregunta:
        return "Escribí una pregunta.", ""
    if len(pregunta) > MAX_CARACTERES:
        return f"La pregunta es demasiado larga (máximo {MAX_CARACTERES} caracteres).", ""

    chunks = buscar_chunks(pregunta, k=4)
    if not chunks or chunks[0][3] > UMBRAL:
        return (
            "No tengo información sobre eso en la documentación indexada "
            "(dbt y Airflow).",
            "",
        )

    numeros = {}  # url -> número de fuente (una por página)
    for _, url, _, _ in chunks:
        numeros.setdefault(url, len(numeros) + 1)

    contexto = "\n\n".join(
        f"[{numeros[url]}] {titulo}\n{contenido}"
        for titulo, url, contenido, _ in chunks
    )
    resp = ollama.chat(
        model=MODELO,
        messages=[
            {"role": "system", "content": SISTEMA},
            {
                "role": "user",
                "content": (
                    f"Fragmentos:\n{contexto}\n\nPregunta: {pregunta}\n\n"
                    "Recordá: terminá cada oración con la fuente, por ejemplo [1]."
                ),
            },
        ],
        options={"temperature": 0.1, "num_ctx": 4096},
    )
    fuentes = "\n".join(f"[{n}] {url}" for url, n in numeros.items())
    texto = resp.message.content
    if "SIN_INFO" in texto:
        return (
            "No tengo información sobre eso en la documentación indexada "
            "(dbt y Airflow).",
            "",
        )
    return texto, fuentes


if __name__ == "__main__":
    texto, fuentes = responder(" ".join(sys.argv[1:]))
    print(texto)
    if fuentes:
        print("\nFuentes:\n" + fuentes)