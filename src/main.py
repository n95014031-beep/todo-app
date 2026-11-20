# # ---- ВСТАВЬТЕ ВАШИ ДАННЫЕ СЮДА ----
# _DEFAULT_URL = "https://jlkrepuwoeccmroeiyiz.supabase.co"
# _DEFAULT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsa3JlcHV3b2VjY21yb2VpeWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5NzE4NTcsImV4cCI6MjExMDU0Nzg1N30.SrpGtJBVrBEmkLTIMmrR8XQeKrAVrXYhCXkdt6NXRok"

import flet as ft
from supabase import create_client, Client
import os

# ---- ВСТАВЬТЕ ВАШИ ДАННЫЕ СЮДА ----
_DEFAULT_URL = "ВАШ_URL"
_DEFAULT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsa3JlcHV3b2VjY21yb2VpeWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5NzE4NTcsImV4cCI6MjExMDU0Nzg1N30.SrpGtJBVrBEmkLTIMmrR8XQeKrAVrXYhCXkdt6NXRok"

SUPABASE_URL = os.environ.get("SUPABASE_URL") or _DEFAULT_URL
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or _DEFAULT_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE = "tasks"
DEFAULT_GROUP = "Без группы"

SORT_MODES = {
    "new": "Сначала новые",
    "old": "Сначала старые",
    "alpha": "По алфавиту",
    "undone": "Сначала невыполненные",
}


def main(page: ft.Page):
    page.title = "Список задач"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    tasks: list[dict] = []
    extra_groups: set[str] = set()   # новые группы, в которых ещё нет задач
    expanded: dict[str, bool] = {}   # запоминаем, какие группы раскрыты

    task_list = ft.Column(spacing=4, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    new_task = ft.TextField(hint_text="Что нужно сделать?", expand=True,
                            on_submit=lambda e: add_task(e))

    group_dd = ft.Dropdown(
        width=150,
        value=DEFAULT_GROUP,
        options=[ft.dropdown.Option(DEFAULT_GROUP)],
    )

    sort_state = {"mode": "new"}  # по умолчанию: сначала новые

    def on_sort_change(e):
        sort_state["mode"] = sort_dd.value
        render()

    sort_dd = ft.Dropdown(
        label="Сортировка",
        value="new",
        options=[ft.dropdown.Option(key=k, text=v) for k, v in SORT_MODES.items()],
        on_change=on_sort_change,
    )

    def error(msg: str):
        page.open(ft.SnackBar(ft.Text(msg)))
        page.update()

    def all_groups() -> list[str]:
        names = {t.get("group_name") or DEFAULT_GROUP for t in tasks}
        names |= extra_groups
        names.add(DEFAULT_GROUP)
        return sorted(names, key=lambda n: (n != DEFAULT_GROUP, n.lower()))

    def sort_items(items: list[dict]) -> list[dict]:
        mode = sort_state["mode"]
        # базовый порядок: последние добавленные сверху
        result = sorted(items, key=lambda t: t.get("created_at") or "", reverse=True)
        if mode == "old":
            result.reverse()
        elif mode == "alpha":
            result = sorted(items, key=lambda t: t["title"].lower())
        elif mode == "undone":
            result = sorted(result, key=lambda t: t["done"])  # стабильная сортировка
        return result

    def render():
        groups: dict[str, list[dict]] = {name: [] for name in all_groups()}
        for t in tasks:
            groups[t.get("group_name") or DEFAULT_GROUP].append(t)

        controls = []
        for name, items in groups.items():
            if name == DEFAULT_GROUP and not items:
                continue  # пустую "Без группы" не показываем
            done_count = sum(1 for t in items if t["done"])
            rows = [make_task_row(t) for t in sort_items(items)] or [
                ft.Text("Пусто", color=ft.Colors.GREY)
            ]
            controls.append(
                ft.ExpansionTile(
                    title=ft.Text(f"{name}  ({done_count}/{len(items)})",
                                  weight=ft.FontWeight.BOLD),
                    initially_expanded=expanded.get(name, True),
                    on_change=lambda e, n=name: expanded.__setitem__(n, e.data == "true"),
                    controls=rows,
                )
            )
        task_list.controls = controls

        # обновляем список групп в выпадающем меню
        current = group_dd.value
        names = all_groups()
        group_dd.options = [ft.dropdown.Option(n) for n in names]
        group_dd.value = current if current in names else DEFAULT_GROUP
        page.update()

    def make_task_row(t: dict):
        def toggle(e):
            new_value = e.control.value
            t["done"] = new_value
            render()

            def send():
                try:
                    supabase.table(TABLE).update({"done": new_value}).eq("id", t["id"]).execute()
                except Exception as ex:
                    t["done"] = not new_value
                    render()
                    error(f"Ошибка обновления: {ex}")

            page.run_thread(send)

        def delete(e):
            if t in tasks:
                tasks.remove(t)
            render()

            def send():
                try:
                    supabase.table(TABLE).delete().eq("id", t["id"]).execute()
                except Exception as ex:
                    tasks.append(t)
                    render()
                    error(f"Ошибка удаления: {ex}")

            page.run_thread(send)

        done = t["done"]
        return ft.Row(
            controls=[
                ft.Checkbox(value=done, on_change=toggle),
                ft.Text(t["title"], expand=True, style=ft.TextStyle(
                    decoration=ft.TextDecoration.LINE_THROUGH if done else None,
                    color=ft.Colors.GREY if done else None,
                )),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE,
                              icon_color=ft.Colors.RED_400, on_click=delete),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def add_task(e):
        title = (new_task.value or "").strip()
        if not title:
            return
        group = group_dd.value or DEFAULT_GROUP
        new_task.value = ""
        page.update()

        def send():
            try:
                res = supabase.table(TABLE).insert(
                    {"title": title, "done": False, "group_name": group}
                ).execute()
                if res.data:
                    tasks.append(res.data[0])
                    render()
            except Exception as ex:
                new_task.value = title
                page.update()
                error(f"Ошибка добавления: {ex}")

        page.run_thread(send)

    # ---- диалог новой группы ----
    group_name_field = ft.TextField(label="Название группы", autofocus=True)

    def create_group(e):
        name = (group_name_field.value or "").strip()
        if not name:
            return
        extra_groups.add(name)
        group_dd.value = name
        group_name_field.value = ""
        page.close(group_dialog)
        render()

    group_dialog = ft.AlertDialog(
        title=ft.Text("Новая группа"),
        content=group_name_field,
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.close(group_dialog)),
            ft.TextButton("Создать", on_click=create_group),
        ],
    )

    def load():
        try:
            res = supabase.table(TABLE).select("*").execute()
            tasks.clear()
            tasks.extend(res.data or [])
        except Exception as ex:
            error(f"Ошибка чтения: {ex}")
        render()

    page.add(
        ft.Text("Список задач", size=28, weight=ft.FontWeight.BOLD),
        ft.Row(controls=[
            new_task,
            ft.IconButton(icon=ft.Icons.ADD, on_click=add_task, tooltip="Добавить задачу"),
        ]),
        ft.Row(controls=[
            group_dd,
            ft.IconButton(icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                          tooltip="Новая группа",
                          on_click=lambda e: page.open(group_dialog)),
        ]),
        sort_dd,
        ft.Divider(),
        task_list,
    )
    page.run_thread(load)


ft.app(target=main)
