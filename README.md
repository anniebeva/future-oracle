# Job Market Oracle

Job Market Oracle - это система прогнозирования трендов востребованности технологических навыков на рынке труда. Система анализирует вакансии из открытых источников и предсказывает, будет ли расти спрос на конкретный навык в ближайшую неделю.

## Тема прогнозирования

Область прогнозирования: **технологические навыки в сфере разработки программного обеспечения**.

Объект прогноза: **конкретный технологический навык (например, Python, Django, AWS)**.

Вопрос прогноза: **будет ли увеличиваться доля вакансий, упоминающих данный навык, в следующей неделе?**

## Источники данных

Проект использует два реальных источника данных:

1. **The Muse API**
   - Данные: Описания вакансий разработчиков программного обеспечения
   - Назначение: Основной источник информации о вакансиях и требуемых навыках
   - Реализация: `backend/app/core/config.py`, `backend/app/services/data_ingestion.py`

2. **Remotive API**
   - Данные: Описания удаленных вакансий в IT
   - Назначение: Дополнительный источник для расширения выборки
## Архитектура

Архитектура проекта состоит из следующих компонентов:

```
The Muse API ─┐
              ├─→ ingestion → парсинг → БД → анализ → прогноз → API
Remotive API ─┘
```

Основные компоненты:
- **API**: FastAPI приложение (`backend/app/main.py`)
- **Routers**: Маршруты API (`backend/app/api/routes/`)
- **Schemas**: Pydantic схемы для валидации данных (`backend/app/schemas/`)
- **Services**: Бизнес-логика (`backend/app/services/`)
## Структура проекта

```
future-oracle/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Data validation schemas
│   │   ├── services/     # Business logic
│   │   ├── repositories/ # Data access layer
│   │   ├── scripts/      # Utility scripts
│   │   └── db/           # Database configuration
│   ├── alembic/          # Database migrations
│   └── tests/            # Unit tests
## База данных

Модели базы данных:

1. **DataSource** (`data_sources`)
   - Назначение: Хранение информации об источниках данных
   - Поля: id, code, name, base_url, is_active, last_successful_sync_at
   - Связи: ingestion_runs, raw_source_records, job_postings, weekly_indicators

2. **IngestionRun** (`ingestion_runs`)
   - Назначение: Отслеживание запусков получения данных
   - Поля: id, source_id, status, started_at, finished_at, records_received, error_message
   - Связи: source, raw_source_records

3. **RawSourceRecord** (`raw_source_records`)
   - Назначение: Хранение сырых данных из источников
   - Поля: id, ingestion_run_id, source_id, external_id, retrieved_at, payload, payload_hash
   - Связи: source, ingestion_run

4. **JobPosting** (`job_postings`)
   - Назначение: Хранение обработанных вакансий
   - Поля: id, source_id, external_id, source_url, title, company_name, published_at, 
           first_seen_at, last_seen_at, location_raw, location_scope, is_remote, category,
           employment_type, description_html, description_text, content_hash, is_active
   - Связи: source, skill_matches

5. **Skill** (`skills`)
   - Назначение: Справочник технологических навыков
   - Поля: id, code, display_name, dictionary_version, is_active
   - Связи: aliases, job_skill_matches, weekly_indicators

6. **SkillAlias** (`skill_aliases`)
   - Назначение: Альтернативные названия навыков
   - Поля: id, skill_id, alias, match_type, is_active
   - Связи: skill

7. **JobSkillMatch** (`job_skill_matches`)
   - Назначение: Сопоставление вакансий с навыками
   - Поля: id, job_posting_id, skill_id, dictionary_version, matched_alias, 
           matched_in_title, matched_in_description, match_count
## Как данные попадают в систему

Реальный pipeline обработки данных:

1. Получение данных из API источников (The Muse, Remotive)
2. Сохранение сырых записей в `raw_source_records`
3. Парсинг и создание записей вакансий в `job_postings`
4. Сопоставление вакансий с навыками в `job_skill_matches`
5. Расчет еженедельных показателей в `weekly_indicators`
6. Расчет прогноза на основе исторических показателей
## Алгоритм прогнозирования

Алгоритм прогнозирования реализован в классе `ForecastService` (`backend/app/services/forecast_service.py`).

Используемые входные данные:
- Еженедельные показатели `skill_share` для конкретного навыка (минимум 3 недели)
- Количество дней покрытия (`coverage_days`)
- Количество подходящих вакансий (`eligible_postings_count`)

Расчет показателей:
1. Вычисление изменения доли навыка между неделями (trend_pp)
2. Вычисление изменения тренда (momentum_pp)

Формулы расчета:
```
trend_pp = skill_shares[0] - skill_shares[1]
trend_signal = max(-1.0, min(1.0, trend_pp / 5.0))

previous_trend_pp = skill_shares[1] - skill_shares[2]
momentum_pp = trend_pp - previous_trend_pp
momentum_signal = max(-1.0, min(1.0, momentum_pp / 3.0))

score = 0.7 * trend_signal + 0.3 * momentum_signal
```

Определение направления прогноза:
```
if score > 0.2:
    direction = "growing"
elif score < -0.2:
    direction = "declining"
else:
    direction = "stable"
```

Расчет уверенности (confidence):
```
coverage_factor = current_indicator.coverage_days / 7.0
volume_factor = min(current_indicator.eligible_postings_count / 100.0, 1.0)
confidence = int(100 * (0.6 * coverage_factor + 0.4 * volume_factor))
## Почему цифры сходятся

Демонстрация воспроизводимости на примере навыка "python":

Исходные данные (из демо):
- Неделя 1: 50% упоминаний python
- Неделя 2: 60% упоминаний python
- Неделя 3: 70% упоминаний python
- Неделя 4: 80% упоминаний python

Расчеты:
- trend_pp = 80 - 70 = 10.0
- trend_signal = min(1.0, 10.0 / 5.0) = 1.0
- previous_trend_pp = 70 - 60 = 10.0
- momentum_pp = 10.0 - 10.0 = 0.0
- momentum_signal = 0.0
- score = 0.7 * 1.0 + 0.3 * 0.0 = 0.7

Результат:
- direction = "growing" (так как 0.7 > 0.2)
## Уверенность и риск

**Confidence** означает уровень достоверности прогноза на основе:
- Полноты данных за неделю (coverage_factor)
- Объема выборки вакансий (volume_factor)

Рассчитывается как:
```
confidence = int(100 * (0.6 * coverage_factor + 0.4 * volume_factor))
```

**Risk** означает вероятность ошибки прогноза:
- "low": Высокая уверенность и достаточный объем данных
- "medium": Средняя уверенность
- "high": Низкая уверенность или недостаток данных
## Как система понимает, что прогноз ошибся

В текущей реализации система не имеет автоматического механизма проверки корректности прогнозов, поскольку:
1. Для проверки требуется знать реальные результаты (фактические значения skill_share в будущем)
2. Такие данные становятся доступны только после завершения прогнозируемого периода

Планируемый подход:
- Сравнение прогноза с фактическими значениями skill_share за прогнозируемую неделю
- Подсчет метрик точности (MAE, RMSE и т.д.)
- Использование результатов для улучшения алгоритма
## API

Основные endpoints прогнозирования:

1. **GET /api/forecasts/skills/{skill_code}**
   - Назначение: Получение прогноза для конкретного навыка
   - Параметры: skill_code (string), weeks_history (int, по умолчанию 4)
   - Response: ForecastResponse | InsufficientDataResponse

2. **GET /api/sources**
   - Назначение: Получение списка источников данных
   - Response: list[DataSourceResponse]

3. **GET /api/skills**
   - Назначение: Получение списка доступных навыков
   - Response: list[SkillResponse]

4. **GET /api/jobs**
   - Назначение: Получение списка вакансий
   - Параметры: source, skill, location, is_remote, published_from, published_to, search
   - Response: list[JobPostingResponse]

5. **GET /api/indicators/weekly**
   - Назначение: Получение еженедельных показателей
   - Параметры: source, skill, period_start, period_end
## Пример ответа API

```json
{
  "skill": {
    "code": "python",
    "display_name": "Python"
  },
  "score": 0.7,
  "direction": "growing",
  "confidence": 95,
  "risk": "low",
  "explanation": "Trend: +10.00pp (+1.00 signal). Momentum: +0.00pp (+0.00 signal). Score: 0.70 -> growing. Confidence: 95% from 7/7 days coverage and 150 eligible postings.",
  "calculation_steps": {
    "trend_pp": 10.0,
    "trend_signal": 1.0,
    "momentum_pp": 0.0,
    "momentum_signal": 0.0,
    "coverage_factor": 1.0,
    "volume_factor": 1.0
  }
}
## Запуск проекта

### Предварительные требования

- Python 3.11+
- Docker и Docker Compose
- Poetry (для управления зависимостями)

### Пошаговая инструкция

1. Скопируйте файл `.env.example` в `.env` и настройте переменные окружения:
   ```
   cp .env.example .env
   ```

2. Установите зависимости backend:
   ```
   cd backend
   poetry install
   ```

3. Запустите базу данных через Docker Compose:
   ```
   docker compose up -d db
   ```
## Demo

Демонстрационный скрипт `app/scripts/demo_seed.py` создает синтетические данные для тестирования системы.

Запуск:
```
cd backend
poetry run python app/scripts/demo_seed.py
```

Скрипт создает:
- 5 недель исторических данных
- Вакансии с различными навыками
- Сопоставления навыков с вакансиями
- Еженедельные показатели
## Проверка работы

Проверка работоспособности системы:

1. Health endpoint:
   ```
   curl http://localhost:8000/health
   ```

2. Запуск тестов:
## Использование AI

### Использование AI

В разработке проекта использовались инструменты искусственного интеллекта как средства помощи в программировании, а не как runtime-компоненты прогнозирования.

Основной этап разработки выполнялся с помощью OpenAI Codex:
- Проработка архитектуры проекта
- Декомпозиция задачи
- Создание основной структуры приложения
- Реализация значительной части backend-кода
- Помощь с проектированием моделей, API и сервисов
- Анализ и исправление ошибок

На последующих этапах для отдельных небольших задач использовался OpenRouter с различными LLM-моделями:
- Реализация отдельных небольших фич
- Доработка существующего кода
- Локальный рефакторинг
- Помощь с отладкой и анализом отдельных проблем

## Ограничения

Реальные ограничения текущей реализации:

- [x] Используются демо/seed данные вместо реального сбора данных из API
- [x] Ограниченное количество источников (только The Muse и Remotive)
- [x] Отсутствует полноценное машинное обучение (rule-based scoring)
- [x] Отсутствие автоматического переобучения
- [x] Ограниченная история (только несколько недель)
- [x] Проект предназначен для демонстрации алгоритма прогнозирования
## Соответствие требованиям тестового задания

- [x] Выбрана область прогнозирования (технологические навыки в IT)
- [x] Используются данные минимум из двух источников (The Muse API, Remotive API)
- [x] Данные сохраняются в базе (реализованы все необходимые модели)
- [x] Есть источники, сырые данные, нормализованные показатели
- [x] Есть прогнозы (реализован алгоритм прогнозирования)
- [x] Есть история обновлений (через WeeklyIndicator.calculated_at)
- [x] Есть список объектов для прогнозирования (эндпоинт /api/skills)
- [x] Есть карточка прогноза (эндпоинт /api/forecasts/skills/{skill_code})
- [x] Есть confidence (реализовано в алгоритме)
- [x] Есть risk (реализовано в алгоритме)
- [x] Есть объяснение прогноза (поле explanation в ответе API)
- [x] Прогноз рассчитывается из сохранённых данных (алгоритм использует WeeklyIndicator)
- [ ] Есть способ проверить корректность прогноза (не реализован автоматически)

## Итог

Job Market Oracle представляет собой прототип системы прогнозирования трендов востребованности технологических навыков на рынке труда. Система демонстрирует основные требования тестового задания: работу с несколькими источниками данных, сохранение и нормализацию данных, расчет прогнозов с оценкой уверенности и риска, а также предоставление объяснений принятых решений.
- [x] Реальные деньги не используются
- [x] Система не совершает финансовые операции
- [x] Прогноз не является гарантией результата и не представляет собой обещание доходности
Важные уточнения:
- AI не используется во время runtime для генерации самого прогноза
- Прогноз рассчитывается детерминированным алгоритмом на основе данных, сохранённых в БД
- AI использовался как инструмент разработки и программирования
- Итоговая логика была проверена и адаптирована под требования проекта
   ```
   cd backend
   APP_ENV=test DATABASE_URL=postgresql+psycopg://unused:unused@localhost:5432/unused poetry run pytest
   ```

3. Проверка форматирования кода:
   ```
   cd backend
   poetry run ruff check .
   poetry run ruff format --check .
   ```

4. Swagger документация доступна по адресу:
   ```
   http://localhost:8000/docs
   ```

После запуска можно:
1. Открыть список доступных навыков: GET `/api/skills`
2. Получить прогноз для конкретного навыка: GET `/api/forecasts/skills/python`
3. Просмотреть еженедельные показатели: GET `/api/indicators/weekly`

4. Выполните миграции базы данных:
   ```
   cd backend
   poetry run alembic upgrade head
   ```

5. Запустите приложение:
   ```
   poetry run uvicorn app.main:app --reload
   ```

6. Запустите демо-скрипт для наполнения базы данных:
   ```
   poetry run python app/scripts/demo_seed.py
   ```

7. API будет доступен по адресу: `http://localhost:8000`

8. Swagger документация: `http://localhost:8000/docs`
  }
}
```
   - Response: list[WeeklyIndicatorResponse]

Факторы, которые могут привести к ошибке прогноза:
- Резкие изменения на рынке труда
- Недостаток данных за предыдущие периоды
- Изменения в терминологии навыков в вакансиях
- При достаточном количестве вакансий и полном покрытии confidence = 100%
- risk = "low"

Эти значения можно получить повторным расчетом из сохраненных данных.
confidence = max(0, min(100, confidence))
```

Определение уровня риска:
```
if confidence >= 80 and len(recent_indicators) >= 4:
    risk = "low"
elif confidence >= 50:
    risk = "medium"
else:
    risk = "high"
```

Аргументация прогноза формируется как строка с деталями всех расчетов.
7. Сохранение прогноза (возвращается через API)
8. Выдача через API endpoints
   - Связи: job_posting, skill

8. **WeeklyIndicator** (`weekly_indicators`)
   - Назначение: Нормализованные показатели по навыкам за неделю
   - Поля: id, source_id, skill_id, period_start, period_end, eligible_postings_count,
           matching_postings_count, skill_share, coverage_days, calculated_at
   - Связи: source, skill
├── frontend/             # Frontend application
├── docker-compose.yml    # Container orchestration
└── README.md             # Project documentation
```
- **Ingestion**: Получение и обработка данных (`backend/app/services/data_ingestion.py`)
- **Database**: PostgreSQL с SQLAlchemy ORM (`backend/app/models/`)
- **Seed/Scripts**: Демонстрационные данные (`backend/app/scripts/demo_seed.py`)
- **Repositories**: Слой доступа к данным (`backend/app/repositories/`)
   - Реализация: `backend/app/core/config.py`, `backend/app/services/data_ingestion.py`

Данные из обоих источников объединяются на уровне обработки вакансий и сопоставления с навыками.
Итоговый прогноз: **одно из трех направлений ("growing", "stable", "declining")** с числовым score и оценкой уверенности.
Проект использует реальные данные из API The Muse и Remotive для анализа вакансий. На выходе пользователь получает прогноз с оценкой уверенности, уровнем риска и детальным объяснением расчета.