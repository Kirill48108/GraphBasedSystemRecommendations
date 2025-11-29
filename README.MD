# Система рекомендаций на основе графов (FastAPI + ArangoDB)

## 1. Описание проекта

Сервис персональных рекомендаций фильмов на основе графовой модели данных и алгоритмов рекомендаций.  

Особенности:

- Графовая база данных **ArangoDB** (узлы: пользователи и фильмы, рёбра взаимодействий).
- Backend на **FastAPI** (чистый API, без сложного фронтенда).
- Онлайн‑алгоритмы рекомендаций:
  - популярность;
  - user-based CF;
  - k‑NN;
  - персонализированный PageRank / Random Walk with Restart;
  - гибридный скоринг (комбинация нескольких алгоритмов).
- **Redis** — кэш рекомендаций и хранение A/B‑флагов.
- **Celery** — фоновые задачи (инвалидация кэша и др.).
- **Airflow** — офлайн DAG’и:
  - nightly пересчёт популярности (витрины);
  - офлайн‑метрики качества (Hit@K, MAP@K).
- JWT‑аутентификация, rate limiting, базовые тесты (pytest).

Проект задуман как учебно‑продуктовый пример «индустриального» рекомендательного сервиса.

---

## 2. Архитектура

### 2.1. Компоненты

- **API (FastAPI)** — эндпоинты:
  - `/auth/token` — получение JWT;
  - `/interactions` — запись действий пользователя;
  - `/recommendations` — онлайн‑рекомендации;
  - `/explain` — объяснение, «почему рекомендовано»;
  - `/stats/*` — статистика и метрики;
  - `/ab/*` — A/B‑назначения;
  - `/events` — лог show/click.
- **ArangoDB** — графовая модель:
  - коллекции вершин: `users`, `movies`;
  - коллекция рёбер: `interactions` (view/like/rating, веса и timestamp);
  - вспомогательные коллекции:
    - `events` (show/click для A/B и метрик),
    - `popularity_offline` (витрины популярности),
    - `metrics_offline` (офлайн‑метрики качества),
    - `auth_users` (учётные записи для JWT).
- **Redis** — кэш `rec:{user_id}:{algo}` и флаги A/B (`ab:{user_id}`).
- **Celery** — фоновые воркеры (инвалидация кэша рекомендаций при новых взаимодействиях).
- **Airflow** — DAG’и:
  - `offline_popularity` — nightly пересчёт популярности за 7/30/90 дней;
  - `offline_quality` — расчёт Hit@K и MAP@K по логам `events`.
- **pytest** — набор автоматических тестов для основных сценариев.

### 2.2. Потоки данных (коротко)

- **Добавление предпочтений**:
  - `POST /api/v1/interactions` → запись ребра в `interactions` (ArangoDB) → отправка Celery‑таски на инвалидацию ключей `rec:{user_id}:*` в Redis.
- **Получение рекомендаций**:
  - `GET /api/v1/recommendations?algo=...` → проверка кэша Redis:
    - hit → мгновенный ответ;
    - miss → расчёт алгоритмом (popular/CF/k‑NN/PR/hybrid) по графу Arango → запись в кэш → ответ.
- **A/B и события**:
  - `GET /api/v1/ab/assign` — детерминированное назначение варианта A/B пользователю и кеширование в Redis;
  - `POST /api/v1/events` — лог show/click/variant в коллекции `events`.
- **Офлайн‑пересчёты (Airflow)**:
  - DAG `offline_popularity` заполняет `popularity_offline`;
  - DAG `offline_quality` считает Hit@K и MAP@K по `events` и пишет в `metrics_offline`.

---

## 3. Технический стек

- **Язык:** Python 3.13 (poetry).
- **API:** FastAPI + Uvicorn.
- **БД:** ArangoDB.
- **Кэш/флаги:** Redis.
- **Фоновая обработка:** Celery (Redis как брокер/бэкенд).
- **Офлайн‑оркестрация:** Apache Airflow (отдельный контейнер).
- **Аутентификация:** JWT (python-jose).
- **Хранение паролей:** passlib (pbkdf2_sha256).
- **Тестирование:** pytest, httpx, pytest‑asyncio, pytest‑cov.
- **Контейнеризация:** Docker, docker-compose.
- **Качество кода:** ruff, mypy, GitHub Actions.

---

## 4. Структура проекта

Предлагаю заменить фрагмент раздела 4 на нормальный блок:

<llm-snippet-file>README.MD</llm-snippet-file>
```markdown
## 4. Структура проекта


.
├─ app/
│  ├─ api/
│  │  └─ v1/
│  │     ├─ endpoints/
│  │     │  ├─ auth.py
│  │     │  ├─ interactions.py
│  │     │  ├─ recommendations.py
│  │     │  ├─ explain.py
│  │     │  ├─ stats.py
│  │     │  ├─ ab.py
│  │     │  └─ events.py
│  │     └─ router.py
│  ├─ core/
│  │  ├─ config.py       # настройки из .env
│  │  ├─ security.py     # JWT, хэширование паролей
│  │  ├─ rate_limit.py   # rate limiting middleware
│  │  └─ logging.py      # конфигурация логов
│  ├─ models/            # pydantic-модели запросов/ответов
│  ├─ services/
│  │  ├─ arango.py       # обёртка над ArangoDB
│  │  ├─ redis_cache.py  # обёртка над Redis
│  │  ├─ recommender/    # алгоритмы рекомендаций
│  │  ├─ stats.py        # логика статистики
│  │  └─ ab.py           # логика A/B-назначений
│  └─ worker/
│     ├─ celery_app.py
│     └─ tasks.py        # Celery-задачи
├─ dags/
│  ├─ offline_popularity.py
│  └─ offline_quality.py
├─ scripts/
│  ├─ init_arango.py      # инициализация БД/графа
│  ├─ create_demo_admin.py # создание демо-админа
│  └─ load_test_data.py   # загрузка тестовых данных (по желанию)
├─ tests/                 # pytest-тесты
├─ docker-compose.yml
├─ Dockerfile
├─ pyproject.toml
├─ .env.example
└─ main.py                # точка входа FastAPI (uvicorn main:app)
```


## 5. Настройка окружения

### 5.1. .env

Создайте файл `.env` по шаблону `.env.example`:

bash cp .env.example .env


Ключевые переменные:

- `ARANGO_URL`, `ARANGO_DB`, `ARANGO_USER`, `ARANGO_PASSWORD` — параметры подключения к ArangoDB.
- `REDIS_URL` — URI Redis (по умолчанию `redis://redis:6379/0` в docker-сети).
- `SECRET_KEY` — **обязательно заменить** на случайную строку (используется для подписи JWT).
- `DEMO_ADMIN_USERNAME`, `DEMO_ADMIN_PASSWORD` — логин/пароль демо‑админа (используются скриптом `create_demo_admin.py`).
- `RATE_LIMIT_REQUESTS_PER_MINUTE` — лимит запросов в минуту на пользователя.

### 5.2. Зависимости (локально)

bash poetry install




## 6. Запуск через Docker

### 6.1. Сборка и запуск

bash docker-compose build docker-compose up


Поднимаются сервисы:

- `api` (FastAPI, порт 8000);
- `arangodb` (порт 8529);
- `redis` (порт 6379);
- `celery-worker`;
- `airflow` (порт 8080, если добавлен соответствующий сервис в compose).

### 6.2. Инициализация схемы ArangoDB и демо-пользователей

В отдельном терминале:
```
bash docker-compose exec api python -m scripts.init_arango docker-compose exec api python -m scripts.create_demo_admin
``` 

Проверка:

- ArangoDB UI: `http://127.0.0.1:8529` (логин/пароль из `.env`);
- БД `movies`, коллекции `users`, `movies`, `interactions`, `events`, `auth_users`, `popularity_offline`, `metrics_offline`.

### 6.3. Airflow UI (если используется)

- `http://127.0.0.1:8080`  
  (логин/пароль, сгенерированные Airflow в standalone‑режиме — см. логи контейнера `airflow`).

Включите DAG’и `offline_popularity` и `offline_quality` и при необходимости запустите их вручную.

---

## 7. Примеры запросов (демо-сценарий)

### 7.1. Получение JWT

bash http POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded
username=admin password=admin


В ответе: поле `access_token`.

### 7.2. Добавление взаимодействия

bash http POST /api/v1/interactions
Authorization:"Bearer <access_token>"
Content-Type:application/json
user_id="ignored_on_server_side"
item_id="movie_1"
type="view"


### 7.3. Получение рекомендаций

bash http GET /api/v1/recommendations?algo=hybrid&k=10
Authorization:"Bearer <access_token>"


Ответ: список фильмов с `item_id`, `score`, `reason`.

### 7.4. Статистика

- Популярность:

  ```bash
  http GET /api/v1/stats/popularity?window=7d&k=10
  ```

- Качество рекомендаций (офлайн-метрики):

  ```bash
  http GET /api/v1/stats/quality?k=10
  ```

---

## 8. Тестирование

Запуск тестов:

bash poetry run pytest -q

Чтобы тесты прошли, должны быть доступны ArangoDB и Redis (локально или через `docker-compose up -d arangodb redis`).

---
```
``` 
## 5. Настройка окружения

### 5.1. .env

Создайте файл `.env` по шаблону `.env.example`:
```
bash cp .env.example .env
``` 

Ключевые переменные:

- `ARANGO_URL`, `ARANGO_DB`, `ARANGO_USER`, `ARANGO_PASSWORD` — параметры подключения к ArangoDB.
- `REDIS_URL` — URI Redis (по умолчанию `redis://redis:6379/0` в docker-сети).
- `SECRET_KEY` — **обязательно заменить** на случайную строку (используется для подписи JWT).
- `DEMO_ADMIN_USERNAME`, `DEMO_ADMIN_PASSWORD` — логин/пароль демо‑админа (используются скриптом `create_demo_admin.py`).
- `RATE_LIMIT_REQUESTS_PER_MINUTE` — лимит запросов в минуту на пользователя.

### 5.2. Зависимости (локально)
```
bash poetry install
``` 

---

## 6. Запуск через Docker

### 6.1. Сборка и запуск
```
bash docker-compose build docker-compose up
``` 

Поднимаются сервисы:

- `api` (FastAPI, порт 8000);
- `arangodb` (порт 8529);
- `redis` (порт 6379);
- `celery-worker`;
- `airflow` (порт 8080, если добавлен соответствующий сервис в compose).

### 6.2. Инициализация схемы ArangoDB и демо-пользователей

В отдельном терминале:
```
bash docker-compose exec api python -m scripts.init_arango docker-compose exec api python -m scripts.create_demo_admin
``` 

Проверка:

- ArangoDB UI: `http://127.0.0.1:8529` (логин/пароль из `.env`);
- БД `movies`, коллекции `users`, `movies`, `interactions`, `events`, `auth_users`, `popularity_offline`, `metrics_offline`.

### 6.3. Airflow UI (если используется)

- `http://127.0.0.1:8080`  
  (логин/пароль, сгенерированные Airflow в standalone‑режиме — см. логи контейнера `airflow`).

Включите DAG’и `offline_popularity` и `offline_quality` и при необходимости запустите их вручную.

---

## 7. Примеры запросов (демо-сценарий)

### 7.1. Получение JWT
```
bash http POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded
username=admin password=admin
``` 

В ответе: поле `access_token`.

### 7.2. Добавление взаимодействия
```
bash http POST /api/v1/interactions
Authorization:"Bearer <access_token>"
Content-Type:application/json
user_id="ignored_on_server_side"
item_id="movie_1"
type="view"
``` 

### 7.3. Получение рекомендаций
```
bash http GET /api/v1/recommendations?algo=hybrid&k=10
Authorization:"Bearer <access_token>"
``` 

Ответ: список фильмов с `item_id`, `score`, `reason`.

### 7.4. Статистика

- Популярность:

  ```bash
  http GET /api/v1/stats/popularity?window=7d&k=10
  ```

- Качество рекомендаций (офлайн-метрики):

  ```bash
  http GET /api/v1/stats/quality?k=10
  ```

---

## 8. Тестирование

Запуск тестов:
```
bash poetry run pytest -q
``` 

Чтобы тесты прошли, должны быть доступны ArangoDB и Redis (локально или через `docker-compose up -d arangodb redis`).

---
```

``` 
## 9. Покрытие кода

Покрытие измеряется с помощью `pytest-cov`:
```
bash poetry run pytest --cov=app --cov-report=term-missing poetry run coverage html # HTML-отчёт в каталоге coverage_html/
``` 

Открыть отчёт можно, открыв файл `coverage_html/index.html` в браузере.

В конфигурации coverage (см. `pyproject.toml`, секция `[tool.coverage.run]`) из строковой метрики **исключены**:

- низкоуровневый слой доступа к БД ArangoDB:
  - `app/services/arango.py`;
- фоновые задачи Celery:
  - `app/worker/*`;
- «тяжёлые» алгоритмы рекомендаций, тестируемые интеграционно через `/recommendations`:
  - `app/services/recommender/cf.py`,
  - `app/services/recommender/knn.py`,
  - `app/services/recommender/pr.py`,
  - `app/services/recommender/hybrid.py`,
  - `app/services/recommender/popular.py`;
- вспомогательные сервисы, чья логика проверяется через API:
  - `app/services/ab.py`,
  - `app/services/explain.py`,
  - `app/services/redis_cache.py`,
  - `app/services/stats.py`.

Таким образом, метрика покрывает в первую очередь **бизнес‑слой** приложения:

- core (конфигурация, безопасность, rate limiting, логирование);
- API‑эндпоинты;
- модели;
- основной glue‑код сервисов.

Итоговое покрытие по пакету `app` (с учётом описанного отбора) составляет **≈86%**.

Алгоритмы рекомендаций (CF, k‑NN, персонализированный PageRank, гибридный скоринг) и низкоуровневый слой работы с БД ArangoDB дополнительно проверяются интеграционными тестами через публичные API (`/recommendations`, `/stats/*`, скрипты `init_arango.py` / `create_demo_admin.py`).

---

## 10. Статический анализ и линтеры

Для повышения качества кода используются:

- **ruff** — статический анализ и стиль (PEP8, импорты, базовые best practices).
- **mypy** — статическая проверка типов для пакета `app`.

Запуск локально:
```
bash poetry run ruff check app tests poetry run mypy app
``` 

---

## 11. CI (GitHub Actions)

В репозитории настроен workflow (`.github/workflows/ci.yml`), который при каждом push/pull‑request:

1. Поднимает ArangoDB и Redis как сервисы.
2. Устанавливает зависимости через `poetry`.
3. Инициализирует схему БД и демо‑админа (`scripts/init_arango.py`, `scripts/create_demo_admin.py`).
4. Запускает:
   - `ruff check` (линтер),
   - `mypy` (проверка типов),
   - `pytest --cov=app --cov-report=term-missing` (тесты и покрытие).

Это позволяет автоматически контролировать качество кода и не допускать регрессий.

---

## 12. Безопасность и эксплуатация

- **JWT `SECRET_KEY`** должен быть уникальным и не лежать в открытом виде в прод‑окружении.
- **Пароли пользователей** хэшируются с помощью `pbkdf2_sha256` (passlib).
- **ArangoDB/Redis** в проде должны использовать отдельные учётные записи и при необходимости TLS.
- **Airflow standalone** — только для разработки; в проде требуется разнести webserver, scheduler и worker.

---

## 13. Известные ограничения и возможные улучшения

- Офлайн‑метрики (Hit@K, MAP@K) считаются по упрощённому сценарию на событиях show/click, без сложных offline‑splitов.
- Холодный старт покрыт популярностью и гибридным алгоритмом, но без контентных признаков.
- Нет полноценного UI (только API/Swagger); для реального продукта можно добавить web‑интерфейс.
- ArangoDB запросы реализованы на уровне Python‑кода; часть логики можно вынести в представления/хранимые процедуры для оптимизации.

```


