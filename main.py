import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ==================== ДОБРЫЕ СООБЩЕНИЯ ====================
MESSAGES = {
    "welcome": "🌸 Привет! Это твой добрый трекер задач.",
    "greeting": "🌼 Что хочешь сделать сегодня?",
    "goodbye": "🌸 До встречи! Помни: ты уже сегодня молодец просто потому, что заботишься о себе. 💕",
    "add_task_prompt": "📝 Напиши название задачи:",
    "task_type_prompt": "Это длинная или короткая задача? (д/к):",
    "long_task_hint": "✨ Это длинная задача. Можно отмечать прогресс зелёными сердечками, даже если ты просто немного поработала над ней. Каждый шаг важен! 🌱",
    "short_task_hint": "⚡ Это короткая задача. Сделаешь — получишь золотое сердечко!",
    "task_added": "✅ Задача «{title}» добавлена! Ты молодец, что начала её отслеживать.",
    "no_tasks": "🌱 В списке пока нет задач. Добавь что-нибудь, даже маленькое!",
    "select_task": "Выбери задачу (номер):",
    "long_task_options": "Что ты сделала с длинной задачей?\n1. 💚 Поработала над ней (зеленое сердечко, задача остается)\n2. 💛 Закончила полностью (золотое сердечко, задача в архив)\nТвой выбор:",
    "green_heart": "💚 Зеленое сердечко для «{title}»! Ты приближаешься к цели. Я тобой горжусь.",
    "gold_heart": "💛 Золотое сердечко! Ты завершила «{title}». Это победа! 🎉",
    "task_completed_short": "💛 Золотое сердечко для «{title}»! Короткая задача выполнена. Ты супер! ✨",
    "invalid_choice": "🌱 Ой, я не понимаю. Давай попробуем еще раз? Просто выбери номер из списка.",
    "task_of_day": "🎲 Твоя задача дня:\n\n«{title}»\n\nЭто {task_type} задача.\n{encouragement}\nГлавное — не дави на себя. Завтра будет новый день 🌷",
    "no_tasks_for_tod": "🌸 В списке нет активных задач. Добавь что-нибудь, и я выберу задачу дня!",
    "stats_header_7": "📊 Твоя статистика за последние 7 дней:",
    "stats_header_30": "📊 Твоя статистика за последние 30 дней:",
    "short_count": "✨ Коротких задач завершено: {count}\n   (ты быстро справляешься с мелкими делами — это отлично!)",
    "green_count": "💚 Зеленых сердечек (прогресс по длинным задачам): {count}\n   (ты двигаешь длинные задачи вперед)",
    "gold_long_count": "💛 Золотых сердечек (завершенные длинные задачи): {count}\n   (большие цели достигнуты — это серьезное достижение!)",
    "praise": "\n🌸 Ты молодец! Даже просто заглянуть в трекер и посмотреть статистику — уже забота о себе. 🌸",
    "menu": """
🌼 МЕНЮ 🌼
1. 📝 Добавить задачу
2. ✨ Отметить прогресс (сердечко)
3. 🎲 Задача дня
4. 📊 Статистика
5. 🚪 Выход

Твой выбор: """,
    "error": "🌱 Что-то пошло не так. Но это не страшно! Давай попробуем еще раз.",
    # Новые сообщения для таблицы
    "select_period": "\n📊 Показать подробную таблицу длинных задач за:",
    "select_7": "   1. 7 дней",
    "select_30": "   2. 30 дней",
    "select_skip": "   0. Пропустить",
    "your_choice": "   Ваш выбор: ",
    "table_header": "📊 Подробная таблица длинных задач (за {days} дней):",
    "no_long_tasks": "   📭 Нет данных о длинных задачах за этот период",
    "table_legend": "\n   💚 — зеленое сердечко (обычный прогресс)\n   💛 — золотое сердечко (завершение длинной задачи)",
}

# ==================== РАБОТА С ДАННЫМИ ====================
DATA_FILE = "tracker_data.json"


def load_data() -> Dict:
    """Загружает данные из файла"""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "history": [], "next_id": 1}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"tasks": [], "history": [], "next_id": 1}


def save_data(data: Dict) -> None:
    """Сохраняет данные в файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== МОДУЛЬ ТАБЛИЦ ====================

def show_long_tasks_table(data: Dict, days: int) -> None:
    """
    Показывает таблицу длинных задач с датами и сердечками

    Args:
        data: словарь с данными (tasks и history)
        days: количество дней (7 или 30)
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    # Создаем словарь для быстрого доступа к типу задачи
    task_types = {task["id"]: task["type"] for task in data["tasks"]}

    # Собираем данные по длинным задачам из истории
    tasks_data = {}  # {название_задачи: {дата: тип_сердечка}}
    all_dates = set()

    for entry in data["history"]:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")

        if entry_date >= cutoff_date:
            task_type = entry.get("task_type", "short")
            if task_type == "long":
                date_str = entry_date.strftime("%d.%m")
                task_title = entry["task_title"]
                action = entry["action"]  # "green_heart" или "gold_heart"
                heart_type = "green" if action == "green_heart" else "gold"

                if task_title not in tasks_data:
                    tasks_data[task_title] = {}
                tasks_data[task_title][date_str] = heart_type
                all_dates.add(date_str)

    if not tasks_data:
        print(f"\n{MESSAGES['no_long_tasks']}")
        return

    # Сортируем даты
    sorted_dates = sorted(all_dates, key=lambda x: (x.split(".")[1], x.split(".")[0]))

    # Ширина колонки для названий задач
    max_task_len = max(len(task) for task in tasks_data.keys())
    task_col_width = min(max_task_len + 2, 30)

    # Фиксированная ВИЗУАЛЬНАЯ ширина колонки для даты/сердечка
    COL_WIDTH = 6

    # Вспомогательная функция: центрирует текст с учётом двойной ширины эмодзи
    def pad_center(text: str, width: int) -> str:
        # Эмодзи обычно занимают 2 ячейки терминала, остальные символы - 1
        display_len = sum(2 if ord(c) > 0x1F00 else 1 for c in text)
        padding = width - display_len
        if padding <= 0:
            return text
        left = padding // 2
        right = padding - left
        return " " * left + text + " " * right

    # Точный расчёт общей ширины таблицы
    dates_cols_width = len(sorted_dates) * (COL_WIDTH + 1)  # +1 для разделителя │
    total_width = task_col_width + dates_cols_width + 1  # +1 для правого края

    # Верхняя граница
    print("\n   " + "─" * total_width)

    # Заголовок
    print(f"   {'Задача':<{task_col_width}}", end="")
    for date in sorted_dates:
        print(f"│{pad_center(date, COL_WIDTH)}", end="")
    print("│")

    # Разделительная линия
    print("   " + "─" * total_width)

    # Строки с задачами
    for task_name, dates_dict in tasks_data.items():
        display_name = (task_name[:task_col_width - 5] + "..."
                        if len(task_name) > task_col_width - 2
                        else task_name)

        print(f"   {display_name:<{task_col_width}}", end="")
        for date in sorted_dates:
            heart = dates_dict.get(date)
            if heart == "green":
                symbol = "💚"
            elif heart == "gold":
                symbol = "💛"
            else:
                symbol = ""
            print(f"│{pad_center(symbol, COL_WIDTH)}", end="")
        print("│")

    # Нижняя граница
    print("   " + "─" * total_width)
    print(MESSAGES['table_legend'])


def show_stats_with_table_choice(data: Dict) -> None:
    """
    Показывает статистику и предлагает выбор таблицы
    """
    if not data["history"]:
        print("\n🌸 Пока нет статистики. Добавляй задачи и отмечай прогресс — и здесь появятся твои достижения!")
        return

    # Статистика за 7 дней
    stats_7 = get_stats(data, 7)
    print(f"\n{MESSAGES['stats_header_7']}")
    print(MESSAGES['short_count'].format(count=stats_7["short"]))
    print(MESSAGES['green_count'].format(count=stats_7["green"]))
    print(MESSAGES['gold_long_count'].format(count=stats_7["gold_long"]))

    # Статистика за 30 дней
    stats_30 = get_stats(data, 30)
    print(f"\n{MESSAGES['stats_header_30']}")
    print(MESSAGES['short_count'].format(count=stats_30["short"]))
    print(MESSAGES['green_count'].format(count=stats_30["green"]))
    print(MESSAGES['gold_long_count'].format(count=stats_30["gold_long"]))

    # Спрашиваем, хочет ли пользователь увидеть таблицу
    print(f"\n{MESSAGES['select_period']}")
    print(MESSAGES['select_7'])
    print(MESSAGES['select_30'])
    print(MESSAGES['select_skip'])

    try:
        choice = input(MESSAGES['your_choice']).strip()

        if choice == "1":
            print(f"\n{MESSAGES['table_header'].format(days=7)}")
            show_long_tasks_table(data, 7)
        elif choice == "2":
            print(f"\n{MESSAGES['table_header'].format(days=30)}")
            show_long_tasks_table(data, 30)
        elif choice == "0":
            pass  # Пропускаем таблицу
        else:
            print("\n   ⚠️ Неверный выбор. Таблица не будет показана.")
    except KeyboardInterrupt:
        print("\n")
        return

    print(MESSAGES['praise'])


# ==================== ФУНКЦИИ ТРЕКЕРА ====================
def add_task(data: Dict) -> Dict:
    """Добавляет новую задачу"""
    print(f"\n{MESSAGES['add_task_prompt']}")
    title = input().strip()
    if not title:
        print("🌱 Название не может быть пустым. Задача не добавлена.")
        return data

    print(MESSAGES['task_type_prompt'])
    task_type = input().strip().lower()

    while task_type not in ['д', 'к', 'long', 'short']:
        print(MESSAGES['invalid_choice'])
        task_type = input().strip().lower()

    if task_type in ['д', 'long']:
        task_type = 'long'
        print(f"\n{MESSAGES['long_task_hint']}")
    else:
        task_type = 'short'
        print(f"\n{MESSAGES['short_task_hint']}")

    task = {
        "id": data["next_id"],
        "title": title,
        "type": task_type,
        "status": "active"
    }

    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)

    print(f"\n{MESSAGES['task_added'].format(title=title)}")
    return data


def show_active_tasks(tasks: List[Dict]) -> None:
    """Показывает активные задачи"""
    if not tasks:
        print(MESSAGES['no_tasks'])
        return

    print("\n📋 Твои активные задачи:")
    for i, task in enumerate(tasks, 1):
        type_emoji = "📖" if task["type"] == "long" else "⚡"
        type_name = "длинная" if task["type"] == "long" else "короткая"
        print(f"  {i}. {type_emoji} {task['title']} ({type_name})")


def mark_done(data: Dict) -> Dict:
    """Отмечает прогресс по задаче"""
    active_tasks = [t for t in data["tasks"] if t["status"] == "active"]

    if not active_tasks:
        print(MESSAGES['no_tasks'])
        return data

    show_active_tasks(active_tasks)
    print(MESSAGES['select_task'])

    try:
        choice = int(input().strip()) - 1
        if choice < 0 or choice >= len(active_tasks):
            print(MESSAGES['invalid_choice'])
            return data

        task = active_tasks[choice]
        today = datetime.now().strftime("%Y-%m-%d")

        if task["type"] == "long":
            print(MESSAGES['long_task_options'])
            action = input().strip()

            if action == "1":
                # Зеленое сердечко — прогресс, задача остается
                data["history"].append({
                    "date": today,
                    "task_id": task["id"],
                    "task_title": task["title"],
                    "task_type": "long",
                    "action": "green_heart"
                })
                save_data(data)
                print(f"\n{MESSAGES['green_heart'].format(title=task['title'])}")

            elif action == "2":
                # Золотое сердечко — завершение, задача удаляется
                data["history"].append({
                    "date": today,
                    "task_id": task["id"],
                    "task_title": task["title"],
                    "task_type": "long",
                    "action": "gold_heart"
                })
                # Удаляем задачу из списка
                data["tasks"] = [t for t in data["tasks"] if t["id"] != task["id"]]
                save_data(data)
                print(f"\n{MESSAGES['gold_heart'].format(title=task['title'])}")
            else:
                print(MESSAGES['invalid_choice'])

        else:  # short task
            # Короткая задача — сразу золотое сердечко и удаление
            data["history"].append({
                "date": today,
                "task_id": task["id"],
                "task_title": task["title"],
                "task_type": "short",
                "action": "gold_heart"
            })
            data["tasks"] = [t for t in data["tasks"] if t["id"] != task["id"]]
            save_data(data)
            print(f"\n{MESSAGES['task_completed_short'].format(title=task['title'])}")

    except ValueError:
        print(MESSAGES['invalid_choice'])

    return data


def task_of_day(data: Dict) -> None:
    """Выбирает случайную задачу дня"""
    active_tasks = [t for t in data["tasks"] if t["status"] == "active"]

    if not active_tasks:
        print(MESSAGES['no_tasks_for_tod'])
        return

    task = random.choice(active_tasks)
    task_type = "длинная" if task["type"] == "long" else "короткая"

    encouragement = "Ты можешь отметить прогресс зелёным сердечком, даже если просто немного поработаешь над ней. 🌱" if \
        task["type"] == "long" else "Сделаешь — получишь золотое сердечко! ✨"

    print(f"\n{MESSAGES['task_of_day'].format(title=task['title'], task_type=task_type, encouragement=encouragement)}")


def get_stats(data: Dict, days: int) -> Dict:
    """Получает статистику за указанное количество дней"""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered_history = [
        h for h in data["history"]
        if h["date"] >= cutoff_date
    ]

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
        "total_entries": len(filtered_history)
    }


def show_stats(data: Dict) -> None:
    """
    Показывает статистику (оригинальная функция)
    Используется для совместимости с существующим кодом
    """
    show_stats_with_table_choice(data)


def main():
    data = load_data()
    print(MESSAGES['welcome'])
    print(MESSAGES['greeting'])

    while True:
        try:
            choice = input(MESSAGES['menu']).strip()

            if choice == "1":
                data = add_task(data)
            elif choice == "2":
                data = mark_done(data)
            elif choice == "3":
                task_of_day(data)
            elif choice == "4":
                show_stats(data)
            elif choice == "5":
                print(f"\n{MESSAGES['goodbye']}")
                break
            else:
                print(MESSAGES['invalid_choice'])

        except KeyboardInterrupt:
            print(f"\n\n{MESSAGES['goodbye']}")
            break
        except Exception as e:
            print(f"{MESSAGES['error']} ({e})")


if __name__ == "__main__":
    main()