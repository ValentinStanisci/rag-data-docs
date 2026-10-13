# rag-data-docs

Asistente RAG que responde preguntas en español sobre la documentación de **dbt** y **Airflow**, indicando de qué páginas salió la información. El foco está en el pipeline de datos que lo alimenta: ingesta incremental, orquestación, búsqueda vectorial y evaluación medida.

## Arquitectura

```
Docs web ──> ingest.py ──> S3 (rag-docs/raw/) ──> chunking + embeddings ──> pgvector
              (hash)                                (multilingual-e5-base)       │
                                                                                 ▼
                          respuesta + fuentes <── responder.py <── buscar.py (top 4)
                                                   (guardrails + Ollama)

Airflow (DAG rag_docs_ingesta): ingestar -> ¿hubo cambios? -> reindexar
```

- **Ingesta incremental:** cada página se guarda en S3 con un hash de su contenido. Si el hash no cambió, no se reprocesa.
- **DAG de Airflow:** tres tareas; si no hay páginas nuevas o modificadas, el reindexado se saltea.
- **Búsqueda:** cada chunk se vectoriza junto con el título de su página y se consulta por distancia coseno en pgvector.
- **Generación:** `llama3.2:3b` local con Ollama, sin costo de API.

## Stack

Python 3.12 · AWS S3 · PostgreSQL + pgvector (Docker) · sentence-transformers (`intfloat/multilingual-e5-base`) · Ollama (`llama3.2:3b`) · Apache Airflow 3.3 (Docker)

## Estructura

| Archivo | Qué hace |
|---|---|
| `src/ingest.py` | Descarga páginas y las guarda en S3 solo si cambiaron |
| `src/chunking.py` | Lee de S3, divide en chunks y define el modelo de embeddings |
| `src/indexar.py` | Calcula embeddings y recrea la tabla `chunks` en pgvector |
| `src/buscar.py` | Busca los fragmentos más cercanos a una pregunta |
| `src/responder.py` | Guardrails + generación de la respuesta con fuentes |
| `src/evaluar.py` | Evalúa la búsqueda con 17 preguntas (hit@k y MRR) |
| `src/distancias.py` | Mide distancias para calibrar el umbral |
| `airflow/` | Dockerfile, compose y DAG `rag_docs_ingesta` |
| `docker-compose.yml` | Postgres con pgvector |

## Cómo correrlo

Requisitos: Python 3.12, Docker Desktop, credenciales de AWS configuradas (`aws configure`), un bucket de S3 propio y [Ollama](https://ollama.com) instalado.

```bash
git clone https://github.com/ValentinStanisci/rag-data-docs.git
cd rag-data-docs
pip install -r requirements.txt
ollama pull llama3.2:3b
docker compose up -d
```

1. En `src/ingest.py` y `src/chunking.py`, cambiá `BUCKET` por el nombre de tu bucket.
2. Ingestá e indexá:

```bash
python src/ingest.py
python src/indexar.py
```

3. Preguntá:

```bash
python src/responder.py "¿Cómo funcionan los modelos incrementales en dbt?"
```

4. Evaluá la búsqueda:

```bash
python src/evaluar.py
```

### Airflow (opcional)

```bash
cd airflow
mkdir logs config plugins
echo AIRFLOW_UID=50000> .env
docker compose up airflow-init
docker compose up -d
```

La interfaz queda en http://localhost:8080. El compose monta `../src` y tu carpeta de credenciales de AWS (`${USERPROFILE}/.aws`, en Windows; en Linux o Mac cambiala por `${HOME}/.aws`).

## Evaluación de la búsqueda

17 preguntas en español, cada una con la página de la documentación donde está la respuesta. Se mide solo la recuperación, sin el LLM.

| Configuración | hit@1 | hit@3 | hit@4 | MRR |
|---|---|---|---|---|
| e5-small, sin título de página | 82% | 82% | 82% | 0.82 |
| e5-small, con título de página | 76% | 88% | 94% | 0.82 |
| e5-base, con título de página | 82% | 100% | 100% | 0.89 |

El sistema le pasa al LLM los 4 mejores fragmentos, por eso hit@4 es la métrica que más importa. Con 17 preguntas, cada una pesa casi 6 puntos, y las páginas "correctas" las etiqueté a mano, así que algunas diferencias en hit@1 pueden ser ruido o etiquetas estrictas.

## Guardrails

- **SQL injection:** la pregunta nunca se concatena en una consulta; viaja como parámetro.
- **Validaciones:** pregunta vacía y largo máximo de 500 caracteres.
- **Umbral de distancia (0.25):** si el mejor fragmento está más lejos, se rechaza sin llamar al LLM. Es un filtro grueso: las distancias del modelo están comprimidas (preguntas legítimas hasta 0.230, fuera de tema desde 0.221), así que solo frena lo claramente ajeno.
- **Señal `SIN_INFO`:** si los fragmentos no contienen la respuesta, el modelo responde solo esa palabra y el código muestra un mensaje estándar, sin fuentes.

## Limitaciones conocidas

- Corpus chico: 14 páginas y 261 chunks.
- Las fuentes mostradas son los fragmentos consultados, no necesariamente todos los que usó el modelo; el modelo local suele citar una sola vez al final.
- Cuando hay cambios se reindexa todo desde cero.
- Preguntas de temas vecinos (por ejemplo Kubernetes o Spark) pasan el umbral y dependen de `SIN_INFO`.
- No cubre prompt injection (en la pregunta ni en las páginas indexadas).
- La contraseña de la base (`rag`) es solo para desarrollo local.