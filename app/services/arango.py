from datetime import datetime
from typing import Any, Iterable, cast

from arango import ArangoClient
from arango.database import StandardDatabase

from app.core.config import settings
from app.models.events import EventCreate
from app.models.interactions import InteractionCreate, InteractionType


class ArangoService:
    def __init__(
        self,
        url: str,
        db_name: str,
        username: str,
        password: str,
    ) -> None:
        self._client = ArangoClient(hosts=url)
        self._db_name = db_name
        self._username = username
        self._password = password

    def get_or_create_db(self) -> StandardDatabase:
        """
        Возвращает подключение к БД. Если БД нет — создаёт.
        """
        sys_db = self._client.db(
            "_system", username=self._username, password=self._password
        )

        if not sys_db.has_database(self._db_name):
            sys_db.create_database(self._db_name)

        db = self._client.db(
            self._db_name, username=self._username, password=self._password
        )
        return db

    def get_db(self) -> StandardDatabase:
        """
        Просто открыть существующую БД (без создания).
        """
        return self._client.db(
            self._db_name, username=self._username, password=self._password
        )

    # ---- Инициализация схемы ----

    def init_schema(self) -> None:
        """
        Создаёт коллекции и граф, если их ещё нет.
        """
        db = self.get_or_create_db()

        # Коллекции вершин
        vertex_collections = ["users", "movies"]
        for col in vertex_collections:
            if not db.has_collection(col):
                db.create_collection(col)

        # Коллекция рёбер
        edge_collection = "interactions"
        if not db.has_collection(edge_collection):
            db.create_collection(edge_collection, edge=True)

        # Коллекция событий для A/B и CTR
        if not db.has_collection("events"):
            db.create_collection("events")

        # Коллекция офлайн-популярности
        if not db.has_collection("popularity_offline"):
            db.create_collection("popularity_offline")

        # Коллекция офлайн-метрик качества
        if not db.has_collection("metrics_offline"):
            db.create_collection("metrics_offline")

        # Коллекция пользователей для аутентификации
        if not db.has_collection("auth_users"):
            db.create_collection("auth_users")

        # Граф
        graph_name = "user_movie_graph"
        if not db.has_graph(graph_name):
            db.create_graph(
                graph_name,
                edge_definitions=[
                    {
                        "edge_collection": edge_collection,
                        "from_vertex_collections": ["users"],
                        "to_vertex_collections": ["movies"],
                    }
                ],
            )
        else:
            db.graph(graph_name)
            # на будущее: тут можно обновлять определения, если надо

    def ensure_user(self, user_id: str) -> None:
        """
        Создаёт вершину пользователя, если её ещё нет.
        """
        db = self.get_db()
        users = db.collection("users")
        doc_key = user_id
        if not users.has(doc_key):
            users.insert({"_key": doc_key, "created_at": None})

    def ensure_movie(self, movie_id: str) -> None:
        """
        Создаёт вершину фильма, если её ещё нет.
        """
        db = self.get_db()
        movies = db.collection("movies")
        doc_key = movie_id
        if not movies.has(doc_key):
            movies.insert({"_key": doc_key})

    @staticmethod
    def _compute_weight(interaction: InteractionCreate) -> float:
        """
        Простая функция веса взаимодействия:
        - view: 1.0
        - like: 2.0
        - rating: 1.0–3.0 (в зависимости от value)
        """
        if interaction.type == InteractionType.VIEW:
            return 1.0
        if interaction.type == InteractionType.LIKE:
            return 2.0
        if interaction.type == InteractionType.RATING:
            if interaction.value is None:
                return 1.0
            # например, нормируем 1–5 к 1.0–3.0
            return 1.0 + (interaction.value - 1) * (2.0 / 4.0)
        return 1.0

    def create_interaction(self, interaction: InteractionCreate) -> str:
        """
        Создаёт ребро взаимодействия в графе. Возвращает ID ребра.
        """
        db = self.get_db()
        graph = db.graph("user_movie_graph")
        edge_collection = graph.edge_collection("interactions")

        # гарантируем, что вершины существуют
        self.ensure_user(interaction.user_id)
        self.ensure_movie(interaction.item_id)

        from_id = f"users/{interaction.user_id}"
        to_id = f"movies/{interaction.item_id}"

        weight = self._compute_weight(interaction)

        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "type": interaction.type.value,
            "value": interaction.value,
            "timestamp": interaction.timestamp.isoformat(),
            "weight": weight,
        }

        result = edge_collection.insert(edge_doc)
        result_dict = cast(dict[str, Any], result)
        return str(result_dict["_id"])

    def create_event(self, event: "EventCreate") -> str:
        """
        Создаёт документ события (show/click) в коллекции events.
        """
        db = self.get_db()
        events_col = db.collection("events")

        doc = {
            "user_id": event.user_id,
            "item_id": event.item_id,
            "variant": event.variant.value,
            "type": event.type.value,
            "timestamp": event.timestamp.isoformat(),
        }

        result = events_col.insert(doc)
        result_dict = cast(dict[str, Any], result)
        return str(result_dict["_id"])

    def create_auth_user(
        self, username: str, hashed_password: str, role: str = "user", result=None
    ) -> str:
        """
        Создаёт пользователя для аутентификации в коллекции auth_users.
        Возвращает user_id (_key). Если username уже существует — возвращает существующий _key.
        """
        db = self.get_db()
        col = db.collection("auth_users")

        # Проверяем, есть ли пользователь с таким username
        cursor = col.find({"username": username}, limit=1)
        existing_iter = cast(Iterable[dict[str, Any]], cursor)
        existing = list(existing_iter)
        if existing:
            return str(existing[0]["_key"])

        doc = {
            "username": username,
            "hashed_password": hashed_password,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = col.insert(doc)
        result_dict = cast(dict[str, Any], result)
        return str(result_dict["_key"])


# Глобальный синглтон-сервис (будем использовать в зависимостях и скриптах)
arango_service = ArangoService(
    url=settings.arango_url,
    db_name=settings.arango_db,
    username=settings.arango_user,
    password=settings.arango_password,
)
