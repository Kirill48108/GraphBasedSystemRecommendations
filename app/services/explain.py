from app.models.explain import ExplainRequest, ExplainResponse
from app.models.recommendations import AlgorithmName


class ExplainService:
    """
    Простые текстовые объяснения для разных алгоритмов.
    Позже можно усложнить, подтягивая реальные основания (похожие пользователи/фильмы и т.п.).
    """

    def explain(self, req: ExplainRequest) -> ExplainResponse:
        if req.algo == AlgorithmName.POPULAR:
            explanation = "Фильм популярен среди пользователей, похожих на вас."
        elif req.algo == AlgorithmName.CF:
            explanation = "Фильм понравился пользователям с похожими предпочтениями."
        elif req.algo == AlgorithmName.KNN:
            explanation = (
                "Фильм похож на другие фильмы, которые вы смотрели или оценивали."
            )
        elif req.algo == AlgorithmName.PR:
            explanation = (
                "Фильм имеет высокий персонализированный ранг "
                "в вашем графе предпочтений."
            )
        elif req.algo == AlgorithmName.HYBRID:
            explanation = (
                "Фильм рекомендован гибридным алгоритмом,"
                " учитывающим популярность и сходство."
            )
        else:
            explanation = (
                "Фильм рекомендован на основе ваших взаимодействий и популярности."
            )

        return ExplainResponse(
            user_id=req.user_id,
            item_id=req.item_id,
            algo=req.algo,
            explanation=explanation,
        )


explain_service = ExplainService()
