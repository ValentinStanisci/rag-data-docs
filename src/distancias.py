from buscar import buscar_chunks

PREGUNTAS = [
    # dentro del tema
    "¿Cómo funcionan los modelos incrementales en dbt?",
    "¿Cómo declaro un DAG?",
    "¿Cómo hago que una tarea espere a un evento externo?",
    "¿Cómo guardo el historial de cambios de una tabla con snapshots?",
    # fuera del tema
    "¿Cuál es la receta de las empanadas?",
    "¿Quién ganó el último mundial de fútbol?",
    "¿Cómo se configura un router wifi?",
    # de datos, pero no cubierto por la documentación indexada
    "¿Cómo se instala Kubernetes?",
    "¿Cómo funciona Spark Structured Streaming?",
]

for p in PREGUNTAS:
    dist = buscar_chunks(p, k=1)[0][3]
    print(f"{dist:.3f}  {p}")