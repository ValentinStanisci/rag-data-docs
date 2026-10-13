from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="rag_docs_ingesta",
    schedule="@daily",
    start_date=datetime(2026, 10, 1),
    catchup=False,
    tags=["rag"],
)
def rag_docs_ingesta():
    @task
    def ingestar():
        from ingest import ingestar_todo

        return ingestar_todo()

    @task.short_circuit
    def hay_cambios(cambiadas: int) -> bool:
        print("Páginas nuevas o modificadas:", cambiadas)
        return cambiadas > 0

    @task
    def reindexar():
        from indexar import main

        main()

    hay_cambios(ingestar()) >> reindexar()


rag_docs_ingesta()