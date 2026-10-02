"""
Консольная версия доброго трекера.
Логика живёт в src/tracker_core.py — той же, что и в приложении на телефоне,
поэтому tracker_data.json подходит обоим.

Запуск:  python tracker.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import tracker_core as core  # noqa: E402
from tracker_core import MESSAGES  # noqa: E402


# ==================== ВЫВОД ТАБЛИЦЫ ====================
def show_long_tasks_table(data, days):
    dates, rows = core.long_tasks_table(data, days)
    if not rows:
        print(f"\n   {MESSAGES['no_long_tasks']}")
        return

    task_col_width = min(max(len(t) for t in rows) + 2, 30)
    COL_WIDTH = 6

    def pad_center(text, width):
        # Эмодзи обычно занимают 2 ячейки терминала, остальные символы - 1
        display_len = sum(2 if ord(c) > 0x1F00 else 1 for c in text)
        padding = width - display_len
        if padding <= 0:
            return text
        left = padding // 2
        return " " * left + text + " " * (padding - left)

    total_width = task_col_width + len(dates) * (COL_WIDTH + 1) + 1
    line = "   " + "─" * total_width

    print("\n" + line)
    print(f"   {'Задача':<{task_col_width}}" + "".join(f"│{pad_center(d, COL_WIDTH)}" for d in dates) + "│")
    print(line)
    for name, cells in rows.items():
        shown = name[:task_col_width - 5] + "..." if len(name) > task_col_width - 2 else name
        symbols = {"green": "💚", "gold": "💛"}
        print(f"   {shown:<{task_col_width}}"
              + "".join(f"│{pad_center(symbols.get(cells.get(d), ''), COL_WIDTH)}" for d in dates) + "│")
    print(line)
    print("\n" + "\n".join("   " + l for l in MESSAGES["table_legend"].splitlines()))


# ==================== ЭКРАНЫ ====================
def show_active_tasks(tasks):
    if not tasks:
        print(MESSAGES["no_tasks"])
        return
    print("\n📋 Твои активные задачи:")
    for i, task in enumerate(tasks, 1):
        emoji = "📖" if task["type"] == "long" else "⚡"
        print(f"  {i}. {emoji} {task['title']} ({core.type_name(task['type'])})")


def add_task(data):
    print(f"\n{MESSAGES['add_task_prompt']}")
    title = input().strip()
    if not title:
        return  # пустой ввод — назад в меню
    print(MESSAGES["task_type_prompt"])
    task_type = core.parse_task_type(input())
    while task_type is None:
        print(MESSAGES["invalid_choice"])
        task_type = core.parse_task_type(input())
    print(f"\n{core.type_hint(task_type)}")
    ok, message = core.add_task(data, title, task_type)
    print(f"\n{message}")


def mark_done(data):
    tasks = core.active_tasks(data)
    if not tasks:
        print(MESSAGES["no_tasks"])
        return
    show_active_tasks(tasks)
    print(MESSAGES["select_task"])
    try:
        choice = int(input().strip()) - 1
    except ValueError:
        print(MESSAGES["invalid_choice"])
        return
    if choice == -1:
        return  # 0 — назад в меню
    if not 0 <= choice < len(tasks):
        print(MESSAGES["invalid_choice"])
        return

    task = tasks[choice]
    if task["type"] == "long":
        print(MESSAGES["long_task_options"])
        action = input().strip()
        if action == "1":
            print(f"\n{core.mark_green(data, task['id'])}")
        elif action == "2":
            print(f"\n{core.mark_gold(data, task['id'])}")
        elif action == "0":
            return
        else:
            print(MESSAGES["invalid_choice"])
    else:
        print(f"\n{core.mark_gold(data, task['id'])}")


def task_of_day(data):
    task = core.task_of_day(data)
    if task is None:
        print(MESSAGES["no_tasks_for_tod"])
        return
    print(f"\n{core.task_of_day_text(task)}")


def show_stats(data):
    if not data["history"]:
        print("\n" + MESSAGES["no_stats"])
        return
    for days, header in ((7, "stats_header_7"), (30, "stats_header_30")):
        s = core.get_stats(data, days)
        print(f"\n{MESSAGES[header]}")
        print(MESSAGES["short_count"].format(count=s["short"]))
        print(MESSAGES["green_count"].format(count=s["green"]))
        print(MESSAGES["gold_long_count"].format(count=s["gold_long"]))

    print(MESSAGES["select_period"])
    print(MESSAGES["select_7"])
    print(MESSAGES["select_30"])
    print(MESSAGES["select_skip"])
    choice = input(MESSAGES["your_choice"]).strip()
    if choice in ("1", "2"):
        days = 7 if choice == "1" else 30
        print(f"\n{MESSAGES['table_header'].format(days=days)}")
        show_long_tasks_table(data, days)
    elif choice != "0":
        print("\n   ⚠️ Неверный выбор. Таблица не будет показана.")
    print("\n" + MESSAGES["praise"])


def main():
    data = core.load_data()
    print(MESSAGES["welcome"])
    print(MESSAGES["greeting"])
    while True:
        try:
            choice = input(MESSAGES["menu"]).strip()
            if choice == "1":
                add_task(data)
            elif choice == "2":
                mark_done(data)
            elif choice == "3":
                task_of_day(data)
            elif choice == "4":
                show_stats(data)
            elif choice == "5":
                show_active_tasks(core.active_tasks(data))
            elif choice == "6":
                print(f"\n{MESSAGES['goodbye']}")
                break
            else:
                print(MESSAGES["invalid_choice"])
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{MESSAGES['goodbye']}")
            break
        except Exception as e:
            print(f"{MESSAGES['error']} ({e})")


if __name__ == "__main__":
    main()
