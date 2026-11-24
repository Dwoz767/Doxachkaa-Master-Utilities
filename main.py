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

    state = {"connected": False}
    status_badge = ft.Text("🔴 СТАТУС: ОТКЛЮЧЕНО", size=13, weight=ft.FontWeight.BOLD, color="#FF4D6D")
    log_text = ft.Text("Готов к работе", size=12, color="#F2D9FF", selectable=True)

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

    def on_gen(_):
        try:
            priv_f.value, pub_f.value = gen_wg_keys()
            show_msg("🔑 Новая пара ключей сгенерирована!", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка: {ex}", "#FF4D6D")

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
        return fn, conf_p

    def on_save(_):
        try:
            fn, _ = save_files()
            show_msg(f"✅ Сохранено в Download:\n• {fn}.conf\n• {fn}_protected.zip", "#E066FF")
        except Exception as ex:
            show_msg(f"Ошибка сохранения: {ex}", "#FF4D6D")

    def on_toggle_vpn(e):
        try:
            if not state["connected"]:
                fn, conf_p = save_files()
                state["connected"] = True
                vpn_switch.value = True
                status_badge.value = "🟢 СТАТУС: АКТИВИРОВАНО (WIREGUARD)"
                status_badge.color = "#00FFAA"
                show_msg(f"🚀 Профиль {fn}.conf собран! Выберите WireGuard / AmneziaWG для включения туннеля.", "#00FFAA")
                page.launch_url(f"file://{conf_p}")
            else:
                state["connected"] = False
                vpn_switch.value = False
                status_badge.value = "🔴 СТАТУС: ОТКЛЮЧЕНО"
                status_badge.color = "#FF4D6D"
                show_msg("⏹ Туннель переведён в режим отключения. Выключите тумблер в WireGuard.", "#FF4D6D")
        except Exception as ex:
            show_msg(f"Файл сохранён в Download. Откройте его в WireGuard ({ex})", "#E066FF")

    vpn_switch = ft.Switch(value=False, active_color="#00FFAA", active_track_color="#0A3D2E", inactive_thumb_color="#FF1E56", inactive_track_color="#2B0618", on_change=on_toggle_vpn)

    def bg_wrap(ctrl):
        return ft.Stack([
            ft.Image(src="bg.png", fit=ft.ImageFit.COVER, width=1080, height=2400, opacity=0.92),
            ft.Container(content=ctrl, padding=14, gradient=ft.LinearGradient(begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=["#44040B1C", "#AA040B1C"]), expand=True)
        ], expand=True)

    def open_main():
        page.clean()
        vpn_panel = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("⚡ DOXAGUARD TUNNEL", size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    status_badge,
                ], spacing=2, expand=True),
                vpn_switch,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=12, border_radius=14, bgcolor="#CC140829",
            border=ft.border.all(2, "#B800FF"),
            shadow=[ft.BoxShadow(blur_radius=14, color="#9D00FF")]
        )
        frame = ft.Container(
            content=ft.Column([
                ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD • @Doxa_pubg_cfg", size=12, weight=ft.FontWeight.BOLD, color="#99CCFF")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                vpn_panel,
                ft.Row([neon_btn("🔑 Ключи", on_gen, "#B800FF", "#9D00FF", "#CC1D0836", expand=True), neon_btn("⚡ Собрать VPN", on_save, "#FF1E56", "#FF0044", "#CC2B0618", expand=True)], spacing=10),
                priv_f, pub_f, srv_f, ep_f,
                ft.Row([addr_f, mtu_f], spacing=10),
                name_f, prev_f,
                ft.Container(content=log_text, bgcolor="#CC0A0F24", padding=12, border_radius=12, border=ft.border.all(1.5, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=10, color="#FF0044")])
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=16, border_radius=18, bgcolor="#55060D21", border=ft.border.all(2, "#FF1E56"), shadow=[ft.BoxShadow(blur_radius=18, spread_radius=1, color="#FF0044")], expand=True
        )
        page.add(bg_wrap(frame))
        on_gen(None)

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
