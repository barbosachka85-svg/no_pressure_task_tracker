"""
Добрый трекер — приложение для телефона.

Здесь только кнопки и экраны. Вся логика, сообщения и работа с
tracker_data.json — в tracker_core.py (тот же мозг, что у консольной версии).
"""

import flet as ft

import tracker_core as core
from tracker_core import MESSAGES

GREEN = "#2F8A52"
GOLD = "#B88310"
PINK = "#B8527A"


def main(page: ft.Page):
    page.title = "Добрый трекер"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.theme = ft.Theme(color_scheme_seed=GREEN)
    page.dark_theme = ft.Theme(color_scheme_seed=GREEN)
    page.padding = 0

    data = core.load_data()
    state = {"tab": 0, "new_type": "long", "period": 7, "tod": None}
    file_picker = ft.FilePicker()

    # ---------- похвала ----------
    def praise(text: str):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(text, size=16),
                behavior=ft.SnackBarBehavior.FLOATING,
                duration=ft.Duration(milliseconds=4500),
                show_close_icon=True,
            )
        )

    # ---------- общие кусочки ----------
    def heading(text: str):
        return ft.Text(text, size=18, weight=ft.FontWeight.BOLD)

    def soft(text: str, size: int = 14):
        return ft.Text(text, size=size, color=ft.Colors.ON_SURFACE_VARIANT)

    def empty_box(text: str):
        return ft.Container(
            content=ft.Text(text, text_align=ft.TextAlign.CENTER, color=ft.Colors.ON_SURFACE_VARIANT),
            padding=20,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
        )

    def card(controls, padding: int = 16):
        return ft.Card(
            content=ft.Container(content=ft.Column(controls=controls, spacing=10), padding=padding),
        )

    def type_badge(task_type: str):
        long = task_type == "long"
        return ft.Container(
            content=ft.Text(
                ("📖 " if long else "⚡ ") + core.type_name(task_type),
                size=12,
                weight=ft.FontWeight.BOLD,
                color=GREEN if long else GOLD,
            ),
            padding=ft.Padding.symmetric(vertical=3, horizontal=10),
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(0.12, GREEN if long else GOLD),
        )

    def heart_buttons(task):
        tid = task["id"]
        if task["type"] == "long":
            return [
                ft.FilledTonalButton(content="💚 Поработала", on_click=lambda e, t=tid: on_green(t)),
                ft.FilledTonalButton(content="💛 Закончила", on_click=lambda e, t=tid: on_gold(t)),
            ]
        return [ft.FilledTonalButton(content="💛 Сделала", on_click=lambda e, t=tid: on_gold(t))]

    # ---------- действия (вызывают мозг) ----------
    def on_green(task_id: int):
        praise(core.mark_green(data, task_id))
        render()

    def on_gold(task_id: int):
        if state["tod"] and state["tod"]["id"] == task_id:
            state["tod"] = None
        praise(core.mark_gold(data, task_id))
        render()

    title_field = ft.TextField(
        label="Новая задача",
        hint_text="Напиши название задачи",
        max_length=200,
        on_submit=lambda e: on_add(),
    )

    def on_add():
        ok, message = core.add_task(data, title_field.value or "", state["new_type"])
        praise(message)
        if ok:
            title_field.value = ""
            render()

    def on_type_change(e):
        state["new_type"] = e.control.selected[0]
        render()

    def on_pick_tod():
        task = core.task_of_day(data)
        state["tod"] = task
        render()

    def on_period_change(e):
        state["period"] = int(e.control.selected[0])
        render()

    async def on_export(e):
        try:
            await file_picker.save_file(
                dialog_title="Сохранить копию трекера",
                file_name="tracker_data.json",
                src_bytes=core.data_to_json(data).encode("utf-8"),
            )
        except Exception:
            praise(MESSAGES["error"])

    async def on_import(e):
        files = await file_picker.pick_files(
            dialog_title="Выбери tracker_data.json",
            allow_multiple=False,
            with_data=True,
        )
        if not files:
            return
        f = files[0]
        raw = f.bytes
        if raw is None and f.path:
            with open(f.path, "rb") as fh:
                raw = fh.read()
        new = core.data_from_json(raw.decode("utf-8-sig")) if raw else None
        if new is None:
            praise(MESSAGES["bad_file"])
            return
        ask_replace(new)

    def ask_replace(new):
        n_tasks = len(core.active_tasks(new))
        n_hist = len(new["history"])

        def yes(e):
            data.clear()
            data.update(new)
            core.save_data(data)
            state["tod"] = None
            page.pop_dialog()
            praise(MESSAGES["imported"])
            render()

        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Заменить данные?"),
                content=ft.Text(
                    f"В файле {n_tasks} активных задач и {n_hist} записей с сердечками. "
                    "Текущие задачи в приложении заменятся на эти."
                ),
                actions=[
                    ft.TextButton(content="Отмена", on_click=lambda e: page.pop_dialog()),
                    ft.FilledButton(content="Заменить", on_click=yes),
                ],
            )
        )

    # ---------- экраны ----------
    def tasks_view():
        add_card = card([
            heading("📝 Добавить задачу"),
            title_field,
            ft.SegmentedButton(
                segments=[
                    ft.Segment(value="long", label="📖 Длинная"),
                    ft.Segment(value="short", label="⚡ Короткая"),
                ],
                selected=[state["new_type"]],
                show_selected_icon=False,
                on_change=on_type_change,
            ),
            soft(core.type_hint(state["new_type"])),
            ft.Button(content="Добавить", icon=ft.Icons.ADD, on_click=lambda e: on_add()),
        ])

        tasks = core.active_tasks(data)
        items = [heading("📋 Твои активные задачи")]
        if not tasks:
            items.append(empty_box(MESSAGES["no_tasks"]))
        for t in tasks:
            rows = [
                ft.Row(
                    controls=[
                        ft.Text(t["title"], size=16, weight=ft.FontWeight.W_600, expand=True),
                        type_badge(t["type"]),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ]
            if t["type"] == "long":
                g = core.green_hearts_for(data, t["id"])
                rows.append(soft(f"💚 × {g}" if g else "Пока без сердечек, и это нормально", 13))
            rows.append(ft.Row(controls=heart_buttons(t), wrap=True, spacing=8, run_spacing=8))
            items.append(card(rows, padding=14))
        return [add_card, *items]

    def day_view():
        controls = [
            heading("🎲 Задача дня"),
            soft("Не знаешь, с чего начать? Я выберу случайную задачу из списка."),
            ft.Button(
                content="Выбрать задачу дня" if state["tod"] is None else "Выбрать другую",
                icon=ft.Icons.CASINO_OUTLINED,
                on_click=lambda e: on_pick_tod(),
            ),
        ]
        if not core.active_tasks(data):
            controls.append(empty_box(MESSAGES["no_tasks_for_tod"]))
        elif state["tod"] is not None:
            t = state["tod"]
            controls.append(card([
                ft.Text(f"«{t['title']}»", size=22, weight=ft.FontWeight.BOLD),
                ft.Text(f"Это {core.type_name(t['type'])} задача. {core.task_of_day_encouragement(t)}"),
                ft.Text(MESSAGES["tod_soft"], color=PINK, italic=True),
                ft.Row(controls=heart_buttons(t), wrap=True, spacing=8, run_spacing=8),
            ], padding=20))
        return controls

    def stat_tile(number: int, caption: str, color: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(str(number), size=30, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(caption, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=2,
            ),
            padding=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
            expand=True,
        )

    def hearts_table(days: int):
        dates, rows = core.long_tasks_table(data, days)
        if not rows:
            return empty_box(MESSAGES["no_long_tasks"])
        symbol = {"green": "💚", "gold": "💛"}
        table = ft.DataTable(
            columns=[ft.DataColumn(label=ft.Text("Задача"))]
            + [ft.DataColumn(label=ft.Text(d)) for d in dates],
            rows=[
                ft.DataRow(
                    cells=[ft.DataCell(content=ft.Text(name[:24] + ("…" if len(name) > 24 else "")))]
                    + [ft.DataCell(content=ft.Text(symbol.get(cells.get(d), ""))) for d in dates]
                )
                for name, cells in rows.items()
            ],
            column_spacing=14,
            horizontal_margin=10,
        )
        return ft.Row(controls=[table], scroll=ft.ScrollMode.AUTO)

    def stats_view():
        controls = [
            heading("📊 Статистика"),
            ft.SegmentedButton(
                segments=[
                    ft.Segment(value="7", label="7 дней"),
                    ft.Segment(value="30", label="30 дней"),
                ],
                selected=[str(state["period"])],
                show_selected_icon=False,
                on_change=on_period_change,
            ),
        ]
        if not data["history"]:
            controls.append(empty_box(MESSAGES["no_stats"]))
        else:
            s = core.get_stats(data, state["period"])
            controls.append(ft.Row(controls=[
                stat_tile(s["short"], "✨ коротких задач завершено", GOLD),
                stat_tile(s["green"], "💚 зелёных сердечек", GREEN),
                stat_tile(s["gold_long"], "💛 длинных задач завершено", GOLD),
            ], spacing=8))
            for count, key, emoji in (
                (s["short"], "short_caption", "✨"),
                (s["green"], "green_caption", "💚"),
                (s["gold_long"], "gold_caption", "💛"),
            ):
                if count:
                    controls.append(soft(f"{emoji} {MESSAGES[key]}"))
            controls.append(heading("Длинные задачи по дням"))
            controls.append(hearts_table(state["period"]))
            controls.append(soft(MESSAGES["table_legend"], 13))
            controls.append(ft.Text(MESSAGES["praise"], color=PINK, italic=True))

        controls += [
            ft.Divider(),
            heading("Мои данные"),
            soft("Задачи хранятся только в этом телефоне, в файле tracker_data.json. "
                 "Иногда сохраняй копию. Её же можно перенести в консольную версию и обратно."),
            ft.Row(
                controls=[
                    ft.OutlinedButton(content="Сохранить копию", icon=ft.Icons.SAVE_ALT, on_click=on_export),
                    ft.OutlinedButton(content="Загрузить из файла", icon=ft.Icons.UPLOAD_FILE, on_click=on_import),
                ],
                wrap=True,
                spacing=8,
                run_spacing=8,
            ),
        ]
        return controls

    # ---------- сборка ----------
    body = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def render():
        views = (tasks_view, day_view, stats_view)
        body.controls = [
            ft.Text("Добрый трекер", size=26, weight=ft.FontWeight.W_800),
            soft(MESSAGES["greeting"], 15),
            *views[state["tab"]](),
            ft.Container(height=12),
        ]
        page.update()

    def on_tab(e):
        state["tab"] = e.control.selected_index
        render()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_tab,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST, label="Задачи"),
            ft.NavigationBarDestination(icon=ft.Icons.CASINO_OUTLINED, label="Задача дня"),
            ft.NavigationBarDestination(icon=ft.Icons.FAVORITE_BORDER, selected_icon=ft.Icons.FAVORITE, label="Статистика"),
        ],
    )
    page.add(
        ft.SafeArea(
            content=ft.Container(content=body, padding=ft.Padding.symmetric(vertical=8, horizontal=16)),
            expand=True,
        )
    )
    render()


if __name__ == "__main__":
    ft.run(main)
