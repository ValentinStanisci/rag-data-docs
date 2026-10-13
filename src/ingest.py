import hashlib
import json
import re
import time
from datetime import datetime, timezone

import boto3
import requests
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

BUCKET = "rag-data-docs"
PREFIX = "rag-docs/raw"

URLS = {
    "dbt": [
        "https://docs.getdbt.com/docs/build/materializations",
        "https://docs.getdbt.com/docs/build/incremental-models",
        "https://docs.getdbt.com/docs/build/models",
        "https://docs.getdbt.com/docs/build/data-tests",
        "https://docs.getdbt.com/docs/build/unit-tests",
        "https://docs.getdbt.com/docs/build/snapshots",
        "https://docs.getdbt.com/docs/build/seeds",
        "https://docs.getdbt.com/docs/build/jinja-macros",
    ],
    "airflow": [
        "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html",
        "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html",
        "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/taskflow.html",
        "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html",
        "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html",
        "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/sensors.html",
    ],
}

s3 = boto3.client("s3")


def extraer_texto(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button", "dialog"]):
        tag.decompose()
    for tag in soup.select('[role="dialog"], [role="search"], [aria-modal]'):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    titulo = soup.title.get_text(strip=True) if soup.title else ""
    return titulo, main.get_text("\n", strip=True)


def slug(url):
    return re.sub(r"[^a-z0-9]+", "-", url.split("//")[1].lower()).strip("-")

def hash_guardado(key):
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        return json.loads(obj["Body"].read()).get("hash")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise

def ingestar(fuente, url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    titulo, texto = extraer_texto(resp.content)
    doc = {
        "fuente": fuente,
        "url": url,
        "titulo": titulo,
        "texto": texto,
        "hash": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
        "fecha_descarga": datetime.now(timezone.utc).isoformat(),
    }
    key = f"{PREFIX}/{fuente}/{slug(url)}.json"
    if hash_guardado(key) == doc["hash"]:
        print("SIN CAMBIOS", key)
        return False
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(doc, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    print("OK", key)
    return True

def ingestar_todo():
    cambiadas = 0
    for fuente, urls in URLS.items():
        for url in urls:
            if ingestar(fuente, url):
                cambiadas += 1
            time.sleep(1)
    return cambiadas

if __name__ == "__main__":
    print("Páginas nuevas o modificadas:", ingestar_todo())