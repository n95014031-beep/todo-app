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

    task_list = ft.Column(spacing=8, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    new_task = ft.TextField(hint_text="Что нужно сделать?", expand=True, on_submit=lambda e: add_task(e))

    def refresh():
        try:
            res = supabase.table(TABLE).select("*").order("created_at", desc=True).execute()
            tasks = res.data or []
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Ошибка чтения: {ex}")))
            tasks = []

        task_list.controls.clear()
        for t in tasks:
            task_list.controls.append(make_task_row(t))
        page.update()

    def make_task_row(t: dict):
        done = t["done"]
        title = t["title"]

        def toggle(e):
            supabase.table(TABLE).update({"done": not done}).eq("id", t["id"]).execute()
            refresh()

        def delete(e):
            supabase.table(TABLE).delete().eq("id", t["id"]).execute()
            refresh()

        return ft.Row(
            controls=[
                ft.Checkbox(value=done, on_change=toggle),
                ft.Text(title, expand=True, style=ft.TextStyle(
                    decoration=ft.TextDecoration.LINE_THROUGH if done else None,
                    color=ft.Colors.GREY if done else None,
                )),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=delete),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def add_task(e):
        title = new_task.value.strip()
        if not title: return
        try:
            supabase.table(TABLE).insert({"title": title, "done": False}).execute()
            new_task.value = ""
            refresh()
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Ошибка добавления: {ex}")))
            page.update()

    page.add(
        ft.Text("Список задач", size=28, weight=ft.FontWeight.BOLD),
        ft.Row(controls=[new_task, ft.IconButton(icon=ft.Icons.ADD, on_click=add_task)]),
        ft.Divider(),
        task_list,
    )
    refresh()

ft.app(target=main)