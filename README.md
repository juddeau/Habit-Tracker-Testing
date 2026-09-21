# Habit Tracker 🔥

Веб-приложение для отслеживания привычек: бэкенд на **FastAPI** (SQLite), фронтенд — чистые **HTML/CSS/JS** без сборщиков и фреймворков.

![status](https://img.shields.io/badge/status-demo-orange)

---

## Возможности

- Создание, редактирование и удаление привычек (иконка + цвет)
- Отметка «выполнено сегодня»
- Текущий стрик (серия дней подряд), процент выполнения, общее число отметок
- Общая статистика по всем привычкам
- Тёмный адаптивный интерфейс

---

## Структура проекта

```
habit-tracker/
├── backend/
│   ├── main.py            # FastAPI-приложение + SQLite
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── README.md
```

---

## Запуск

### 1. Бэкенд (FastAPI)

Требуется Python 3.9+.

```bash
cd habit-tracker/backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

После запуска:
- API доступно на `http://127.0.0.1:8000`
- Интерактивная документация (Swagger) — `http://127.0.0.1:8000/docs`
- База данных `habits.db` создаётся автоматически в папке `backend/` при первом запуске

### 2. Фронтенд

Фронтенд — статические файлы, backend отдельно их не раздаёт. Проще всего поднять локальный веб-сервер прямо в папке `frontend/`:

```bash
cd habit-tracker/frontend
python3 -m http.server 5500
```

Открыть в браузере: **http://127.0.0.1:5500**

> Открывать `index.html` двойным кликом (`file://...`) не стоит — часть браузеров тогда блокирует запросы `fetch` к API. Через `http.server` всё работает штатно.

Адрес API прописан в `frontend/app.js` в константе:

```js
const API_BASE = "http://127.0.0.1:8000/api";
```

Если бэкенд запущен на другом хосте/порту — поменяйте эту строку.

### 3. Проверка

Откройте `http://127.0.0.1:5500`, добавьте привычку через кнопку **«+ Новая привычка»**, отметьте её выполненной. Если карточка появилась и обновилась статистика сверху — всё работает.

---

## API (кратко)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/habits` | Список привычек с посчитанной статистикой |
| POST | `/api/habits` | Создать привычку `{name, icon, color}` |
| PUT | `/api/habits/{id}` | Обновить привычку |
| DELETE | `/api/habits/{id}` | Удалить привычку |
| POST | `/api/habits/{id}/checkins` | Отметить выполнение сегодня |
| DELETE | `/api/habits/{id}/checkins/{date}` | Убрать отметку за дату (`YYYY-MM-DD`) |
| GET | `/api/stats` | Общая статистика |

---

## Технологии

- **Backend:** Python 3, FastAPI, Uvicorn, SQLite (стандартная библиотека `sqlite3`)
- **Frontend:** HTML5, CSS3 (без препроцессоров), Vanilla JS (без сборки и фреймворков)
