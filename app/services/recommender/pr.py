from typing import Any, Dict, Iterable, List, cast

from app.models.recommendations import (
    RecommendationRequest,
    RecommendedItem,
)
from app.services.arango import arango_service
from app.services.recommender.base import Recommender


class PageRankRecommender(Recommender):
    """
    Персонализированный Random Walk with Restart по подграфу вокруг пользователя.
    """

    def __init__(self, alpha: float = 0.85, max_iter: int = 20) -> None:
        self.alpha = alpha
        self.max_iter = max_iter

    def recommend(self, request: RecommendationRequest) -> List[RecommendedItem]:
        db = arango_service.get_db()
        user_id = request.user_id
        k = request.k

        query = """
        LET userId = @user_id

        LET userEdges = (
          FOR e IN interactions
            FILTER e._from == CONCAT("users/", userId)
            RETURN e
        )

        LET userMovies = (
          FOR e IN userEdges
            RETURN PARSE_IDENTIFIER(e._to).key
        )

        LET neighborUsers = UNIQUE(
          FOR mId IN userMovies
            FOR e IN interactions
              FILTER PARSE_IDENTIFIER(e._to).key == mId
              RETURN PARSE_IDENTIFIER(e._from).key
        )

        LET neighborEdges = (
          FOR uId IN neighborUsers
            FOR e IN interactions
              FILTER PARSE_IDENTIFIER(e._from).key == uId
              RETURN e
        )

        RETURN {
          userEdges: userEdges,
          neighborEdges: neighborEdges
        }
        """

        cursor = db.aql.execute(query, bind_vars={"user_id": user_id})
        result_iter = cast(Iterable[dict[str, Any]], cursor)
        result = list(result_iter)
        if not result:
            return []

        data = result[0]
        user_edges = data["userEdges"]
        neighbor_edges = data["neighborEdges"]

        # строим неориентированный взвешенный граф
        neighbors: Dict[str, Dict[str, float]] = {}

        def add_edge(a: str, b: str, w: float) -> None:
            neighbors.setdefault(a, {})
            neighbors.setdefault(b, {})
            neighbors[a][b] = neighbors[a].get(b, 0.0) + w
            neighbors[b][a] = neighbors[b].get(a, 0.0) + w

        for e in user_edges + neighbor_edges:
            u = e["_from"]
            m = e["_to"]
            w = float(e.get("weight", 1.0))
            add_edge(u, m, w)

        start_node = f"users/{user_id}"
        if start_node not in neighbors:
            return []

        nodes = list(neighbors.keys())
        scores: Dict[str, float] = {n: 0.0 for n in nodes}
        scores[start_node] = 1.0

        alpha = self.alpha
        for _ in range(self.max_iter):
            new_scores: Dict[str, float] = {n: 0.0 for n in nodes}
            for n in nodes:
                neighs = neighbors[n]
                if not neighs:
                    continue
                total_w = sum(neighs.values())
                if total_w == 0:
                    continue
                for m, w in neighs.items():
                    new_scores[m] += alpha * scores[n] * (w / total_w)
            for n in nodes:
                new_scores[n] += (1 - alpha) * (1.0 if n == start_node else 0.0)
            scores = new_scores

        seen_movies = {e["_to"].split("/", 1)[1] for e in user_edges}
        movie_scores: Dict[str, float] = {}

        for node, s in scores.items():
            if node.startswith("movies/"):
                movie_id = node.split("/", 1)[1]
                if movie_id in seen_movies:
                    continue
                movie_scores[movie_id] = s

        ranked = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)[:k]

        return [
            RecommendedItem(
                item_id=movie_id,
                score=float(score),
                reason="personalized_pagerank",
            )
            for movie_id, score in ranked
        ]
