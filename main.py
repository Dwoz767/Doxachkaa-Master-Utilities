import os, base64, zipfile
from pathlib import Path
import flet as ft
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

APP_PWD = "Doxachka2001"
OUT_DIR = Path("/storage/emulated/0/Download")

def gen_wg_keys():
    priv_obj = x25519.X25519PrivateKey.generate()
    priv_b = priv_obj.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    pub_b = priv_obj.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(priv_b).decode(), base64.b64encode(pub_b).decode()

def pub_from_priv(priv_b64: str) -> str:
    try:
        raw = base64.b64decode(priv_b64.strip())
        if len(raw) == 32:
            priv_obj = x25519.X25519PrivateKey.from_private_bytes(raw)
            pub_b = priv_obj.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            return base64.b64encode(pub_b).decode()
    except Exception:
        pass
    return ""

def parse_wg_config(text: str) -> dict:
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";") or line.startswith("["):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip().lower()] = v.strip()
    return data

def neon_title(txt, size=34):
    return ft.Text(txt, size=size, weight=ft.FontWeight.W_900, color="#E066FF", style=ft.TextStyle(shadow=[ft.BoxShadow(blur_radius=14, color="#B800FF"), ft.BoxShadow(blur_radius=28, color="#8A00E6")]))

def neon_btn(label, on_click, border="#FF1E56", glow="#FF0044", bg="#CC24072E", expand=False, width=None):
    return ft.Container(
        content=ft.ElevatedButton(label, on_click=on_click, bgcolor="transparent", color="#FFFFFF", style=ft.ButtonStyle(shadow_color="transparent", elevation=0, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=13))),
        bgcolor=bg, border=ft.border.all(2, border), border_radius=12, shadow=[ft.BoxShadow(blur_radius=14, spread_radius=1, color=glow)], expand=expand, width=width, alignment=ft.alignment.center
    )

def main(page: ft.Page):
    page.title = "DOXAGUARD | DOXACHKAA"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#060E22"
    page.padding = 0

    page.overlay.append(ft.Container(content=ft.Text("🐉 @Doxa_pubg_cfg", size=11, weight=ft.FontWeight.BOLD, color="#FFFFFF"), bgcolor="#CC120624", border=ft.border.all(1.5, "#FF1E56"), border_radius=20, padding=ft.padding.symmetric(horizontal=10, vertical=4), shadow=[ft.BoxShadow(blur_radius=10, color="#FF0044")], right=12, top=12))

    state = {"active_tunnel": None}
    status_badge = ft.Text("🔴 СТАТУС: ОТКЛЮЧЕНО", size=12, weight=ft.FontWeight.BOLD, color="#FF4D6D")
    log_text = ft.Text("Готов к работе", size=12, color="#F2D9FF", selectable=True)
    tunnels_col = ft.Column(spacing=8)

    def show_msg(msg, color="#E066FF"):
        log_text.value, log_text.color = msg, color
        page.update()

    fbg, rneon = "#CC0A1128", "#FF1E56"
    priv_f = ft.TextField(label="PrivateKey клиента", bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF", text_size=12)
    pub_f = ft.TextField(label="Ваш PublicKey (для сервера)", read_only=True, bgcolor=fbg, border_color=rneon, text_size=12)
    srv_f = ft.TextField(label="PublicKey сервера", value="bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=", bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF", text_size=12)
    ep_f = ft.TextField(label="Endpoint (IP:PORT)", value="162.159.192.1:2408", bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF", text_size=12)
    addr_f = ft.TextField(label="Address", value="10.66.66.2/32", bgcolor=fbg, border_color=rneon, text_size=12, expand=True)
    mtu_f = ft.TextField(label="MTU", value="1280", bgcolor=fbg, border_color=rneon, text_size=12, width=100)
    name_f = ft.TextField(label="Имя файла", value="DoxaGuard", bgcolor=fbg, border_color=rneon, text_size=12)
    prev_f = ft.TextField(label="Готовый код VPN.conf", multiline=True, min_lines=5, max_lines=8, bgcolor=fbg, border_color=rneon, text_size=11)

    def apply_config_text(raw_text: str, profile_name: str = ""):
        cfg = parse_wg_config(raw_text)
        if not cfg:
            show_msg("❌ Не удалось распознать конфиг VPN!", "#FF4D6D")
            return False
        if "privatekey" in cfg:
            priv_f.value = cfg["privatekey"]
            derived_pub = pub_from_priv(cfg["privatekey"])
            if derived_pub:
                pub_f.value = derived_pub
        if "publickey" in cfg:
            srv_f.value = cfg["publickey"]
        if "endpoint" in cfg:
            ep_f.value = cfg["endpoint"]
        if "address" in cfg:
            addr_f.value = cfg["address"]
        if "mtu" in cfg:
            mtu_f.value = cfg["mtu"]
        if profile_name:
            name_f.value = profile_name.replace(".conf", "").replace(".zip", "")
        prev_f.value = raw_text.strip()
        return True

    def save_raw_conf(name: str, raw_text: str) -> Path:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        clean_name = (name.strip() or "DoxaGuard").replace(".conf", "")
        conf_p = OUT_DIR / f"{clean_name}.conf"
        conf_p.write_text(raw_text.strip() + "\n", encoding="utf-8")
        return conf_p

    def toggle_tunnel_item(conf_path: Path, is_on: bool):
        if is_on:
            state["active_tunnel"] = conf_path.name
            status_badge.value = f"🟢 АКТИВЕН: {conf_path.stem}"
            status_badge.color = "#00FFAA"
            try:
                content = conf_path.read_text(encoding="utf-8", errors="ignore")
                apply_config_text(content, conf_path.stem)
                show_msg(f"🚀 Включён туннель {conf_path.name}! Выберите клиент туннеля для запуска.", "#00FFAA")
                page.launch_url(f"file://{conf_path}")
            except Exception as ex:
                show_msg(f"Профиль {conf_path.name} выбран ({ex})", "#00FFAA")
        else:
            if state["active_tunnel"] == conf_path.name:
                state["active_tunnel"] = None
                status_badge.value = "🔴 СТАТУС: ОТКЛЮЧЕНО"
                status_badge.color = "#FF4D6D"
                show_msg(f"⏹ Туннель {conf_path.stem} отключён.", "#FF4D6D")
        refresh_tunnels_list()

    def load_tunnel_to_editor(conf_path: Path):
        try:
            content = conf_path.read_text(encoding="utf-8", errors="ignore")
            if apply_config_text(content, conf_path.stem):
                show_msg(f"📝 Профиль {conf_path.stem} загружен в редактор.", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка чтения: {ex}", "#FF4D6D")

    def delete_tunnel_item(conf_path: Path):
        try:
            if state["active_tunnel"] == conf_path.name:
                state["active_tunnel"] = None
                status_badge.value = "🔴 СТАТУС: ОТКЛЮЧЕНО"
                status_badge.color = "#FF4D6D"
            conf_path.unlink(missing_ok=True)
            show_msg(f"🗑 Профиль {conf_path.stem} удалён.", "#FF4D6D")
            refresh_tunnels_list()
        except Exception as ex:
            show_msg(f"Ошибка удаления: {ex}", "#FF4D6D")

    def refresh_tunnels_list():
        tunnels_col.controls.clear()
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(OUT_DIR.glob("*.conf"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            tunnels_col.controls.append(
                ft.Text("Нет сохранённых VPN. Нажмите + чтобы импортировать или создать.", size=12, color="#99CCFF")
            )
        else:
            for f in files:
                is_active = (state["active_tunnel"] == f.name)
                border_col = "#00FFAA" if is_active else "#B800FF"
                card = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f.stem, size=14, weight=ft.FontWeight.BOLD, color="#00FFAA" if is_active else "#FFFFFF"),
                                ft.Text("Нажмите, чтобы открыть в редакторе", size=10, color="#99CCFF"),
                            ], spacing=1),
                            on_click=lambda _, p=f: load_tunnel_to_editor(p),
                            expand=True,
                        ),
                        ft.Switch(
                            value=is_active,
                            active_color="#00FFAA",
                            active_track_color="#0A3D2E",
                            inactive_thumb_color="#FF1E56",
                            inactive_track_color="#2B0618",
                            on_change=lambda e, p=f: toggle_tunnel_item(p, e.control.value),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color="#FF4D6D",
                            icon_size=20,
                            tooltip="Удалить",
                            on_click=lambda _, p=f: delete_tunnel_item(p),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border_radius=12,
                    bgcolor="#CC140829",
                    border=ft.border.all(1.5, border_col),
                )
                tunnels_col.controls.append(card)
        page.update()

    def on_gen(_):
        try:
            priv_f.value, pub_f.value = gen_wg_keys()
            show_msg("🔑 Новая пара ключей сгенерирована!", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка: {ex}", "#FF4D6D")

    def on_create_scratch(_):
        close_import_sheet()
        priv_f.value, pub_f.value = gen_wg_keys()
        srv_f.value = ""
        ep_f.value = ""
        addr_f.value = "10.66.66.2/32"
        mtu_f.value = "1280"
        name_f.value = "DoxaGuard_New"
        prev_f.value = ""
        show_msg("✨ Создан новый пустой профиль. Заполните поля и нажмите «Собрать VPN».", "#00FFAA")

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f_path = e.files[0].path
        if not f_path:
            show_msg("❌ Не удалось получить путь к файлу.", "#FF4D6D")
            return
        try:
            p = Path(f_path)
            if p.suffix.lower() == ".zip":
                with zipfile.ZipFile(p, "r") as zf:
                    conf_names = [n for n in zf.namelist() if n.lower().endswith(".conf") and not n.startswith("__MACOSX")]
                    if not conf_names:
                        show_msg("❌ Внутри архива нет файлов .conf!", "#FF4D6D")
                        return
                    imported_count = 0
                    last_content, last_stem = "", ""
                    for cname in conf_names:
                        content = zf.read(cname).decode("utf-8", errors="ignore")
                        if parse_wg_config(content):
                            stem = Path(cname).stem
                            save_raw_conf(stem, content)
                            last_content, last_stem = content, stem
                            imported_count += 1
                    if imported_count > 0:
                        apply_config_text(last_content, last_stem)
                        refresh_tunnels_list()
                        show_msg(f"📦 Импортировано профилей из архива: {imported_count}!", "#00FFAA")
            else:
                content = p.read_text(encoding="utf-8", errors="ignore")
                if apply_config_text(content, p.stem):
                    save_raw_conf(p.stem, content)
                    refresh_tunnels_list()
                    show_msg(f"📂 Профиль {p.stem} добавлен в список!", "#00FFAA")
        except Exception as ex:
            show_msg(f"❌ Ошибка импорта файла: {ex}", "#FF4D6D")

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def start_import_file(_):
        close_import_sheet()
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["conf", "zip", "txt"])

    qr_input = ft.TextField(label="Вставьте текст из QR-кода или буфера", multiline=True, min_lines=4, max_lines=7, bgcolor="#CC0A1128", border_color="#B800FF", text_size=12)
    def apply_qr_dialog(_):
        qr_dlg.open = False
        raw = qr_input.value or ""
        if apply_config_text(raw, "DoxaGuard_QR"):
            save_raw_conf("DoxaGuard_QR", raw)
            refresh_tunnels_list()
            show_msg("📷 Профиль из QR-кода добавлен в список!", "#00FFAA")
        page.update()

    qr_dlg = ft.AlertDialog(
        title=ft.Text("📷 Сканировать / Вставить QR", size=16, weight=ft.FontWeight.BOLD, color="#E066FF"),
        content=ft.Column([
            ft.Text("Отсканируйте QR камерой телефона, скопируйте текст и вставьте ниже:", size=12, color="#B8DCFF"),
            qr_input
        ], tight=True, spacing=8),
        actions=[
            ft.TextButton("Отмена", on_click=lambda _: setattr(qr_dlg, "open", False) or page.update()),
            ft.ElevatedButton("Загрузить", bgcolor="#FF1E56", color="#FFFFFF", on_click=apply_qr_dialog)
        ],
        bgcolor="#0A1128"
    )
    page.overlay.append(qr_dlg)

    def start_import_qr(_):
        close_import_sheet()
        qr_input.value = ""
        qr_dlg.open = True
        page.update()

    def sheet_item(icon_txt, title_txt, sub_txt, on_tap, accent="#B800FF"):
        return ft.Container(
            content=ft.Row([
                ft.Text(icon_txt, size=24),
                ft.Column([
                    ft.Text(title_txt, size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    ft.Text(sub_txt, size=11, color="#B8DCFF"),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=accent)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=12, border_radius=12, bgcolor="#CC120624", border=ft.border.all(1.5, accent), on_click=on_tap
        )

    import_sheet = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("➕ ДОБАВИТЬ ТУННЕЛЬ", size=16, weight=ft.FontWeight.W_900, color="#E066FF"),
                    ft.IconButton(ft.Icons.CLOSE, icon_color="#FF4D6D", on_click=lambda _: close_import_sheet())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sheet_item("📂", "Импорт из файла или архива", "Добавить .conf или все конфиги из .zip архива", start_import_file, "#FF1E56"),
                sheet_item("📷", "Сканировать QR-код", "Вставить распознанный QR-код конфига", start_import_qr, "#B800FF"),
                sheet_item("✨", "Создать с нуля", "Сгенерировать новые ключи и настроить вручную", on_create_scratch, "#00FFAA"),
            ], tight=True, spacing=10),
            padding=18, bgcolor="#0A1128", border_radius=ft.border_radius.only(top_left=22, top_right=22), border=ft.border.all(2, "#FF1E56")
        ),
        bgcolor="#0A1128"
    )
    page.overlay.append(import_sheet)

    def open_import_sheet(_):
        import_sheet.open = True
        page.update()

    def close_import_sheet():
        import_sheet.open = False
        page.update()

    def save_files():
        if not priv_f.value.strip():
            on_gen(None)
        a_val = addr_f.value.strip() or "10.66.66.2/32"
        m_val = mtu_f.value.strip() or "1280"
        txt = f"# Built with DoxaGuard | DOXACHKAA | @Doxa_pubg_cfg\n[Interface]\nPrivateKey = {priv_f.value.strip()}\nAddress = {a_val}\nDNS = 1.1.1.1, 1.0.0.1\nMTU = {m_val}\n\n[Peer]\nPublicKey = {srv_f.value.strip()}\nEndpoint = {ep_f.value.strip()}\nAllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 10\n"
        prev_f.value = txt
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fn = (name_f.value.strip() or "DoxaGuard").replace(".conf", "")
        conf_p = OUT_DIR / f"{fn}.conf"
        conf_p.write_text(txt, encoding="utf-8")
        with zipfile.ZipFile(OUT_DIR / f"{fn}_protected.zip", "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{fn}.conf", txt)
        refresh_tunnels_list()
        return fn, conf_p

    def on_save(_):
        try:
            fn, _ = save_files()
            show_msg(f"✅ Профиль {fn}.conf добавлен в список и сохранён в Download!", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка сохранения: {ex}", "#FF4D6D")

    def bg_wrap(ctrl):
        return ft.Stack([
            ft.Image(src="bg.png", fit=ft.ImageFit.COVER, width=1080, height=2400, opacity=0.92),
            ft.Container(content=ctrl, padding=14, gradient=ft.LinearGradient(begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=["#44040B1C", "#AA040B1C"]), expand=True)
        ], expand=True)

    def open_main():
        page.clean()
        page.floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD, bgcolor="#FF1E56", foreground_color="#FFFFFF", shape=ft.CircleBorder(), on_click=open_import_sheet, tooltip="Импорт / Создать профиль"
        )
        tunnels_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("⚡ МОИ ТУННЕЛИ DOXAGUARD", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    status_badge,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                tunnels_col,
            ], spacing=8),
            padding=12, border_radius=14, bgcolor="#CC0A1128", border=ft.border.all(2, "#B800FF"), shadow=[ft.BoxShadow(blur_radius=14, color="#9D00FF")]
        )
        frame = ft.Container(
            content=ft.Column([
                ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD • @Doxa_pubg_cfg", size=12, weight=ft.FontWeight.BOLD, color="#99CCFF")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                tunnels_panel,
                ft.Row([
                    neon_btn("🔑 Ключи", on_gen, "#B800FF", "#9D00FF", "#CC1D0836", expand=True),
                    neon_btn("⚡ Собрать VPN", on_save, "#FF1E56", "#FF0044", "#CC2B0618", expand=True),
                ], spacing=10),
                priv_f, pub_f, srv_f, ep_f,
                ft.Row([addr_f, mtu_f], spacing=10),
                name_f, prev_f,
                ft.Container(content=log_text, bgcolor="#CC0A0F24", padding=12, border_radius=12, border=ft.border.all(1.5, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=10, color="#FF0044")]),
                ft.Container(height=60)
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=16, border_radius=18, bgcolor="#55060D21", border=ft.border.all(2, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=18, spread_radius=1, color="#FF0044")], expand=True
        )
        page.add(bg_wrap(frame))
        on_gen(None)
        refresh_tunnels_list()

    pwd_in = ft.TextField(label="Введите пароль доступа", password=True, can_reveal_password=True, bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF")
    err_t = ft.Text("", color="#FF4D6D", size=12)
    def login(_):
        if pwd_in.value.strip() == APP_PWD:
            open_main()
        else:
            err_t.value = "❌ Неверный пароль!"
            page.update()

    card = ft.Container(
        content=ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD v1.0 • @Doxa_pubg_cfg", size=12, color="#B8DCFF"), pwd_in, neon_btn("ВОЙТИ В DOXAGUARD", login, width=260), err_t], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
        padding=24, margin=ft.margin.only(top=70), bgcolor="#B3070E24", border_radius=20, border=ft.border.all(2.5, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=22, spread_radius=2, color="#FF0044")]
    )
    page.add(bg_wrap(card))

ft.app(target=main, assets_dir="assets")

def main(page: ft.Page):
    page.title = "DOXAGUARD | DOXACHKAA"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#060E22"
    page.padding = 0

    page.overlay.append(ft.Container(content=ft.Text("🐉 @Doxa_pubg_cfg", size=11, weight=ft.FontWeight.BOLD, color="#FFFFFF"), bgcolor="#CC120624", border=ft.border.all(1.5, "#FF1E56"), border_radius=20, padding=ft.padding.symmetric(horizontal=10, vertical=4), shadow=[ft.BoxShadow(blur_radius=10, color="#FF0044")], right=12, top=12))

    dev_model = get_device_model()
    state = {"active_tunnel": None, "tab": 0, "fps": 120, "pubg_ver": "GLOBAL", "scheme": "Apply", "shizuku_ok": False}
    status_badge = ft.Text("🔴 СТАТУС: ОТКЛЮЧЕНО", size=12, weight=ft.FontWeight.BOLD, color="#FF4D6D")
    log_text = ft.Text("Готов к работе", size=12, color="#F2D9FF", selectable=True)
    fps_log = ft.Text("Выберите версию PUBG, FPS (60/90/120/165) и нажмите APPLY FPS", size=12, color="#00FFAA", selectable=True)
    tunnels_col = ft.Column(spacing=8)

    def show_msg(msg, color="#E066FF"):
        log_text.value, log_text.color = msg, color
        page.update()

    fbg, rneon = "#CC0A1128", "#FF1E56"
    priv_f = ft.TextField(label="PrivateKey клиента", bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF", text_size=12)
    pub_f = ft.TextField(label="Ваш PublicKey (для сервера)", read_only=True, bgcolor=fbg, border_color=rneon, text_size=12)
    srv_f = ft.TextField(label="PublicKey сервера", value="bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=", bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF", text_size=12)
    ep_f = ft.TextField(label="Endpoint (IP:PORT)", value="162.159.192.1:2408", bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF", text_size=12)
    addr_f = ft.TextField(label="Address", value="10.66.66.2/32", bgcolor=fbg, border_color=rneon, text_size=12, expand=True)
    mtu_f = ft.TextField(label="MTU", value="1280", bgcolor=fbg, border_color=rneon, text_size=12, width=100)
    name_f = ft.TextField(label="Имя файла", value="DoxaGuard", bgcolor=fbg, border_color=rneon, text_size=12)
    prev_f = ft.TextField(label="Готовый код VPN.conf", multiline=True, min_lines=5, max_lines=8, bgcolor=fbg, border_color=rneon, text_size=11)

    def apply_config_text(raw_text: str, profile_name: str = ""):
        cfg = parse_wg_config(raw_text)
        if not cfg:
            show_msg("❌ Не удалось распознать конфиг VPN!", "#FF4D6D")
            return False
        if "privatekey" in cfg:
            priv_f.value = cfg["privatekey"]
            derived_pub = pub_from_priv(cfg["privatekey"])
            if derived_pub:
                pub_f.value = derived_pub
        if "publickey" in cfg:
            srv_f.value = cfg["publickey"]
        if "endpoint" in cfg:
            ep_f.value = cfg["endpoint"]
        if "address" in cfg:
            addr_f.value = cfg["address"]
        if "mtu" in cfg:
            mtu_f.value = cfg["mtu"]
        if profile_name:
            name_f.value = profile_name.replace(".conf", "").replace(".zip", "")
        prev_f.value = raw_text.strip()
        return True

    def save_raw_conf(name: str, raw_text: str) -> Path:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        clean_name = (name.strip() or "DoxaGuard").replace(".conf", "")
        conf_p = OUT_DIR / f"{clean_name}.conf"
        conf_p.write_text(raw_text.strip() + "\n", encoding="utf-8")
        return conf_p

    def toggle_tunnel_item(conf_path: Path, is_on: bool):
        if is_on:
            state["active_tunnel"] = conf_path.name
            status_badge.value = f"🟢 АКТИВЕН: {conf_path.stem}"
            status_badge.color = "#00FFAA"
            try:
                content = conf_path.read_text(encoding="utf-8", errors="ignore")
                apply_config_text(content, conf_path.stem)
                show_msg(f"🚀 Включён туннель {conf_path.name}!", "#00FFAA")
                page.launch_url(f"file://{conf_path}")
            except Exception as ex:
                show_msg(f"Профиль {conf_path.name} выбран ({ex})", "#00FFAA")
        else:
            if state["active_tunnel"] == conf_path.name:
                state["active_tunnel"] = None
                status_badge.value = "🔴 СТАТУС: ОТКЛЮЧЕНО"
                status_badge.color = "#FF4D6D"
                show_msg(f"⏹ Туннель {conf_path.stem} отключён.", "#FF4D6D")
        refresh_tunnels_list()

    def load_tunnel_to_editor(conf_path: Path):
        try:
            content = conf_path.read_text(encoding="utf-8", errors="ignore")
            if apply_config_text(content, conf_path.stem):
                show_msg(f"📝 Профиль {conf_path.stem} загружен в редактор.", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка чтения: {ex}", "#FF4D6D")

    def delete_tunnel_item(conf_path: Path):
        try:
            if state["active_tunnel"] == conf_path.name:
                state["active_tunnel"] = None
                status_badge.value = "🔴 СТАТУС: ОТКЛЮЧЕНО"
                status_badge.color = "#FF4D6D"
            conf_path.unlink(missing_ok=True)
            show_msg(f"🗑 Профиль {conf_path.stem} удалён.", "#FF4D6D")
            refresh_tunnels_list()
        except Exception as ex:
            show_msg(f"Ошибка удаления: {ex}", "#FF4D6D")

    def refresh_tunnels_list():
        tunnels_col.controls.clear()
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(OUT_DIR.glob("*.conf"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            tunnels_col.controls.append(ft.Text("Нет сохранённых VPN. Нажмите + чтобы импортировать или создать.", size=12, color="#99CCFF"))
        else:
            for f in files:
                is_active = (state["active_tunnel"] == f.name)
                card = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f.stem, size=14, weight=ft.FontWeight.BOLD, color="#00FFAA" if is_active else "#FFFFFF"),
                                ft.Text("Нажмите, чтобы открыть в редакторе", size=10, color="#99CCFF"),
                            ], spacing=1),
                            on_click=lambda _, p=f: load_tunnel_to_editor(p),
                            expand=True,
                        ),
                        ft.Switch(value=is_active, active_color="#00FFAA", active_track_color="#0A3D2E", inactive_thumb_color="#FF1E56", inactive_track_color="#2B0618", on_change=lambda e, p=f: toggle_tunnel_item(p, e.control.value)),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#FF4D6D", icon_size=20, on_click=lambda _, p=f: delete_tunnel_item(p)),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=12, bgcolor="#CC140829", border=ft.border.all(1.5, "#00FFAA" if is_active else "#B800FF"),
                )
                tunnels_col.controls.append(card)
        page.update()

    def on_gen(_):
        try:
            priv_f.value, pub_f.value = gen_wg_keys()
            show_msg("🔑 Новая пара ключей сгенерирована!", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка: {ex}", "#FF4D6D")

    def on_create_scratch(_):
        close_import_sheet()
        priv_f.value, pub_f.value = gen_wg_keys()
        srv_f.value, ep_f.value, prev_f.value = "", "", ""
        addr_f.value, mtu_f.value, name_f.value = "10.66.66.2/32", "1280", "DoxaGuard_New"
        show_msg("✨ Создан новый пустой профиль. Заполните поля и нажмите «Собрать VPN».", "#00FFAA")

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files or not e.files.path:
            return
        try:
            p = Path(e.files.path)
            if p.suffix.lower() == ".zip":
                with zipfile.ZipFile(p, "r") as zf:
                    conf_names = [n for n in zf.namelist() if n.lower().endswith(".conf") and not n.startswith("__MACOSX")]
                    if not conf_names:
                        show_msg("❌ Внутри архива нет файлов .conf!", "#FF4D6D")
                        return
                    cnt, last_c, last_s = 0, "", ""
                    for cname in conf_names:
                        c = zf.read(cname).decode("utf-8", errors="ignore")
                        if parse_wg_config(c):
                            st = Path(cname).stem
                            save_raw_conf(st, c)
                            last_c, last_s, cnt = c, st, cnt + 1
                    if cnt > 0:
                        apply_config_text(last_c, last_s)
                        refresh_tunnels_list()
                        show_msg(f"📦 Импортировано профилей из архива: {cnt}!", "#00FFAA")
            else:
                c = p.read_text(encoding="utf-8", errors="ignore")
                if apply_config_text(c, p.stem):
                    save_raw_conf(p.stem, c)
                    refresh_tunnels_list()
                    show_msg(f"📂 Профиль {p.stem} добавлен в список!", "#00FFAA")
        except Exception as ex:
            show_msg(f"❌ Ошибка импорта: {ex}", "#FF4D6D")

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def start_import_file(_):
        close_import_sheet()
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["conf", "zip", "txt"])

    qr_input = ft.TextField(label="Вставьте текст из QR-кода", multiline=True, min_lines=4, max_lines=7, bgcolor="#CC0A1128", border_color="#B800FF", text_size=12)
    def apply_qr_dialog(_):
        qr_dlg.open = False
        raw = qr_input.value or ""
        if apply_config_text(raw, "DoxaGuard_QR"):
            save_raw_conf("DoxaGuard_QR", raw)
            refresh_tunnels_list()
            show_msg("📷 Профиль из QR-кода добавлен в список!", "#00FFAA")
        page.update()

    qr_dlg = ft.AlertDialog(
        title=ft.Text("📷 Сканировать / Вставить QR", size=16, weight=ft.FontWeight.BOLD, color="#E066FF"),
        content=ft.Column([ft.Text("Вставьте текст конфига из QR:", size=12, color="#B8DCFF"), qr_input], tight=True, spacing=8),
        actions=[ft.TextButton("Отмена", on_click=lambda _: setattr(qr_dlg, "open", False) or page.update()), ft.ElevatedButton("Загрузить", bgcolor="#FF1E56", color="#FFFFFF", on_click=apply_qr_dialog)],
        bgcolor="#0A1128"
    )
    page.overlay.append(qr_dlg)

    def start_import_qr(_):
        close_import_sheet()
        qr_input.value = ""
        qr_dlg.open = True
        page.update()

    def sheet_item(icon_txt, title_txt, sub_txt, on_tap, accent="#B800FF"):
        return ft.Container(
            content=ft.Row([ft.Text(icon_txt, size=24), ft.Column([ft.Text(title_txt, size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"), ft.Text(sub_txt, size=11, color="#B8DCFF")], spacing=2, expand=True), ft.Icon(ft.Icons.CHEVRON_RIGHT, color=accent)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=12, border_radius=12, bgcolor="#CC120624", border=ft.border.all(1.5, accent), on_click=on_tap
        )

    import_sheet = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("➕ ДОБАВИТЬ ТУННЕЛЬ", size=16, weight=ft.FontWeight.W_900, color="#E066FF"), ft.IconButton(ft.Icons.CLOSE, icon_color="#FF4D6D", on_click=lambda _: close_import_sheet())], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sheet_item("📂", "Импорт из файла или архива", "Добавить .conf или все конфиги из .zip", start_import_file, "#FF1E56"),
                sheet_item("📷", "Сканировать QR-код", "Вставить распознанный QR-код конфига", start_import_qr, "#B800FF"),
                sheet_item("✨", "Создать с нуля", "Сгенерировать новые ключи вручную", on_create_scratch, "#00FFAA"),
            ], tight=True, spacing=10),
            padding=18, bgcolor="#0A1128", border_radius=ft.border_radius.only(top_left=22, top_right=22), border=ft.border.all(2, "#FF1E56")
        ),
        bgcolor="#0A1128"
    )
    page.overlay.append(import_sheet)

    def open_import_sheet(_):
        import_sheet.open = True
        page.update()

    def close_import_sheet():
        import_sheet.open = False
        page.update()

    def save_files():
        if not priv_f.value.strip():
            on_gen(None)
        a_val = addr_f.value.strip() or "10.66.66.2/32"
        m_val = mtu_f.value.strip() or "1280"
        txt = f"# Built with DoxaGuard | DOXACHKAA | @Doxa_pubg_cfg\n[Interface]\nPrivateKey = {priv_f.value.strip()}\nAddress = {a_val}\nDNS = 1.1.1.1, 1.0.0.1\nMTU = {m_val}\n\n[Peer]\nPublicKey = {srv_f.value.strip()}\nEndpoint = {ep_f.value.strip()}\nAllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 10\n"
        prev_f.value = txt
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fn = (name_f.value.strip() or "DoxaGuard").replace(".conf", "")
        conf_p = OUT_DIR / f"{fn}.conf"
        conf_p.write_text(txt, encoding="utf-8")
        with zipfile.ZipFile(OUT_DIR / f"{fn}_protected.zip", "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{fn}.conf", txt)
        refresh_tunnels_list()
        return fn, conf_p

    def on_save(_):
        try:
            fn, _ = save_files()
            show_msg(f"✅ Профиль {fn}.conf добавлен в список и сохранён в Download!", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка сохранения: {ex}", "#FF4D6D")

    # --- ВТОРОЕ ОКНО: FPS UNLOCKER (60 / 90 / 120 / 165 FPS + game_patch + Active.sav) ---
    def check_shizuku_status(_):
        ok, out = run_shizuku_cmd("id")
        state["shizuku_ok"] = ok
        if ok:
            fps_log.value = f"🟢 Shizuku Mode активен! Готов к прошивке game_patch + Active.sav ({out})"
            fps_log.color = "#00FFAA"
        else:
            fps_log.value = f"🔴 Shizuku не подключён: {out}\nОткройте Shizuku -> «Использовать в терминале» -> «Экспорт файлов» в Download/Shizuku."
            fps_log.color = "#FF4D6D"
        open_main()

    def on_apply_fps(_):
        pkg = PUBG_PACKAGES[state["pubg_ver"]]
        ok, msg = process_fps_unlock(pkg, state["fps"], state["scheme"])
        fps_log.value = msg
        fps_log.color = "#00FFAA" if ok else "#FF4D6D"
        page.update()

    def launch_pubg_app(_):
        pkg = PUBG_PACKAGES[state["pubg_ver"]]
        ok, _ = run_shizuku_cmd(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
        if not ok:
            try:
                page.launch_url(f"android-app://{pkg}")
            except Exception:
                fps_log.value = f"Откройте PUBG ({state['pubg_ver']}) с рабочего стола — {state['fps']} FPS и game_patch готовы!"
                page.update()

    def bg_wrap(ctrl):
        return ft.Stack([
            ft.Image(src="bg.png", fit=ft.ImageFit.COVER, width=1080, height=2400, opacity=0.92),
            ft.Container(content=ctrl, padding=14, gradient=ft.LinearGradient(begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=["#44040B1C", "#AA040B1C"]), expand=True)
        ], expand=True)

    def switch_tab(idx: int):
        state["tab"] = idx
        open_main()

    def radio_pill(label: str, selected: bool, on_tap, expand=True):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED if selected else ft.Icons.RADIO_BUTTON_UNCHECKED, color="#00FFAA" if selected else "#99CCFF", size=18),
                ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color="#00FFAA" if selected else "#FFFFFF"),
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
            border_radius=12,
            bgcolor="#CC1A0836" if selected else "#CC0A1128",
            border=ft.border.all(1.5, "#00FFAA" if selected else "#B800FF"),
            expand=expand,
            on_click=on_tap,
        )

    def open_main():
        page.clean()
        is_vpn = (state["tab"] == 0)
        page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor="#FF1E56", foreground_color="#FFFFFF", shape=ft.CircleBorder(), on_click=open_import_sheet, tooltip="Импорт / Создать профиль") if is_vpn else None

        nav_bar = ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Text("🛡 VPN ТУННЕЛИ", size=12, weight=ft.FontWeight.BOLD, color="#00FFAA" if is_vpn else "#FFFFFF"), padding=10, alignment=ft.alignment.center, border_radius=10, bgcolor="#CC1D0836" if is_vpn else "transparent", border=ft.border.all(1.5, "#00FFAA" if is_vpn else "#44FFFFFF"), expand=True, on_click=lambda _: switch_tab(0)),
                ft.Container(content=ft.Text("🚀 FPS UNLOCKER", size=12, weight=ft.FontWeight.BOLD, color="#00FFAA" if not is_vpn else "#FFFFFF"), padding=10, alignment=ft.alignment.center, border_radius=10, bgcolor="#CC1D0836" if not is_vpn else "transparent", border=ft.border.all(1.5, "#00FFAA" if not is_vpn else "#44FFFFFF"), expand=True, on_click=lambda _: switch_tab(1)),
            ], spacing=8),
            padding=6, border_radius=14, bgcolor="#CC0A1128", border=ft.border.all(1.5, "#B800FF")
        )

        if is_vpn:
            tunnels_panel = ft.Container(
                content=ft.Column([ft.Row([ft.Text("⚡ МОИ ТУННЕЛИ DOXAGUARD", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF"), status_badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), tunnels_col], spacing=8),
                padding=12, border_radius=14, bgcolor="#CC0A1128", border=ft.border.all(2, "#B800FF"), shadow=[ft.BoxShadow(blur_radius=14, color="#9D00FF")]
            )
            body_controls = [
                ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD • @Doxa_pubg_cfg", size=12, weight=ft.FontWeight.BOLD, color="#99CCFF")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                nav_bar, tunnels_panel,
                ft.Row([neon_btn("🔑 Ключи", on_gen, "#B800FF", "#9D00FF", "#CC1D0836", expand=True), neon_btn("⚡ Собрать VPN", on_save, "#FF1E56", "#FF0044", "#CC2B0618", expand=True)], spacing=10),
                priv_f, pub_f, srv_f, ep_f, ft.Row([addr_f, mtu_f], spacing=10), name_f, prev_f,
                ft.Container(content=log_text, bgcolor="#CC0A0F24", padding=12, border_radius=12, border=ft.border.all(1.5, "#FF1E56")),
                ft.Container(height=60)
            ]
        else:
            device_hero = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"{state['fps']} FPS", size=28, weight=ft.FontWeight.W_900, color="#FFFFFF"),
                        ft.Container(content=ft.Text(dev_model, size=12, weight=ft.FontWeight.BOLD, color="#E066FF"), padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=10, bgcolor="#CC140829", border=ft.border.all(1, "#B800FF"), width=180),
                        ft.Container(content=ft.Text(f"{state['fps']} FPS + game_patch", size=12, weight=ft.FontWeight.BOLD, color="#00FFAA"), padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=10, bgcolor="#CC140829", border=ft.border.all(1, "#00FFAA"), width=180),
                    ], spacing=8, expand=True),
                    ft.Column([
                        ft.Container(
                            content=ft.Text("Shizuku Mode" if state["shizuku_ok"] else "Check Shizuku", size=11, weight=ft.FontWeight.BOLD, color="#060E22" if state["shizuku_ok"] else "#FFFFFF"),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=20, bgcolor="#00FFAA" if state["shizuku_ok"] else "#FF1E56", on_click=check_shizuku_status
                        ),
                        ft.Container(
                            content=ft.Column([ft.Text("FPS UNLOCKER", size=7, color="#00FFAA", weight=ft.FontWeight.BOLD), ft.Text(dev_model[:12], size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=78, height=118, border_radius=14, bgcolor="#060E22", border=ft.border.all(2.5, "#00FFAA"), shadow=[ft.BoxShadow(blur_radius=12, color="#00FFAA")]
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=8)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=14, border_radius=16, bgcolor="#CC0A1128", border=ft.border.all(2, "#B800FF"), shadow=[ft.BoxShadow(blur_radius=14, color="#9D00FF")]
            )
            ver_row1 = ft.Row([
                radio_pill("GLOBAL", state["pubg_ver"] == "GLOBAL", lambda _: state.update({"pubg_ver": "GLOBAL"}) or open_main()),
                radio_pill("INDIAN", state["pubg_ver"] == "INDIAN", lambda _: state.update({"pubg_ver": "INDIAN"}) or open_main()),
            ], spacing=8)
            ver_row2 = ft.Row([
                radio_pill("KOREA", state["pubg_ver"] == "KOREA", lambda _: state.update({"pubg_ver": "KOREA"}) or open_main()),
                radio_pill("VIETNAM", state["pubg_ver"] == "VIETNAM", lambda _: state.update({"pubg_ver": "VIETNAM"}) or open_main()),
            ], spacing=8)
            fps_row1 = ft.Row([
                radio_pill("60 FPS", state["fps"] == 60, lambda _: state.update({"fps": 60}) or open_main()),
                radio_pill("90 FPS", state["fps"] == 90, lambda _: state.update({"fps": 90}) or open_main()),
            ], spacing=8)
            fps_row2 = ft.Row([
                radio_pill("120 FPS", state["fps"] == 120, lambda _: state.update({"fps": 120}) or open_main()),
                radio_pill("165 FPS", state["fps"] == 165, lambda _: state.update({"fps": 165}) or open_main()),
            ], spacing=8)
            scheme_row = ft.Row([
                radio_pill("📂 Apply (Shizuku)", state["scheme"] == "Apply", lambda _: state.update({"scheme": "Apply"}) or open_main()),
                radio_pill("💾 Save", state["scheme"] == "Save", lambda _: state.update({"scheme": "Save"}) or open_main()),
            ], spacing=8)

            body_controls = [
                ft.Column([neon_title("DOXACHKAA", 34), ft.Text("FPS UNLOCKER • @Doxa_pubg_cfg", size=12, weight=ft.FontWeight.BOLD, color="#00FFAA")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                nav_bar, device_hero,
                ft.Text("Select Your Game Version", size=13, weight=ft.FontWeight.BOLD, color="#99CCFF"),
                ver_row1, ver_row2,
                ft.Text("Select FPS (60 / 90 / 120 / 165)", size=13, weight=ft.FontWeight.BOLD, color="#99CCFF"),
                fps_row1, fps_row2,
                ft.Text("Select Files Scheme (UserCustom + Active.sav + game_patch)", size=12, weight=ft.FontWeight.BOLD, color="#99CCFF"),
                scheme_row,
                neon_btn(f"» APPLY {state['fps']} FPS", on_apply_fps, "#00FFAA", "#00CC88", "#CC0A2E24"),
                neon_btn(f"🎮 ЗАПУСТИТЬ PUBG ({state['pubg_ver']})", launch_pubg_app, "#FF1E56", "#FF0044", "#CC2B0618"),
                ft.Container(content=fps_log, bgcolor="#CC0A0F24", padding=12, border_radius=12, border=ft.border.all(1.5, "#00FFAA")),
            ]

        frame = ft.Container(
            content=ft.Column(body_controls, spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=16, border_radius=18, bgcolor="#55060D21", border=ft.border.all(2, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=18, spread_radius=1, color="#FF0044")], expand=True
        )
        page.add(bg_wrap(frame))
        if is_vpn:
            on_gen(None)
            refresh_tunnels_list()

    pwd_in = ft.TextField(label="Введите пароль доступа", password=True, can_reveal_password=True, bgcolor=fbg, border_color=rneon, focused_border_color="#E066FF")
    err_t = ft.Text("", color="#FF4D6D", size=12)
    def login(_):
        if pwd_in.value.strip() == APP_PWD:
            open_main()
        else:
            err_t.value = "❌ Неверный пароль!"
            page.update()

    card = ft.Container(
        content=ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD v3.0 PRO • @Doxa_pubg_cfg", size=12, color="#B8DCFF"), pwd_in, neon_btn("ВОЙТИ В DOXAGUARD", login, width=260), err_t], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
        padding=24, margin=ft.margin.only(top=70), bgcolor="#B3070E24", border_radius=20, border=ft.border.all(2.5, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=22, spread_radius=2, color="#FF0044")]
    )
    page.add(bg_wrap(card))

ft.app(target=main, assets_dir="assets")
