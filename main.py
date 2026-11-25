import os, re, base64, zipfile, subprocess, struct, zlib
from pathlib import Path
import flet as ft
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

APP_PWD = "Doxachka2001"
OUT_DIR = Path("/storage/emulated/0/Download")
FPS_OUT_DIR = Path("/storage/emulated/0/Download/DoxaGuard_FPS")
PUBG_PACKAGES = {"GLOBAL": "com.tencent.ig", "INDIAN": "com.pubg.imobile", "KOREA": "com.pubg.krmobile", "VIETNAM": "com.vng.pubgmobile"}
FPS_STEPS = [60, 90, 120, 165]

def get_device_model():
    try:
        out = subprocess.check_output(["getprop", "ro.product.model"], text=True, timeout=2).strip()
        if out: return out
    except Exception: pass
    return "Android Gaming Device"

def gen_wg_keys():
    priv_obj = x25519.X25519PrivateKey.generate()
    priv_b = priv_obj.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    pub_b = priv_obj.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(priv_b).decode(), base64.b64encode(pub_b).decode()

def pub_from_priv(priv_b64):
    try:
        raw = base64.b64decode(priv_b64.strip())
        if len(raw) == 32:
            priv_obj = x25519.X25519PrivateKey.from_private_bytes(raw)
            return base64.b64encode(priv_obj.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    except Exception: pass
    return ""

def parse_wg_config(text):
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ";", "[")) and "=" in line:
            k, v = line.split("=", 1)
            data[k.strip().lower()] = v.strip()
    return data

def build_user_custom_ini(fps):
    lv = {60: 6, 90: 7, 120: 8, 165: 9}.get(fps, 8)
    return f"[UserCustom DeviceProfile]\n+CVars=r.PUBGQualityLevel=1\n+CVars=r.UserQualitySetting=1\n+CVars=r.PUBGLobbyFPS={lv}\n+CVars=r.PUBGBattleFPS={lv}\n+CVars=r.PUBGMaxFPS={fps}\n+CVars=t.MaxFPS={fps}\n+CVars=r.VSync=0\n+CVars=r.PUBGDeviceFPSLow={lv}\n+CVars=r.PUBGDeviceFPSMid={lv}\n+CVars=r.PUBGDeviceFPSHigh={lv}\n+CVars=r.PUBGDeviceFPSHDR={lv}\n+CVars=r.PUBGStyle=2\n+CVars=r.ShadowQuality=0\n"

def build_active_sav(fps):
    fc = {60: 6, 90: 7, 120: 8, 165: 9}.get(fps, 8)
    props = bytearray(b"GVAS\x02\x00\x00\x00\x04\x00\x00\x00\x16\x00\x00\x00\x00\x00\x00\x00")
    for pn in [b"BattleFPS\x00", b"LobbyFPS\x00", b"ArtQuality\x00"]:
        val = 1 if pn.startswith(b"Art") else fc
        props += struct.pack("<I", len(pn)) + pn + struct.pack("<I", 12) + b"IntProperty\x00" + struct.pack("<Q", 4) + b"\x00" + struct.pack("<I", val)
    return bytes(props + struct.pack("<I", 5) + b"None\x00")

def build_game_patch_pak(fps):
    ini = build_user_custom_ini(fps).encode("utf-8")
    comp = zlib.compress(ini, level=6)
    en = b"ShadowTrackerExtra/Config/DefaultDeviceProfiles.ini\x00"
    hdr = struct.pack("<QQQI", 0, len(comp), len(ini), 1) + b"\x00" * 21 + struct.pack("<I", len(ini))
    payload = bytearray(hdr + comp)
    idx_off = len(payload)
    idx = bytearray(struct.pack("<I", 1) + b"\x00" + struct.pack("<I", 1) + struct.pack("<I", len(en)) + en + hdr)
    payload += idx + struct.pack("<IIQQ20s", 0x5A6F12E1, 4, idx_off, len(idx), b"\x00" * 20)
    return bytes(payload)

def run_shizuku_cmd(shell_cmd):
    rish = next((c for c in [Path("assets/rish"), Path(__file__).parent / "assets/rish", Path("/storage/emulated/0/Download/Shizuku/rish"), Path("/storage/emulated/0/Download/rish")] if c.exists()), None)
    if not rish: return False, "Не найден файл rish"
    try:
        cd = Path("/data/data/com.doxaguard.doxaguard/cache")
        if not cd.exists(): cd = Path.cwd()
        lr, ld = cd / "rish", cd / "rish_shizuku.dex"
        rish_txt = rish.read_text(encoding="utf-8", errors="ignore")
        rish_txt = re.sub(r"PKG=.*", "PKG=com.doxaguard.doxaguard", rish_txt)
        lr.write_text(rish_txt, encoding="utf-8")
        dex_src = rish.parent / "rish_shizuku.dex"
        if dex_src.exists(): ld.write_bytes(dex_src.read_bytes())
        os.chmod(lr, 0o755)
        env = os.environ.copy()
        env["RISH_APPLICATION_ID"] = "com.doxaguard.doxaguard"
        res = subprocess.run(["sh", str(lr), "-c", shell_cmd], stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, timeout=10)
        return (True, res.stdout.strip()) if res.returncode == 0 else (False, (res.stderr or res.stdout or "Ошибка Shizuku").strip())
    except Exception as ex: return False, str(ex)

def process_fps_unlock(pkg, fps, scheme):
    FPS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    ip, sp, pn = FPS_OUT_DIR / "UserCustom.ini", FPS_OUT_DIR / "Active.sav", f"game_patch_4.7.0.99{fps}.pak"
    pp = FPS_OUT_DIR / pn
    ip.write_text(build_user_custom_ini(fps), encoding="utf-8")
    sp.write_bytes(build_active_sav(fps))
    pp.write_bytes(build_game_patch_pak(fps))
    if scheme == "Save": return True, f"💾 Комплект ({fps} FPS: UserCustom.ini + Active.sav + {pn}) сохранён в Download/DoxaGuard_FPS/"
    bg = f"/storage/emulated/0/Android/data/{pkg}/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved"
    cmd = f"mkdir -p '{bg}/Config/Android' '{bg}/SaveGames' '{bg}/Paks' && rm -f '{bg}/Paks/game_patch_3.6.0.99'*.pak '{bg}/Paks/game_patch_4.7.0.99'*.pak && cp '{ip}' '{bg}/Config/Android/UserCustom.ini' && cp '{sp}' '{bg}/SaveGames/Active.sav' && cp '{pp}' '{bg}/Paks/{pn}' && chmod 666 '{bg}/Config/Android/UserCustom.ini' '{bg}/SaveGames/Active.sav' '{bg}/Paks/{pn}' && settings put system peak_refresh_rate {float(fps)} && settings put system min_refresh_rate {float(fps)}"
    ok, msg = run_shizuku_cmd(cmd)
    return (True, f"✅ APPLY ({fps} FPS): UserCustom.ini + Active.sav + {pn} залиты через Shizuku!") if ok else (False, f"⚠️ Файлы созданы, но Shizuku: {msg}")

def neon_title(txt, size=34):
    return ft.Text(txt, size=size, weight=ft.FontWeight.W_900, color="#E066FF", style=ft.TextStyle(shadow=[ft.BoxShadow(blur_radius=14, color="#B800FF"), ft.BoxShadow(blur_radius=28, color="#8A00E6")]))

def neon_btn(label, on_click, border="#FF1E56", glow="#FF0044", bg="#CC24072E", expand=False, width=None):
    return ft.Container(
        content=ft.ElevatedButton(label, on_click=on_click, bgcolor="transparent", color="#FFFFFF", style=ft.ButtonStyle(shadow_color="transparent", elevation=0, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=13))),
        bgcolor=bg, border=ft.border.all(2, border), border_radius=12, shadow=[ft.BoxShadow(blur_radius=14, spread_radius=1, color=glow)], expand=expand, width=width, alignment=ft.alignment.center,
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT), animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT), ink=True
    )

def main(page: ft.Page):
    page.title, page.theme_mode, page.bgcolor, page.padding = "DOXAGUARD | DOXACHKAA", ft.ThemeMode.DARK, "#060E22", 0
    page.overlay.append(ft.Container(content=ft.Text("🐉 @Doxa_pubg_cfg", size=11, weight=ft.FontWeight.BOLD, color="#FFFFFF"), bgcolor="#CC120624", border=ft.border.all(1.5, "#FF1E56"), border_radius=20, padding=ft.padding.symmetric(horizontal=10, vertical=4), shadow=[ft.BoxShadow(blur_radius=10, color="#FF0044")], right=12, top=12))

    dev_model = get_device_model()
    st = {"active": None, "fps": 120, "ver": "GLOBAL", "scheme": "Apply", "shizuku": False}
    status_badge = ft.Text("🔴 СТАТУС: ОТКЛЮЧЕНО", size=12, weight=ft.FontWeight.BOLD, color="#FF4D6D")
    log_text = ft.Text("Готов к работе", size=12, color="#F2D9FF", selectable=True)
    fps_log = ft.Text("Проведите ползунок FPS вправо (60 → 165) и нажмите APPLY FPS", size=12, color="#00FFAA", selectable=True)
    tunnels_col = ft.Column(spacing=8)

    def show_msg(m, c="#E066FF"):
        log_text.value, log_text.color = m, c; page.update()

    fbg, rneon = "#CC0A1128", "#FF1E56"
    priv_f = ft.TextField(label="PrivateKey клиента", bgcolor=fbg, border_color=rneon, text_size=12)
    pub_f = ft.TextField(label="Ваш PublicKey (для сервера)", read_only=True, bgcolor=fbg, border_color=rneon, text_size=12)
    srv_f = ft.TextField(label="PublicKey сервера", value="bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=", bgcolor=fbg, border_color=rneon, text_size=12)
    ep_f = ft.TextField(label="Endpoint (IP:PORT)", value="162.159.192.1:2408", bgcolor=fbg, border_color=rneon, text_size=12)
    addr_f = ft.TextField(label="Address", value="10.66.66.2/32", bgcolor=fbg, border_color=rneon, text_size=12, expand=True)
    mtu_f = ft.TextField(label="MTU", value="1280", bgcolor=fbg, border_color=rneon, text_size=12, width=100)
    name_f = ft.TextField(label="Имя файла", value="DoxaGuard", bgcolor=fbg, border_color=rneon, text_size=12)
    prev_f = ft.TextField(label="Готовый код VPN.conf", multiline=True, min_lines=5, max_lines=8, bgcolor=fbg, border_color=rneon, text_size=11)

    def apply_cfg(raw, pname=""):
        cfg = parse_wg_config(raw)
        if not cfg: show_msg("❌ Неверный конфиг!", "#FF4D6D"); return False
        if "privatekey" in cfg: priv_f.value, pub_f.value = cfg["privatekey"], pub_from_priv(cfg["privatekey"])
        if "publickey" in cfg: srv_f.value = cfg["publickey"]
        if "endpoint" in cfg: ep_f.value = cfg["endpoint"]
        if "address" in cfg: addr_f.value = cfg["address"]
        if "mtu" in cfg: mtu_f.value = cfg["mtu"]
        if pname: name_f.value = pname.replace(".conf", "").replace(".zip", "")
        prev_f.value = raw.strip(); return True

    def save_raw(n, raw):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        p = OUT_DIR / f"{(n.strip() or 'DoxaGuard').replace('.conf', '')}.conf"
        p.write_text(raw.strip() + "\n", encoding="utf-8"); return p

    def refresh_tunnels():
        tunnels_col.controls.clear()
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(OUT_DIR.glob("*.conf"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files: tunnels_col.controls.append(ft.Text("Нет сохранённых VPN. Нажмите + чтобы добавить.", size=12, color="#99CCFF"))
        for f in files:
            act = (st["active"] == f.name)
            def tog(e, p=f):
                st["active"] = p.name if e.control.value else None
                status_badge.value = f"🟢 АКТИВЕН: {p.stem}" if e.control.value else "🔴 СТАТУС: ОТКЛЮЧЕНО"
                status_badge.color = "#00FFAA" if e.control.value else "#FF4D6D"
                if e.control.value:
                    apply_cfg(p.read_text(encoding="utf-8", errors="ignore"), p.stem)
                    try: page.launch_url(f"file://{p}")
                    except Exception: pass
                refresh_tunnels()
            tunnels_col.controls.append(ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Text(f.stem, size=14, weight=ft.FontWeight.BOLD, color="#00FFAA" if act else "#FFFFFF"), on_click=lambda _, p=f: apply_cfg(p.read_text(encoding="utf-8", errors="ignore"), p.stem) and show_msg(f"📝 Загружен {p.stem}"), expand=True),
                    ft.Switch(value=act, active_color="#00FFAA", on_change=tog),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#FF4D6D", icon_size=20, on_click=lambda _, p=f: p.unlink(missing_ok=True) or refresh_tunnels()),
                ]),
                padding=ft.padding.symmetric(horizontal=12, vertical=4), border_radius=12, bgcolor="#CC140829",
                border=ft.border.all(1.5, "#00FFAA" if act else "#B800FF"), animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
            ))
        page.update()

    def on_gen(_):
        priv_f.value, pub_f.value = gen_wg_keys(); show_msg("🔑 Новые ключи сгенерированы!")

    def on_save(_):
        if not priv_f.value.strip(): on_gen(None)
        txt = f"# DoxaGuard | @Doxa_pubg_cfg\n[Interface]\nPrivateKey = {priv_f.value.strip()}\nAddress = {addr_f.value.strip() or '10.66.66.2/32'}\nDNS = 1.1.1.1, 1.0.0.1\nMTU = {mtu_f.value.strip() or '1280'}\n\n[Peer]\nPublicKey = {srv_f.value.strip()}\nEndpoint = {ep_f.value.strip()}\nAllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 10\n"
        prev_f.value = txt; p = save_raw(name_f.value, txt); refresh_tunnels(); show_msg(f"✅ Сохранено: {p.name}", "#00FFAA")

    def on_pick(e: ft.FilePickerResultEvent):
        if not e.files or not e.files.path: return
        p = Path(e.files.path)
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                cns = [n for n in z.namelist() if n.lower().endswith(".conf") and not n.startswith("__MACOSX")]
                for cn in cns: save_raw(Path(cn).stem, z.read(cn).decode("utf-8", errors="ignore"))
                if cns: apply_cfg(z.read(cns).decode("utf-8", errors="ignore"), Path(cns).stem); refresh_tunnels(); show_msg(f"📦 Импортировано из ZIP: {len(cns)}", "#00FFAA")
        else:
            c = p.read_text(encoding="utf-8", errors="ignore")
            if apply_cfg(c, p.stem): save_raw(p.stem, c); refresh_tunnels(); show_msg(f"📂 Импортирован: {p.stem}", "#00FFAA")

    fp = ft.FilePicker(on_result=on_pick); page.overlay.append(fp)
    qr_in = ft.TextField(label="Текст из QR-кода", multiline=True, min_lines=4, bgcolor=fbg, border_color="#B800FF")
    qr_dlg = ft.AlertDialog(title=ft.Text("📷 Вставить QR-конфиг"), content=qr_in, actions=[ft.ElevatedButton("Загрузить", on_click=lambda _: setattr(qr_dlg, "open", False) or (apply_cfg(qr_in.value or "", "DoxaGuard_QR") and save_raw("DoxaGuard_QR", qr_in.value) and refresh_tunnels()) or page.update())], bgcolor="#0A1128")
    page.overlay.append(qr_dlg)

    sheet = ft.BottomSheet(content=ft.Container(content=ft.Column([
        ft.Text("➕ ДОБАВИТЬ ТУННЕЛЬ", size=16, weight=ft.FontWeight.BOLD, color="#E066FF"),
        ft.ElevatedButton("📂 Импорт из файла или архива (.conf / .zip)", on_click=lambda _: setattr(sheet, "open", False) or page.update() or fp.pick_files(allowed_extensions=["conf", "zip", "txt"])),
        ft.ElevatedButton("📷 Сканировать / Вставить QR-код", on_click=lambda _: setattr(sheet, "open", False) or setattr(qr_dlg, "open", True) or page.update()),
        ft.ElevatedButton("✨ Создать с нуля", on_click=lambda _: setattr(sheet, "open", False) or on_gen(None) or page.update()),
    ], tight=True, spacing=10), padding=18, bgcolor="#0A1128", border=ft.border.all(2, "#FF1E56"), border_radius=ft.border_radius.only(top_left=20, top_right=20)))
    page.overlay.append(sheet)

    # --- ПЛАВНЫЕ ЭЛЕМЕНТЫ FPS UNLOCKER БЕЗ ПЕРЕРИСОВКИ ЭКРАНА ---
    hero_fps_txt = ft.Text("120 FPS", size=30, weight=ft.FontWeight.W_900, color="#00FFAA")
    apply_btn_lbl = ft.Text("» APPLY 120 FPS", weight=ft.FontWeight.BOLD, size=14, color="#FFFFFF")
    launch_btn_lbl = ft.Text("🎮 ЗАПУСТИТЬ PUBG (GLOBAL)", weight=ft.FontWeight.BOLD, size=13, color="#FFFFFF")
    shizuku_pill_txt = ft.Text("Check Shizuku", size=11, weight=ft.FontWeight.BOLD, color="#FFFFFF")
    shizuku_pill = ft.Container(content=shizuku_pill_txt, padding=10, border_radius=16, bgcolor="#FF1E56", animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT))

    ver_pills, scheme_pills, fps_marks = {}, {}, {}

    def set_ver(v):
        st["ver"] = v
        launch_btn_lbl.value = f"🎮 ЗАПУСТИТЬ PUBG ({v})"
        for k, box in ver_pills.items():
            sel = (k == v)
            box.bgcolor = "#CC1A0836" if sel else "#CC0A1128"
            box.border = ft.border.all(1.5, "#00FFAA" if sel else "#B800FF")
            box.content.controls.name = ft.Icons.RADIO_BUTTON_CHECKED if sel else ft.Icons.RADIO_BUTTON_UNCHECKED
            box.content.controls.color = "#00FFAA" if sel else "#99CCFF"
            box.content.controls.color = "#00FFAA" if sel else "#FFFFFF"
        page.update()

    def set_scheme(sc):
        st["scheme"] = sc
        for k, box in scheme_pills.items():
            sel = (k == sc)
            box.bgcolor = "#CC1A0836" if sel else "#CC0A1128"
            box.border = ft.border.all(1.5, "#00FFAA" if sel else "#B800FF")
            box.content.controls.name = ft.Icons.RADIO_BUTTON_CHECKED if sel else ft.Icons.RADIO_BUTTON_UNCHECKED
            box.content.controls.color = "#00FFAA" if sel else "#99CCFF"
            box.content.controls.color = "#00FFAA" if sel else "#FFFFFF"
        page.update()

    def update_fps_ui(val: int):
        st["fps"] = val
        hero_fps_txt.value = f"{val} FPS"
        apply_btn_lbl.value = f"» APPLY {val} FPS"
        for fval, lbl in fps_marks.items():
            lbl.color = "#00FFAA" if fval == val else "#99CCFF"
            lbl.size = 14 if fval == val else 12
        page.update()

    def on_fps_slide(e):
        idx = int(round(e.control.value))
        update_fps_ui(FPS_STEPS[idx])

    fps_slider = ft.Slider(
        min=0, max=3, divisions=3, value=2,
        active_color="#00FFAA", inactive_color="#2B0618", thumb_color="#FF1E56",
        on_change=on_fps_slide
    )

    def make_ver_pill(v):
        sel = (st["ver"] == v)
        box = ft.Container(
            content=ft.Row([ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED if sel else ft.Icons.RADIO_BUTTON_UNCHECKED, color="#00FFAA" if sel else "#99CCFF", size=18), ft.Text(v, size=12, weight=ft.FontWeight.BOLD, color="#00FFAA" if sel else "#FFFFFF")], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            padding=10, border_radius=12, bgcolor="#CC1A0836" if sel else "#CC0A1128", border=ft.border.all(1.5, "#00FFAA" if sel else "#B800FF"), expand=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT), ink=True, on_click=lambda _: set_ver(v)
        )
        ver_pills[v] = box
        return box

    def make_scheme_pill(key, label):
        sel = (st["scheme"] == key)
        box = ft.Container(
            content=ft.Row([ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED if sel else ft.Icons.RADIO_BUTTON_UNCHECKED, color="#00FFAA" if sel else "#99CCFF", size=18), ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color="#00FFAA" if sel else "#FFFFFF")], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            padding=10, border_radius=12, bgcolor="#CC1A0836" if sel else "#CC0A1128", border=ft.border.all(1.5, "#00FFAA" if sel else "#B800FF"), expand=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT), ink=True, on_click=lambda _: set_scheme(key)
        )
        scheme_pills[key] = box
        return box

    def check_shizuku(_):
        ok, out = run_shizuku_cmd("id")
        st["shizuku"] = ok
        shizuku_pill.bgcolor = "#00FFAA" if ok else "#FF1E56"
        shizuku_pill_txt.value = "Shizuku Mode" if ok else "Check Shizuku"
        shizuku_pill_txt.color = "#060E22" if ok else "#FFFFFF"
        fps_log.value = f"🟢 Shizuku активен ({out})" if ok else f"🔴 {out}"
        fps_log.color = "#00FFAA" if ok else "#FF4D6D"
        page.update()

    shizuku_pill.on_click = check_shizuku

    def on_apply_fps(_):
        ok, msg = process_fps_unlock(PUBG_PACKAGES[st["ver"]], st["fps"], st["scheme"])
        fps_log.value, fps_log.color = msg, "#00FFAA" if ok else "#FF4D6D"; page.update()

    def bg_wrap(c):
        return ft.Stack([ft.Image(src="bg.png", fit=ft.ImageFit.COVER, width=1080, height=2400, opacity=0.92), ft.Container(content=c, padding=14, gradient=ft.LinearGradient(begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=["#44040B1C", "#AA040B1C"]), expand=True)], expand=True)
    def open_main():
        page.clean()
        fab = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor="#FF1E56", foreground_color="#FFFFFF", shape=ft.CircleBorder(), on_click=lambda _: setattr(sheet, "open", True) or page.update())
        page.floating_action_button = fab

        for fval in FPS_STEPS:
            fps_marks[fval] = ft.Text(f"{fval} FPS", size=14 if fval == 120 else 12, weight=ft.FontWeight.BOLD, color="#00FFAA" if fval == 120 else "#99CCFF")

        vpn_view = ft.Column([
            ft.Container(content=ft.Column([ft.Row([ft.Text("⚡ МОИ ТУННЕЛИ", size=13, weight=ft.FontWeight.BOLD), status_badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), tunnels_col], spacing=8), padding=12, border_radius=14, bgcolor="#CC0A1128", border=ft.border.all(2, "#B800FF")),
            ft.Row([neon_btn("🔑 Ключи", on_gen, "#B800FF", "#9D00FF", "#CC1D0836", expand=True), neon_btn("⚡ Собрать VPN", on_save, "#FF1E56", "#FF0044", "#CC2B0618", expand=True)], spacing=10),
            priv_f, pub_f, srv_f, ep_f, ft.Row([addr_f, mtu_f], spacing=10), name_f, prev_f,
            ft.Container(content=log_text, bgcolor="#CC0A0F24", padding=12, border_radius=12, border=ft.border.all(1.5, "#FF1E56")),
            ft.Container(height=60)
        ], spacing=10, visible=True)

        fps_view = ft.Column([
            ft.Container(content=ft.Row([
                ft.Column([hero_fps_txt, ft.Text(f"📱 {dev_model}", size=12, color="#E066FF"), ft.Text("📦 game_patch_4.7.0 + Active.sav", size=11, color="#00FFAA")], spacing=4, expand=True),
                shizuku_pill
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=14, border_radius=16, bgcolor="#CC0A1128", border=ft.border.all(2, "#B800FF")),
            ft.Text("Select Game Version", size=13, weight=ft.FontWeight.BOLD, color="#99CCFF"),
            ft.Row([make_ver_pill("GLOBAL"), make_ver_pill("INDIAN")], spacing=8),
            ft.Row([make_ver_pill("KOREA"), make_ver_pill("VIETNAM")], spacing=8),
            ft.Text("Проведите ползунок вправо для выбора FPS", size=13, weight=ft.FontWeight.BOLD, color="#99CCFF"),
            ft.Container(
                content=ft.Column([
                    fps_slider,
                    ft.Row([fps_marks, fps_marks, fps_marks, fps_marks], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=2),
                padding=ft.padding.symmetric(horizontal=12, vertical=8), border_radius=14, bgcolor="#CC0A1128", border=ft.border.all(1.5, "#FF1E56")
            ),
            ft.Text("Select Files Scheme", size=13, weight=ft.FontWeight.BOLD, color="#99CCFF"),
            ft.Row([make_scheme_pill("Apply", "📂 Apply (Shizuku)"), make_scheme_pill("Save", "💾 Save")], spacing=8),
            ft.Container(content=ft.ElevatedButton(content=apply_btn_lbl, on_click=on_apply_fps, bgcolor="transparent", style=ft.ButtonStyle(shadow_color="transparent", elevation=0)), bgcolor="#CC0A2E24", border=ft.border.all(2, "#00FFAA"), border_radius=12, shadow=[ft.BoxShadow(blur_radius=14, color="#00CC88")], alignment=ft.alignment.center, ink=True),
            ft.Container(content=ft.ElevatedButton(content=launch_btn_lbl, on_click=lambda _: run_shizuku_cmd(f"monkey -p {PUBG_PACKAGES[st['ver']]} -c android.intent.category.LAUNCHER 1"), bgcolor="transparent", style=ft.ButtonStyle(shadow_color="transparent", elevation=0)), bgcolor="#CC2B0618", border=ft.border.all(2, "#FF1E56"), border_radius=12, shadow=[ft.BoxShadow(blur_radius=14, color="#FF0044")], alignment=ft.alignment.center, ink=True),
            ft.Container(content=fps_log, bgcolor="#CC0A0F24", padding=12, border_radius=12, border=ft.border.all(1.5, "#00FFAA"))
        ], spacing=10, visible=False)

        tab0_btn = ft.Container(content=ft.Text("🛡 VPN ТУННЕЛИ", size=12, weight=ft.FontWeight.BOLD, color="#00FFAA"), padding=10, alignment=ft.alignment.center, border_radius=10, bgcolor="#CC1D0836", border=ft.border.all(1.5, "#00FFAA"), expand=True, animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT), ink=True)
        tab1_btn = ft.Container(content=ft.Text("🚀 FPS UNLOCKER", size=12, weight=ft.FontWeight.BOLD, color="#FFFFFF"), padding=10, alignment=ft.alignment.center, border_radius=10, bgcolor="transparent", border=ft.border.all(1.5, "#44FFFFFF"), expand=True, animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT), ink=True)

        def switch_tab(idx):
            is_v = (idx == 0)
            vpn_view.visible, fps_view.visible = is_v, not is_v
            fab.visible = is_v
            tab0_btn.bgcolor = "#CC1D0836" if is_v else "transparent"
            tab0_btn.border = ft.border.all(1.5, "#00FFAA" if is_v else "#44FFFFFF")
            tab0_btn.content.color = "#00FFAA" if is_v else "#FFFFFF"
            tab1_btn.bgcolor = "#CC1D0836" if not is_v else "transparent"
            tab1_btn.border = ft.border.all(1.5, "#00FFAA" if not is_v else "#44FFFFFF")
            tab1_btn.content.color = "#00FFAA" if not is_v else "#FFFFFF"
            page.update()

        tab0_btn.on_click = lambda _: switch_tab(0)
        tab1_btn.on_click = lambda _: switch_tab(1)

        nav = ft.Container(content=ft.Row([tab0_btn, tab1_btn], spacing=8), padding=6, border_radius=14, bgcolor="#CC0A1128", border=ft.border.all(1.5, "#B800FF"))
        header = ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD v4.0 PRO • @Doxa_pubg_cfg", size=12, weight=ft.FontWeight.BOLD, color="#99CCFF")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

        page.add(bg_wrap(ft.Container(content=ft.Column([header, nav, vpn_view, fps_view], spacing=10, scroll=ft.ScrollMode.AUTO), padding=16, border_radius=18, bgcolor="#55060D21", border=ft.border.all(2, "#FF1E56"), expand=True)))
        on_gen(None); refresh_tunnels()

    pwd_in = ft.TextField(label="Введите пароль доступа", password=True, can_reveal_password=True, bgcolor=fbg, border_color=rneon)
    err_t = ft.Text("", color="#FF4D6D", size=12)
    card = ft.Container(content=ft.Column([neon_title("DOXACHKAA", 34), ft.Text("DOXAGUARD v4.0 PRO • @Doxa_pubg_cfg", size=12, color="#B8DCFF"), pwd_in, neon_btn("ВОЙТИ В DOXAGUARD", lambda _: open_main() if pwd_in.value.strip() == APP_PWD else setattr(err_t, "value", "❌ Неверный пароль!") or page.update(), width=260), err_t], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14), padding=24, margin=ft.margin.only(top=70), bgcolor="#B3070E24", border_radius=20, border=ft.border.all(2.5, "#FF1E56"))
    page.add(bg_wrap(card))

ft.app(target=main, assets_dir="assets")
