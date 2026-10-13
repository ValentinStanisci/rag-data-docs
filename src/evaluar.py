from buscar import buscar_chunks

B = "https://docs.getdbt.com/docs/build/"
A = "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/"

# (pregunta, [páginas donde está la respuesta])
PREGUNTAS = [
    ("¿Qué diferencia hay entre view, table y ephemeral?", [B + "materializations"]),
    ("¿Cuándo conviene usar un modelo incremental en vez de una tabla?",
     [B + "incremental-models", B + "materializations"]),
    ("¿Cómo uso is_incremental() para filtrar solo las filas nuevas?", [B + "incremental-models"]),
    ("¿Cómo defino un test not_null o unique sobre una columna?", [B + "data-tests"]),
    ("¿Cómo pruebo la lógica de un modelo con datos de ejemplo?", [B + "unit-tests"]),
    ("¿Cómo guardo el historial de cambios de una tabla con snapshots?", [B + "snapshots"]),
    ("¿Cómo cargo un archivo CSV como tabla con dbt?", [B + "seeds"]),
    ("¿Cómo escribo una macro reutilizable con Jinja?", [B + "jinja-macros"]),
    ("¿Qué es un modelo en dbt y dónde se guardan?", [B + "models"]),
    ("¿Cómo declaro un DAG?", [A + "dags.html"]),
    ("¿Cómo defino el orden y las dependencias entre tareas?", [A + "dags.html", A + "tasks.html"]),
    ("¿Qué tipos de tareas existen en Airflow?", [A + "tasks.html"]),
    ("¿Cómo paso información de una tarea a otra?", [A + "xcoms.html", A + "taskflow.html"]),
    ("¿Cómo defino tareas con el decorador @task?", [A + "taskflow.html"]),
    ("¿Qué es un operador y qué relación tiene con una tarea?", [A + "operators.html", A + "tasks.html"]),
    ("¿Cómo hago que una tarea espere a un evento externo?", [A + "sensors.html"]),
    ("¿Qué diferencia hay entre XComs y Variables?", [A + "xcoms.html"]),
]


def nombre(url):
    return url.rstrip("/").split("/")[-1]


def evaluar(k=4):
    rangos = []
    distancias = []
    for pregunta, esperadas in PREGUNTAS:
        res = buscar_chunks(pregunta, k=k)
        urls = [c[1] for c in res]
        distancias.append(res[0][3])
        rango = next((i for i, u in enumerate(urls, 1) if u in esperadas), None)
        rangos.append(rango)
        if rango != 1:
            print(f"\n✗ {pregunta}")
            print(f"  esperada: {[nombre(u) for u in esperadas]}")
            print(f"  obtuvo:   {[nombre(u) for u in urls]}")
    n = len(rangos)
    print(f"\nPreguntas: {n}")
    print(f"hit@1: {sum(r == 1 for r in rangos) / n:.0%}")
    print(f"hit@3: {sum(r is not None and r <= 3 for r in rangos) / n:.0%}")
    print(f"hit@{k}: {sum(r is not None for r in rangos) / n:.0%}")
    print(f"MRR:   {sum(1 / r for r in rangos if r) / n:.2f}")
    print(f"Distancia del mejor resultado: mín {min(distancias):.3f}, "
          f"máx {max(distancias):.3f}")
    print("Las 3 más altas:", [round(d, 3) for d in sorted(distancias)[-3:]])

if __name__ == "__main__":
    evaluar()