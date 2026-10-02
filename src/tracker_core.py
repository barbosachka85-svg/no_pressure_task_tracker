"""
Мозг доброго трекера.

Это логика из консольной версии: те же сообщения, те же правила сердечек,
тот же формат tracker_data.json. Функции только считают и меняют данные,
а показывают результат уже интерфейсы: консоль (tracker.py) или
приложение на телефоне (main.py).
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ==================== ДОБРЫЕ СООБЩЕНИЯ ====================
MESSAGES = {
    "welcome": "🌸 Привет! Это твой добрый трекер задач.",
    "greeting": "🌼 Что хочешь сделать сегодня?",
    "goodbye": "🌸 До встречи! Помни: ты уже сегодня молодец просто потому, что заботишься о себе. 💕",
    "add_task_prompt": "📝 Напиши название задачи (или просто Enter, чтобы вернуться в меню):",
    "task_type_prompt": "Это длинная или короткая задача? (д/к):",
    "long_task_hint": "✨ Это длинная задача. Можно отмечать прогресс зелёными сердечками, даже если ты просто немного поработала над ней. Каждый шаг важен! 🌱",
    "short_task_hint": "⚡ Это короткая задача. Сделаешь — получишь золотое сердечко!",
    "task_added": "✅ Задача «{title}» добавлена! Ты молодец, что начала её отслеживать.",
    "empty_title": "🌱 Название не может быть пустым. Задача не добавлена.",
    "no_tasks": "🌱 В списке пока нет задач. Добавь что-нибудь, даже маленькое!",
    "select_task": "Выбери задачу (номер, 0 — назад в меню):",
    "long_task_options": "Что ты сделала с длинной задачей?\n1. 💚 Поработала над ней (зеленое сердечко, задача остается)\n2. 💛 Закончила полностью (золотое сердечко, задача в архив)\n0. ↩️ Назад в меню\nТвой выбор:",
    "green_heart": "💚 Зеленое сердечко для «{title}»! Ты приближаешься к цели. Я тобой горжусь.",
    "gold_heart": "💛 Золотое сердечко! Ты завершила «{title}». Это победа! 🎉",
    "task_completed_short": "💛 Золотое сердечко для «{title}»! Короткая задача выполнена. Ты супер! ✨",
    "invalid_choice": "🌱 Ой, я не понимаю. Давай попробуем еще раз? Просто выбери номер из списка.",
    "task_of_day": "🎲 Твоя задача дня:\n\n«{title}»\n\nЭто {task_type} задача.\n{encouragement}\nГлавное — не дави на себя. Завтра будет новый день 🌷",
    "tod_long": "Ты можешь отметить прогресс зелёным сердечком, даже если просто немного поработаешь над ней. 🌱",
    "tod_short": "Сделаешь — получишь золотое сердечко! ✨",
    "tod_soft": "Главное — не дави на себя. Завтра будет новый день 🌷",
    "no_tasks_for_tod": "🌸 В списке нет активных задач. Добавь что-нибудь, и я выберу задачу дня!",
    "no_stats": "🌸 Пока нет статистики. Добавляй задачи и отмечай прогресс — и здесь появятся твои достижения!",
    "stats_header_7": "📊 Твоя статистика за последние 7 дней:",
    "stats_header_30": "📊 Твоя статистика за последние 30 дней:",
    "short_count": "✨ Коротких задач завершено: {count}\n   (ты быстро справляешься с мелкими делами — это отлично!)",
    "green_count": "💚 Зеленых сердечек (прогресс по длинным задачам): {count}\n   (ты двигаешь длинные задачи вперед)",
    "gold_long_count": "💛 Золотых сердечек (завершенные длинные задачи): {count}\n   (большие цели достигнуты — это серьезное достижение!)",
    "short_caption": "ты быстро справляешься с мелкими делами — это отлично!",
    "green_caption": "ты двигаешь длинные задачи вперед",
    "gold_caption": "большие цели достигнуты — это серьезное достижение!",
    "praise": "🌸 Ты молодец! Даже просто заглянуть в трекер и посмотреть статистику — уже забота о себе. 🌸",
    "menu": """
🌼 МЕНЮ 🌼
1. 📝 Добавить задачу
2. ✨ Отметить прогресс (сердечко)
3. 🎲 Задача дня
4. 📊 Статистика
5. 📋 Посмотреть активные задачи
6. 🚪 Выход

Твой выбор: """,
    "error": "🌱 Что-то пошло не так. Но это не страшно! Давай попробуем еще раз.",
    "select_period": "\n📊 Показать подробную таблицу длинных задач за:",
    "select_7": "   1. 7 дней",
    "select_30": "   2. 30 дней",
    "select_skip": "   0. Пропустить",
    "your_choice": "   Ваш выбор: ",
    "table_header": "📊 Подробная таблица длинных задач (за {days} дней):",
    "no_long_tasks": "📭 Нет данных о длинных задачах за этот период",
    "table_legend": "💚 — зеленое сердечко (обычный прогресс)\n💛 — золотое сердечко (завершение длинной задачи)",
    "saved_copy": "💾 Копия сохранена. Ты бережёшь свои достижения — это мудро.",
    "imported": "📥 Данные загружены. С возвращением! 🌸",
    "bad_file": "🌱 Этот файл не похож на данные трекера. Попробуй другой?",
}

# ==================== РАБОТА С ДАННЫМИ ====================
# На телефоне Flet делает рабочей папкой личную папку приложения,
# поэтому файл с этим именем живёт там же, где и раньше: "рядом с программой".
DATA_FILE = "tracker_data.json"


def empty_data() -> Dict:
    return {"tasks": [], "history": [], "next_id": 1}


def is_valid_data(data) -> bool:
    """Похоже ли это на данные трекера"""
    return (
        isinstance(data, dict)
        and isinstance(data.get("tasks"), list)
        and isinstance(data.get("history"), list)
        and isinstance(data.get("next_id"), int)
    )


def load_data(path: str = DATA_FILE) -> Dict:
    """Загружает данные из файла"""
    if not os.path.exists(path):
        return empty_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if is_valid_data(data) else empty_data()
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return empty_data()


def save_data(data: Dict, path: str = DATA_FILE) -> None:
    """Сохраняет данные в файл (сначала во временный, чтобы не испортить при сбое)"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def data_to_json(data: Dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def data_from_json(text: str) -> Optional[Dict]:
    """Разбирает текст файла. Возвращает None, если это не данные трекера."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return data if is_valid_data(data) else None


# ==================== ЗАДАЧИ ====================
def active_tasks(data: Dict) -> List[Dict]:
    return [t for t in data["tasks"] if t.get("status") == "active"]


def type_name(task_type: str) -> str:
    return "длинная" if task_type == "long" else "короткая"


def type_hint(task_type: str) -> str:
    return MESSAGES["long_task_hint"] if task_type == "long" else MESSAGES["short_task_hint"]


def parse_task_type(answer: str) -> Optional[str]:
    """'д'/'long' → long, 'к'/'short' → short, иначе None"""
    answer = answer.strip().lower()
    if answer in ("д", "long"):
        return "long"
    if answer in ("к", "short"):
        return "short"
    return None


def add_task(data: Dict, title: str, task_type: str) -> Tuple[bool, str]:
    """Добавляет новую задачу. Возвращает (получилось ли, сообщение)."""
    title = title.strip()
    if not title:
        return False, MESSAGES["empty_title"]

    task = {
        "id": data["next_id"],
        "title": title,
        "type": task_type,
        "status": "active",
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    return True, MESSAGES["task_added"].format(title=title)


def find_task(data: Dict, task_id: int) -> Optional[Dict]:
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def _log(data: Dict, task: Dict, action: str) -> None:
    data["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "task_id": task["id"],
        "task_title": task["title"],
        "task_type": task["type"],
        "action": action,
    })


def mark_green(data: Dict, task_id: int) -> str:
    """Зеленое сердечко — прогресс по длинной задаче, задача остается"""
    task = find_task(data, task_id)
    if task is None or task["type"] != "long":
        return MESSAGES["invalid_choice"]
    _log(data, task, "green_heart")
    save_data(data)
    return MESSAGES["green_heart"].format(title=task["title"])


def mark_gold(data: Dict, task_id: int) -> str:
    """Золотое сердечко — задача завершена и уходит из списка"""
    task = find_task(data, task_id)
    if task is None:
        return MESSAGES["invalid_choice"]
    _log(data, task, "gold_heart")
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    if task["type"] == "long":
        return MESSAGES["gold_heart"].format(title=task["title"])
    return MESSAGES["task_completed_short"].format(title=task["title"])


def green_hearts_for(data: Dict, task_id: int) -> int:
    return sum(1 for h in data["history"]
               if h.get("task_id") == task_id and h.get("action") == "green_heart")


# ==================== ЗАДАЧА ДНЯ ====================
def task_of_day(data: Dict) -> Optional[Dict]:
    """Выбирает случайную задачу дня (или None, если задач нет)"""
    tasks = active_tasks(data)
    if not tasks:
        return None
    return random.choice(tasks)


def task_of_day_encouragement(task: Dict) -> str:
    return MESSAGES["tod_long"] if task["type"] == "long" else MESSAGES["tod_short"]


def task_of_day_text(task: Dict) -> str:
    return MESSAGES["task_of_day"].format(
        title=task["title"],
        task_type=type_name(task["type"]),
        encouragement=task_of_day_encouragement(task),
    )


# ==================== СТАТИСТИКА ====================
def get_stats(data: Dict, days: int) -> Dict:
    """Получает статистику за указанное количество дней"""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered_history = [h for h in data["history"] if h["date"] >= cutoff_date]

    short_count = sum(1 for h in filtered_history
                      if h["task_type"] == "short" and h["action"] == "gold_heart")
    green_count = sum(1 for h in filtered_history
                      if h["task_type"] == "long" and h["action"] == "green_heart")
    gold_long_count = sum(1 for h in filtered_history
                          if h["task_type"] == "long" and h["action"] == "gold_heart")

    return {
        "short": short_count,
        "green": green_count,
        "gold_long": gold_long_count,
        "total_entries": len(filtered_history),
    }


def long_tasks_table(data: Dict, days: int) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    """
    Данные для таблицы длинных задач.
    Возвращает (даты по порядку в виде "дд.мм", {название: {дата: "green"/"gold"}}).
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    tasks_data: Dict[str, Dict[str, str]] = {}
    all_dates = set()

    for entry in data["history"]:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
        if entry_date < cutoff_date:
            continue
        if entry.get("task_type", "short") != "long":
            continue
        day = entry["date"]  # ГГГГ-ММ-ДД сортируется правильно и через Новый год
        heart = "green" if entry["action"] == "green_heart" else "gold"
        cells = tasks_data.setdefault(entry["task_title"], {})
        if cells.get(day) != "gold":  # золотое важнее зелёного в тот же день
            cells[day] = heart
        all_dates.add(day)

    sorted_days = sorted(all_dates)
    label = {d: d[8:10] + "." + d[5:7] for d in sorted_days}
    rows = {name: {label[d]: h for d, h in cells.items()} for name, cells in tasks_data.items()}
    return [label[d] for d in sorted_days], rows
