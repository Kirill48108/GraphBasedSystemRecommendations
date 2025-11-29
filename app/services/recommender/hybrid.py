from typing import Dict, List

from app.core.config import settings
from app.models.recommendations import (
    AlgorithmName,
    RecommendationRequest,
    RecommendedItem,
)
from app.services.recommender.base import Recommender


class HybridRecommender(Recommender):
    """
    Гибридный скоринг: линейная комбинация popular, cf и pr.
    """

    def recommend(self, request: RecommendationRequest) -> List[RecommendedItem]:
        # ЛЕНИВЫЙ импорт, чтобы избежать циклического импорта с __init__.py
        from app.services.recommender import get_recommender

        user_id = request.user_id
        k = request.k

        weights = {
            AlgorithmName.POPULAR: settings.hybrid_weight_popular,
            AlgorithmName.CF: settings.hybrid_weight_cf,
            AlgorithmName.PR: settings.hybrid_weight_pr,
        }

        scores: Dict[str, float] = {}
        reasons: Dict[str, List[str]] = {}

        for algo, w in weights.items():
            if w <= 0:
                continue

            sub_req = RecommendationRequest(user_id=user_id, algo=algo, k=k * 2)
            recommender = get_recommender(algo)
            items = recommender.recommend(sub_req)

            if not items:
                continue

            max_score = max(it.score for it in items) or 1.0

            for it in items:
                norm = it.score / max_score
                scores[it.item_id] = scores.get(it.item_id, 0.0) + w * norm
                reasons.setdefault(it.item_id, []).append(algo.value)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

        result: List[RecommendedItem] = []
        for item_id, score in ranked:
            rs = ",".join(sorted(set(reasons.get(item_id, []))))
            reason = f"hybrid({rs})" if rs else "hybrid"
            result.append(
                RecommendedItem(
                    item_id=item_id,
                    score=float(score),
                    reason=reason,
                )
            )

        return result
