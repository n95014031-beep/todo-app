# # ---- ВСТАВЬТЕ ВАШИ ДАННЫЕ СЮДА ----
# _DEFAULT_URL = "https://jlkrepuwoeccmroeiyiz.supabase.co"
# _DEFAULT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsa3JlcHV3b2VjY21yb2VpeWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5NzE4NTcsImV4cCI6MjExMDU0Nzg1N30.SrpGtJBVrBEmkLTIMmrR8XQeKrAVrXYhCXkdt6NXRok"

import flet as ft
from supabase import create_client, Client
import os

# ---- ВСТАВЬТЕ ВАШИ ДАННЫЕ СЮДА ----
_DEFAULT_URL = "https://jlkrepuwoeccmroeiyiz.supabase.co"
_DEFAULT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsa3JlcHV3b2VjY21yb2VpeWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5NzE4NTcsImV4cCI6MjExMDU0Nzg1N30.SrpGtJBVrBEmkLTIMmrR8XQeKrAVrXYhCXkdt6NXRok"

SUPABASE_URL = os.environ.get("SUPABASE_URL") or _DEFAULT_URL
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or _DEFAULT_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE = "tasks"


def main(page: ft.Page):
    page.title = "Список задач"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    tasks: list[dict] = []
    task_list = ft.Column(spacing=8, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    new_task = ft.TextField(hint_text="Что нужно сделать?", expand=True,
                            on_submit=lambda e: add_task(e))

    def error(msg: str):
        page.open(ft.SnackBar(ft.Text(msg)))
        page.update()

    def render():
        task_list.controls = [make_task_row(t) for t in tasks]
        page.update()

    def make_task_row(t: dict):
        def toggle(e):
            new_value = e.control.value
            t["done"] = new_value
            render()  # мгновенно обновляем экран

            def send():
                try:
                    supabase.table(TABLE).update({"done": new_value}).eq("id", t["id"]).execute()
                except Exception as ex:
                    t["done"] = not new_value  # откат при ошибке
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
                    tasks.insert(0, t)
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
        new_task.value = ""
        page.update()

        def send():
            try:
                res = supabase.table(TABLE).insert({"title": title, "done": False}).execute()
                if res.data:
                    tasks.insert(0, res.data[0])  # сервер вернул созданную строку
                    render()
            except Exception as ex:
                new_task.value = title  # вернуть текст, чтобы не потерять
                page.update()
                error(f"Ошибка добавления: {ex}")

        page.run_thread(send)

    def load():
        try:
            res = supabase.table(TABLE).select("*").order("created_at", desc=True).execute()
            tasks.clear()
            tasks.extend(res.data or [])
        except Exception as ex:
            error(f"Ошибка чтения: {ex}")
        render()

    page.add(
        ft.Text("Список задач", size=28, weight=ft.FontWeight.BOLD),
        ft.Row(controls=[new_task, ft.IconButton(icon=ft.Icons.ADD, on_click=add_task)]),
        ft.Divider(),
        task_list,
    )
    page.run_thread(load)


ft.app(target=main)
