from datetime import datetime, timedelta
from typing import Any, Iterable, List, Optional, cast

from app.models.stats import PopularItem, PopularityWindow, QualityMetrics
from app.services.arango import arango_service


class StatsService:
    def get_popularity_online(
        self, window: PopularityWindow, k: int
    ) -> List[PopularItem]:
        """
        Online-расчёт популярности по interactions.
        """
        db = arango_service.get_db()

        now = datetime.utcnow()
        if window == PopularityWindow.D7:
            since = now - timedelta(days=7)
        elif window == PopularityWindow.D30:
            since = now - timedelta(days=30)
        else:
            since = now - timedelta(days=90)

        query = """
        LET since = @since

        FOR e IN interactions
          FILTER e.timestamp >= DATE_ISO8601(since)
          COLLECT movieId = PARSE_IDENTIFIER(e._to).key INTO group = e
          LET score = SUM(group[*].weight)
          SORT score DESC
          LIMIT @k
          RETURN {
            movie_id: movieId,
            score: score
          }
        """

        bind_vars = {
            "since": since.isoformat(),
            "k": k,
        }

        cursor = db.aql.execute(query, bind_vars=bind_vars)  # type: ignore[arg-type]
        docs_iter = cast(Iterable[dict[str, Any]], cursor)
        docs = list(docs_iter)

        return [
            PopularItem(item_id=doc["movie_id"], score=float(doc["score"]))
            for doc in docs
        ]

    def get_popularity_offline(
        self, window: PopularityWindow, k: int
    ) -> List[PopularItem]:
        """
        Читает предрасчитанные витрины из popularity_offline.
        """
        db = arango_service.get_db()
        if not db.has_collection("popularity_offline"):
            return []

        window_id = window.value  # "7d" / "30d" / "90d"

        query = """
        FOR p IN popularity_offline
          FILTER p.`window` == @window
          SORT p.score DESC
          LIMIT @k
          RETURN p
        """
        bind_vars: dict[str, object] = {"window": window_id, "k": k}
        cursor = db.aql.execute(query, bind_vars=bind_vars)  # type: ignore[arg-type]
        docs_iter = cast(Iterable[dict[str, Any]], cursor)
        docs = list(docs_iter)

        return [
            PopularItem(item_id=doc["movie_id"], score=float(doc["score"]))
            for doc in docs
        ]

    def get_quality_offline(self, k: int) -> Optional[QualityMetrics]:
        """
        Читает офлайн-метрики из metrics_offline.
        """
        db = arango_service.get_db()
        if not db.has_collection("metrics_offline"):
            return None

        query = """
        FOR m IN metrics_offline
          FILTER m.name == "recs_quality" AND m.k == @k
          SORT m.calculated_at DESC
          LIMIT 1
          RETURN m
        """
        bind_vars: dict[str, object] = {"k": k}
        cursor = db.aql.execute(query, bind_vars=bind_vars)  # type: ignore[arg-type]
        docs_iter = cast(Iterable[dict[str, Any]], cursor)
        docs = list(docs_iter)
        if not docs:
            return None

        doc = docs[0]
        return QualityMetrics(
            hit_at_k=float(doc.get("hit_at_k", 0.0)),
            map_at_k=float(doc.get("map_at_k", 0.0)),
            k=int(doc.get("k", k)),
            calculated_at=datetime.fromisoformat(doc["calculated_at"]),
        )


stats_service = StatsService()
