FROM apache/airflow:3.3.0
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir requests beautifulsoup4 boto3 "psycopg[binary]" pgvector sentence-transformers