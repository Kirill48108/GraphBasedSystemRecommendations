import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from arango import ArangoClient

ARANGO_URL = os.getenv("ARANGO_URL", "http://arangodb:8529")
ARANGO_DB = os.getenv("ARANGO_DB", "movies")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "password")


def compute_popularity(window_days: int) -> None:
    client = ArangoClient(hosts=ARANGO_URL)
    db = client.db(ARANGO_DB, username=ARANGO_USER, password=ARANGO_PASSWORD)

    since = (datetime.utcnow() - timedelta(days=window_days)).isoformat()
    window_id = f"{window_days}d"

    # Удаляем старые записи по этому окну
    if not db.has_collection("popularity_offline"):
        db.create_collection("popularity_offline")
    col = db.collection("popularity_offline")
    col.delete_many({"window": window_id})  # безопасно, если пусто

    query = """
    LET since = @since
    FOR e IN interactions
      FILTER e.timestamp >= DATE_ISO8601(since)
      COLLECT movieId = PARSE_IDENTIFIER(e._to).key INTO group = e
      LET score = SUM(group[*].weight)
      SORT score DESC
      LIMIT 100
      RETURN {
        movie_id: movieId,
        score: score
      }
    """

    cursor = db.aql.execute(query, bind_vars={"since": since})
    docs = list(cursor)

    for doc in docs:
        col.insert(
            {
                "window": window_id,
                "movie_id": doc["movie_id"],
                "score": float(doc["score"]),
                "calculated_at": datetime.utcnow().isoformat(),
            }
        )


with DAG(
    dag_id="offline_popularity",
    start_date=datetime(2025, 1, 1),
    schedule="0 3 * * *",  # каждый день в 03:00
    catchup=False,
    tags=["movies", "stats"],
) as dag:
    task_popularity_7d = PythonOperator(
        task_id="compute_popularity_7d",
        python_callable=compute_popularity,
        op_args=[7],
    )

    task_popularity_30d = PythonOperator(
        task_id="compute_popularity_30d",
        python_callable=compute_popularity,
        op_args=[30],
    )

    task_popularity_90d = PythonOperator(
        task_id="compute_popularity_90d",
        python_callable=compute_popularity,
        op_args=[90],
    )

    task_popularity_7d >> [task_popularity_30d, task_popularity_90d]
