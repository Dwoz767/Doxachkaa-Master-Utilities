import os
import base64
import zipfile
from pathlib import Path
import flet as ft
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

APP_PWD = "Doxachka2001"
OUT_DIR = Path("/storage/emulated/0/Download")


def gen_wg_keys():
    priv_obj = x25519.X25519PrivateKey.generate()
    priv_bytes = priv_obj.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = priv_obj.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(priv_bytes).decode(), base64.b64encode(pub_bytes).decode()


def main(page: ft.Page):
    page.title = "DOXAGUARD | @Doxa_pubg_cfg"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0D14"
    page.padding = 18
    page.scroll = ft.ScrollMode.AUTO

    # Плавающий логотип / водяной знак в углу экрана
    watermark = ft.Container(
        content=ft.Text("🛡️ @Doxa_pubg_cfg", size=11, weight=ft.FontWeight.BOLD, color="#62E6B2"),
        bgcolor="#161B29",
        border=ft.border.all(1, "#2A334D"),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        right=12,
        top=12,
    )
    page.overlay.append(watermark)

    log_text = ft.Text("Готов к работе", size=12, color="#9BA3BC", selectable=True)

    def show_msg(msg: str, color: str = "#62E6B2"):
        log_text.value = msg
        log_text.color = color
        page.update()

    # Поля конструктора
    priv_field = ft.TextField(label="PrivateKey клиента", border_color="#2A334D", text_size=12)
    pub_client_field = ft.TextField(label="Ваш PublicKey (для сервера)", read_only=True, border_color="#2A334D", text_size=12)
    srv_pub_field = ft.TextField(
        label="PublicKey сервера",
        value="bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
        border_color="#2A334D",
        text_size=12,
    )
    ep_field = ft.TextField(
        label="Endpoint сервера (IP:PORT)",
        value="162.159.192.1:2408",
        border_color="#2A334D",
        text_size=12,
    )
    addr_field = ft.TextField(label="Address клиента", value="10.66.66.2/32", border_color="#2A334D", text_size=12)
    mtu_field = ft.TextField(label="MTU (оптимизация 4G/игр)", value="1280", border_color="#2A334D", text_size=12)
    name_field = ft.TextField(label="Имя файла", value="DoxaGuard", border_color="#2A334D", text_size=12)
    preview_field = ft.TextField(
        label="Готовый код VPN.conf",
        multiline=True,
        min_lines=7,
        max_lines=10,
        border_color="#2A334D",
        text_size=11,
    )

    def on_generate_keys(_):
        try:
            priv, pub = gen_wg_keys()
            priv_field.value = priv
            pub_client_field.value = pub
            show_msg("🔑 Новая пара ключей WireGuard сгенерирована!", "#62E6B2")
        except Exception as ex:
            show_msg(f"Ошибка генерации ключей: {ex}", "#FF7373")

    def build_config_text():
        if not priv_field.value.strip():
            on_generate_keys(None)
        return (
            f"# Built with DoxaGuard | @Doxa_pubg_cfg\n"
            f"[Interface]\n"
            f"PrivateKey = {priv_field.value.strip()}\n"
            f"Address = {addr_field.value.strip() or '10.66.66.2/32'}\n"
            f"DNS = 1.1.1.1, 1.0.0.1\n"
            f"MTU = {mtu_field.value.strip() or '1280'}\n\n"
            f"[Peer]\n"
            f"PublicKey = {srv_pub_field.value.strip()}\n"
            f"Endpoint = {ep_field.value.strip()}\n"
            f"AllowedIPs = 0.0.0.0/0\n"
            f"PersistentKeepalive = 10\n"
        )

    def on_build_and_save(_):
        try:
            conf_text = build_config_text()
            preview_field.value = conf_text
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            fname = (name_field.value.strip() or "DoxaGuard").replace(".conf", "")
            conf_path = OUT_DIR / f"{fname}.conf"
            zip_path = OUT_DIR / f"{fname}_protected.zip"

            conf_path.write_text(conf_text, encoding="utf-8")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"{fname}.conf", conf_text)

            show_msg(
                f"✅ Готово! Сохранено в Download:\n• {fname}.conf\n• {fname}_protected.zip",
                "#62E6B2",
            )
        except Exception as ex:
            show_msg(f"Ошибка сохранения: {ex}", "#FF7373")

    def open_main_ui():
        page.clean()
        page.add(
            ft.Column(
                [
                    ft.Text("🛡️ DOXAGUARD", size=22, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    ft.Text("Конструктор WireGuard / AmneziaWG • @Doxa_pubg_cfg", size=12, color="#8E96B0"),
                    ft.Divider(color="#1E2436"),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "🔑 Сгенерировать ключи",
                                on_click=on_generate_keys,
                                bgcolor="#1E263D",
                                color="#FFFFFF",
                                expand=True,
                            ),
                            ft.ElevatedButton(
                                "⚡ Собрать VPN.conf",
                                on_click=on_build_and_save,
                                bgcolor="#6C5CE7",
                                color="#FFFFFF",
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    priv_field,
                    pub_client_field,
                    srv_pub_field,
                    ep_field,
                    ft.Row([addr_field, mtu_field], spacing=10),
                    name_field,
                    preview_field,
                    ft.Container(
                        content=log_text,
                        bgcolor="#131724",
                        padding=12,
                        border_radius=10,
                        border=ft.border.all(1, "#232A40"),
                    ),
                ],
                spacing=10,
            )
        )
        on_generate_keys(None)

    # Экран входа по паролю
    pwd_input = ft.TextField(
        label="Введите пароль доступа",
        password=True,
        can_reveal_password=True,
        border_color="#2A334D",
    )
    login_err = ft.Text("", color="#FF7373", size=12)

    def check_login(_):
        if pwd_input.value.strip() == APP_PWD:
            open_main_ui()
        else:
            login_err.value = "❌ Неверный пароль!"
            page.update()

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("🛡️ DOXAGUARD v1.0", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("@Doxa_pubg_cfg", size=13, color="#62E6B2"),
                    pwd_input,
                    ft.ElevatedButton(
                        "Войти в конструктор",
                        on_click=check_login,
                        bgcolor="#6C5CE7",
                        color="#FFFFFF",
                        width=260,
                    ),
                    login_err,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
            padding=24,
            margin=ft.margin.only(top=60),
            bgcolor="#131724",
            border_radius=16,
            border=ft.border.all(1, "#232A40"),
        )
    )


ft.app(target=main)
