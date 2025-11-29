import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from arango import ArangoClient

ARANGO_URL = os.getenv("ARANGO_URL", "http://arangodb:8529")
ARANGO_DB = os.getenv("ARANGO_DB", "movies")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "password")


def compute_quality(k: int = 10) -> None:
    """
    Упрощённый расчёт Hit@K и MAP@K на основе логов events.
    Идея:
    - берём недавние события за N дней;
    - для каждого user/variant считаем: какие фильмы показали, по каким был click;
    - считаем Hit@K и MAP@K по этим спискам.
    """
    client = ArangoClient(hosts=ARANGO_URL)
    db = client.db(ARANGO_DB, username=ARANGO_USER, password=ARANGO_PASSWORD)

    since = (datetime.utcnow() - timedelta(days=7)).isoformat()

    if not db.has_collection("metrics_offline"):
        db.create_collection("metrics_offline")
    col = db.collection("metrics_offline")
    col.delete_many({"name": "recs_quality", "k": k})

    # Собираем события за 7 дней
    query = """
    LET since = @since

    FOR e IN events
      FILTER e.timestamp >= DATE_ISO8601(since)
      COLLECT
        userId = e.user_id,
        variant = e.variant
      INTO grouped

      LET shows = (
        FOR ev IN grouped
          FILTER ev.type == "show"
          RETURN ev.item_id
      )

      LET clicks = (
        FOR ev IN grouped
          FILTER ev.type == "click"
          RETURN ev.item_id
      )

      RETURN {
        user_id: userId,
        variant: variant,
        shows: shows,
        clicks: clicks
      }
    """

    cursor = db.aql.execute(query, bind_vars={"since": since})
    sessions = list(cursor)

    if not sessions:
        return

    def hit_at_k(shows, clicks, k_val):
        if not shows or not clicks:
            return 0.0
        top_k = shows[:k_val]
        for item in top_k:
            if item in clicks:
                return 1.0
        return 0.0

    def average_precision_at_k(shows, clicks, k_val):
        if not shows or not clicks:
            return 0.0
        hits = 0
        score = 0.0
        for i, item in enumerate(shows[:k_val], start=1):
            if item in clicks:
                hits += 1
                score += hits / i
        if hits == 0:
            return 0.0
        return score / hits

    total_hit = 0.0
    total_map = 0.0
    n = 0

    for s in sessions:
        shows = s["shows"]
        clicks = s["clicks"]
        if not shows:
            continue
        total_hit += hit_at_k(shows, clicks, k)
        total_map += average_precision_at_k(shows, clicks, k)
        n += 1

    if n == 0:
        return

    avg_hit = total_hit / n
    avg_map = total_map / n

    col.insert(
        {
            "name": "recs_quality",
            "k": k,
            "hit_at_k": float(avg_hit),
            "map_at_k": float(avg_map),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    )


with DAG(
    dag_id="offline_quality",
    start_date=datetime(2025, 1, 1),
    schedule="0 4 * * *",  # каждый день в 04:00
    catchup=False,
    tags=["movies", "quality"],
) as dag:
    task_quality_k10 = PythonOperator(
        task_id="compute_quality_k10",
        python_callable=compute_quality,
        op_args=[10],
    )
