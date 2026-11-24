import logging
from pathlib import Path
import flet as ft
from pak_engine import TencentPakFile, build_reconstructed_pak

APP_NAME = "DOXACHKAA MASTER UTILITIES"


def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0D14"
    page.padding = 18
    page.scroll = ft.ScrollMode.AUTO
    page.window_min_width = 340
    page.window_min_height = 620

    state = {"pak": None, "output": None, "busy": False}

    def add_log(message, color="#C7CBE0"):
        log_list.controls.append(
            ft.Row(
                [ft.Container(width=6, height=6, bgcolor=color, border_radius=6),
                 ft.Text(message, size=12, color="#D7DAE8", selectable=True, expand=True)],
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
            )
        )
        if len(log_list.controls) > 80:
            log_list.controls.pop(0)
        page.update()

    def set_busy(value, message=None):
        state["busy"] = value
        for control in action_controls:
            control.disabled = value
        if message:
            status.value = message
        page.update()

    def on_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            add_log("Выбор файла отменён", "#F6C76A")
            return
        chosen = e.files[0]
        if not chosen.path:
            add_log("Android не вернул путь к файлу. Попробуйте выбрать файл через системный проводник ещё раз.", "#F6C76A")
            return
        path = Path(chosen.path)
        if path.suffix.lower() != ".pak":
            add_log("Нужен файл с расширением .pak", "#FF7373")
            return
        state["pak"] = path
        selected_name.value = path.name
        status.value = "Файл выбран и готов к операции"
        status.color = "#62E6B2"
        add_log(f"Выбран файл: {path.name}", "#62E6B2")
        page.update()

    def on_dir_result(e: ft.FilePickerResultEvent):
        if not e.path:
            add_log("Папка назначения не выбрана", "#F6C76A")
            return
        state["output"] = Path(e.path)
        output_name.value = str(state["output"])
        add_log(f"Папка сохранения: {e.path}", "#62E6B2")
        page.update()

    picker = ft.FilePicker(on_result=on_file_result)
    folder_picker = ft.FilePicker(on_result=on_dir_result)
    page.overlay.extend([picker, folder_picker])

    def require_ready():
        if not state["pak"]:
            add_log("Сначала выберите исходный .pak файл", "#FF7373")
            return False
        if not state["pak"].is_file():
            add_log("Исходный файл больше недоступен. Выберите его заново.", "#FF7373")
            return False
        if not state["output"]:
            add_log("Сначала выберите папку сохранения", "#F6C76A")
            return False
        return True

    async def choose_file(_):
        try:
            picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["pak"],
                dialog_title="Выберите PAK-файл"
            )
        except Exception as ex:
            add_log(f"Ошибка выбора файла: {ex}", "#FF7373")

    async def choose_folder(_):
        try:
            folder_picker.get_directory_path(
                dialog_title="Куда сохранить результат"
            )
        except Exception as ex:
            add_log(f"Ошибка выбора папки: {ex}", "#FF7373")

    def unpack(_):
        if state["busy"] or not require_ready():
            return
        set_busy(True, "Выполняется распаковка…")
        try:
            pak = TencentPakFile(state["pak"])
            destination = state["output"] / f"Doxachkaa_Unpack_{state['pak'].stem}"
            destination.mkdir(parents=True, exist_ok=True)
            extracted, raw = pak.unpack_all(destination)
            status.value = "Распаковка завершена"
            status.color = "#62E6B2"
            add_log(f"Распаковка завершена. Извлечено: {extracted}; сырых: {raw}", "#62E6B2")
            add_log(f"Папка результата: {destination}")
        except Exception as ex:
            logging.exception("Unpack failed")
            status.value = "Ошибка распаковки"
            status.color = "#FF7373"
            add_log(f"Ошибка: {type(ex).__name__}: {ex}", "#FF7373")
        finally:
            set_busy(False)

    def rebuild_unchanged(_):
        if state["busy"] or not require_ready():
            return
        set_busy(True, "Подготовка копии PAK…")
        try:
            source = state["pak"]
            target = state["output"] / f"{source.stem}_repacked{source.suffix}"
            pak = TencentPakFile(source)
            total, changed = build_reconstructed_pak(pak, {}, target)
            status.value = "Сборка завершена"
            status.color = "#62E6B2"
            add_log(f"Сборка завершена. Файлов: {total}; изменённых: {changed}", "#62E6B2")
            add_log(f"Результат: {target}")
        except Exception as ex:
            logging.exception("Build failed")
            status.value = "Ошибка сборки"
            status.color = "#FF7373"
            add_log(f"Ошибка: {type(ex).__name__}: {ex}", "#FF7373")
        finally:
            set_busy(False)

    def card_button(text, icon, handler, filled=False):
        return ft.Container(
            content=ft.ElevatedButton(
                text=text,
                icon=icon,
                on_click=handler,
                height=54,
                style=ft.ButtonStyle(
                    bgcolor="#795BFA" if filled else "#202438",
                    color="#FFFFFF",
                    shape=ft.RoundedRectangleBorder(radius=15),
                    elevation=0,
                ),
                expand=True,
            ),
            expand=True,
        )

    status = ft.Text("Выберите PAK-файл и папку назначения", size=12, color="#A6ABC2")
    selected_name = ft.Text("Файл ещё не выбран", size=13, color="#DDE0F0", weight=ft.FontWeight.W_600)
    output_name = ft.Text("Папка не выбрана", size=12, color="#A6ABC2", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
    log_list = ft.ListView(spacing=10, auto_scroll=True, height=175)

    action_controls = []
    pick_btn = ft.ElevatedButton("Выбрать .PAK файл", icon=ft.Icons.FOLDER_OPEN, on_click=choose_file, height=52,
        style=ft.ButtonStyle(bgcolor="#795BFA", color="white", shape=ft.RoundedRectangleBorder(radius=14)))
    folder_btn = ft.OutlinedButton("Выбрать папку сохранения", icon=ft.Icons.FOLDER, on_click=choose_folder, height=48,
        style=ft.ButtonStyle(color="#D5CCFF", side=ft.BorderSide(1, "#51447E"), shape=ft.RoundedRectangleBorder(radius=14)))
    build_btn = ft.ElevatedButton("Пересобрать без изменений", icon=ft.Icons.BUILD_CIRCLE, on_click=rebuild_unchanged, height=54,
        style=ft.ButtonStyle(bgcolor="#292341", color="#D9D0FF", shape=ft.RoundedRectangleBorder(radius=14)))
    unpack_btn = ft.ElevatedButton("Распаковать архив", icon=ft.Icons.UNARCHIVE, on_click=unpack, height=54,
        style=ft.ButtonStyle(bgcolor="#202438", color="#E4E7F5", shape=ft.RoundedRectangleBorder(radius=14)))
    action_controls = [pick_btn, folder_btn, build_btn, unpack_btn]

    def panel(content, padding=16):
        return ft.Container(content=content, padding=padding, bgcolor="#141827",
            border=ft.border.all(1, "#252C42"), border_radius=20)

    page.add(
        ft.Row([
            ft.Container(content=ft.Icon(ft.Icons.TERMINAL_ROUNDED, color="#FFFFFF", size=27),
                         bgcolor="#795BFA", padding=12, border_radius=15),
            ft.Column([
                ft.Text("DOXACHKAA", size=20, weight=ft.FontWeight.BOLD, color="#F3F1FF"),
                ft.Text("MASTER UTILITIES  •  ANDROID", size=10, color="#9BA2BD", weight=ft.FontWeight.BOLD),
            ], spacing=2, expand=True),
            ft.Container(content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color="#D8CEFF"),
                         bgcolor="#302750", padding=ft.padding.symmetric(horizontal=11, vertical=7), border_radius=20),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=4),
        ft.Text("Работа с PAK-файлами", size=23, weight=ft.FontWeight.BOLD, color="#F2F3FA"),
        ft.Text("Выберите исходный файл и место для результата", size=12, color="#929AB5"),
        panel(ft.Column([
            ft.Row([ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, color="#B8A7FF"),
                    ft.Text("ИСХОДНЫЙ ФАЙЛ", size=10, color="#929AB5", weight=ft.FontWeight.BOLD)], spacing=9),
            selected_name,
            pick_btn,
        ], spacing=12)),
        panel(ft.Column([
            ft.Row([ft.Icon(ft.Icons.SAVE_ALT_ROUNDED, color="#B8A7FF"),
                    ft.Text("МЕСТО СОХРАНЕНИЯ", size=10, color="#929AB5", weight=ft.FontWeight.BOLD)], spacing=9),
            output_name,
            folder_btn,
        ], spacing=12)),
        ft.Text("ОПЕРАЦИИ", size=10, color="#929AB5", weight=ft.FontWeight.BOLD),
        build_btn,
        unpack_btn,
        panel(ft.Column([
            ft.Row([ft.Icon(ft.Icons.MONITOR_HEART_OUTLINED, color="#62E6B2"),
                    ft.Text("СОСТОЯНИЕ", size=10, color="#929AB5", weight=ft.FontWeight.BOLD)], spacing=9),
            status,
        ], spacing=8)),
        panel(ft.Column([
            ft.Row([ft.Icon(ft.Icons.TERMINAL, color="#B8A7FF"),
                    ft.Text("ЖУРНАЛ ОПЕРАЦИЙ", size=10, color="#929AB5", weight=ft.FontWeight.BOLD)], spacing=9),
            log_list,
        ], spacing=10)),
        ft.Text("Doxachkaa Utilities  •  Android build", size=10, color="#626B87", text_align=ft.TextAlign.CENTER),
    )


ft.app(target=main)
