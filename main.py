import os
from pathlib import Path, PurePath
import flet as ft
from pak_engine import TencentPakFile, build_reconstructed_pak

DOWNLOADS = Path("/storage/emulated/0/Download")
DEFAULT_TAG = "Telegram @Doxa_pubg_cfg. DOXACHKA"
TARGET_PHRASE = "Нажмите для просмотра особенностей FLASH."

def main(page: ft.Page):
    page.title = "Doxachkaa Master Utilities"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0F111A"
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    selected_pak = {"path": None}

    status_text = ft.Text("Выберите исходный .pak файл из папки Download", color="#A0A8C0", size=14)
    log_box = ft.Text("", color="#00FFAA", size=12, selectable=True)
    tag_input = ft.TextField(
        label="Ваш рекламный тег (до 42 символов)",
        value=DEFAULT_TAG,
        max_length=42,
        border_color="#6C63FF"
    )
    out_name_input = ft.TextField(
        label="Имя выходного файла",
        value="game_patch_4.7.0.21783.pak",
        border_color="#6C63FF"
    )

    def log(msg: str):
        log_box.value += f"\n• {msg}"
        page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            selected_pak["path"] = Path(e.files[0].path)
            status_text.value = f"Выбран: {selected_pak['path'].name}"
            status_text.color = "#00FFAA"
            log(f"Загружен файл: {selected_pak['path']}")
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def unpack_pak(e):
        if not selected_pak["path"]:
            log("Ошибка: сначала выберите .pak файл!")
            return
        try:
            log("Начинаю распаковку...")
            pak = TencentPakFile(selected_pak["path"])
            out_dir = DOWNLOADS / f"Doxachkaa_Unpack_{selected_pak['path'].stem}"
            ok, fail = pak.unpack_all(out_dir)
            log(f"Готово! Извлечено: {ok}, сырых: {fail}")
            log(f"Папка: {out_dir}")
        except Exception as ex:
            log(f"Ошибка распаковки: {ex}")

    def inject_tag_and_build(e):
        if not selected_pak["path"]:
            log("Ошибка: сначала выберите .pak файл!")
            return
        try:
            new_tag = tag_input.value.strip()
            if len(new_tag) > len(TARGET_PHRASE):
                log(f"Ошибка: тег длиннее {len(TARGET_PHRASE)} символов!")
                return

            log("Читаю структуру PAK...")
            pak = TencentPakFile(selected_pak["path"])
            modified_files = {}
            found_locres = False

            for dir_path, files in pak.index.items():
                for fn, entry in files.items():
                    if fn.lower() == "game_patch_3.locres" and "ru" in str(dir_path).lower():
                        rel = str(PurePath(dir_path) / fn).replace("\\", "/")
                        raw_data = pak.extract_entry(entry, rel)
                        old_b = TARGET_PHRASE.encode("utf-16le")
                        new_b = new_tag.ljust(len(TARGET_PHRASE)).encode("utf-16le")
                        if old_b in raw_data:
                            modified_files[rel] = raw_data.replace(old_b, new_b)
                            found_locres = True
                            log(f"Тег вшит в: {rel}")

            if not found_locres:
                log("Внимание: строка в ru/Game_patch_3.locres не найдена, собираю без замены текста.")

            out_pak = DOWNLOADS / out_name_input.value.strip()
            total, mod_cnt = build_reconstructed_pak(pak, modified_files, out_pak)
            log(f"УСПЕХ! Собрано файлов: {total} (изменено: {mod_cnt})")
            log(f"Сохранено в: {out_pak}")
        except Exception as ex:
            log(f"Ошибка сборки: {ex}")

    page.add(
        ft.Text("DOXACHKAA MASTER UTILITIES", size=22, weight=ft.FontWeight.BOLD, color="#6C63FF"),
        ft.Text("PUBG Mobile PAK Repacker & Tag Injector", size=12, color="#8892B0"),
        ft.Divider(color="#232946"),
        status_text,
        ft.ElevatedButton(
            "1. Выбрать .pak файл",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: file_picker.pick_files(allowed_extensions=["pak"]),
            width=400
        ),
        tag_input,
        out_name_input,
        ft.ElevatedButton(
            "2. Вшить тег и собрать .pak",
            icon=ft.Icons.BUILD,
            bgcolor="#6C63FF",
            color="white",
            on_click=inject_tag_and_build,
            width=400
        ),
        ft.OutlinedButton(
            "3. Просто распаковать .pak в Download",
            icon=ft.Icons.UNARCHIVE,
            on_click=unpack_pak,
            width=400
        ),
        ft.Divider(color="#232946"),
        ft.Text("Лог операций:", weight=ft.FontWeight.BOLD, color="#A0A8C0"),
        log_box
    )

ft.app(target=main)
