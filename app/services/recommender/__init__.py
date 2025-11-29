from typing import Dict

from app.models.recommendations import AlgorithmName
from app.services.recommender.base import Recommender
from app.services.recommender.cf import CFRecommender
from app.services.recommender.hybrid import HybridRecommender
from app.services.recommender.knn import KNNRecommender
from app.services.recommender.popular import PopularRecommender
from app.services.recommender.pr import PageRankRecommender

_recommenders: Dict[AlgorithmName, Recommender] = {
    AlgorithmName.POPULAR: PopularRecommender(),
    AlgorithmName.CF: CFRecommender(),
    AlgorithmName.KNN: KNNRecommender(),
    AlgorithmName.PR: PageRankRecommender(),
    AlgorithmName.HYBRID: HybridRecommender(),
}


def get_recommender(algo: AlgorithmName) -> Recommender:
    if algo not in _recommenders:
        # Временно будем отдавать popular для не реализованных алгоритмов
        # или можно бросать исключение, а на уровне API вернуть 501.
        return _recommenders[AlgorithmName.POPULAR]
    return _recommenders[algo]
