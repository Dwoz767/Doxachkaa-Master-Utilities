import json, math, random, time
from pathlib import Path
import flet as ft

DB_PATH = Path("/storage/emulated/0/Download/doxachkaauc_data.json")
ADMIN_PWD = "Doxachka2001"

SECTORS = (0, 60, 120, 325, 385, 660, 1320, 1800, 2460, 3850, 5650, 8100, 11950, 16200, 24300, 32400, 40500, 81000)
WEIGHTS = (38.0, 32.0, 13.0, 7.5, 3.8, 2.2, 1.3, 0.8, 0.5, 0.3, 0.2, 0.15, 0.1, 0.06, 0.04, 0.025, 0.015, 0.01)
RANKS = {0: "Игрок", 1: "Мл. Модер", 2: "Модер", 3: "Ст. Модер", 4: "Мл. Админ", 5: "Админ", 6: "Ст. Админ", 7: "Зам. Основателя", 8: "Основатель"}

def load_db():
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "next_id": 2, "cur_id": 1,
        "users": {"1": {"id": 1, "uc": 1000, "rub": 0, "rank": 8, "ban": False}},
        "logs": ["[SYSTEM] ID 1 — Основатель (8 ранг)."]
    }

def save_db(db):
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def main(page: ft.Page):
    page.title = "DoxachkaaUC"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#070B19"
    page.padding = 0

    db = load_db()
    st = {"spin": False, "ang": 0.0, "adm": False}
    online = random.randint(160, 350)

    def get_u(uid=None):
        k = str(uid if uid is not None else db["cur_id"])
        if k not in db["users"]:
            n = int(k)
            db["users"][k] = {"id": n, "uc": 120, "rub": 0, "rank": 0, "ban": False}
            if n >= db["next_id"]:
                db["next_id"] = min(100000000, n + 1)
            save_db(db)
        return db["users"][k]

    def log_act(msg):
        db["logs"].insert(0, f"[{time.strftime('%H:%M:%S')}] {msg}")
        del db["logs"][60:]
        save_db(db)

    hdr_txt = ft.Text("", size=12, color="#99CCFF")
    bal_txt = ft.Text("", size=22, weight=ft.FontWeight.BOLD, color="#FFD166")
    res_txt = ft.Text("Жми КРУТИТЬ КОЛЕСО!", size=15, weight=ft.FontWeight.BOLD, color="#E066FF")
    whl_val = ft.Text("0 UC", size=30, weight=ft.FontWeight.W_900, color="#FFFFFF")
    log_txt = ft.Text("", size=11, color="#D8E2FF", selectable=True)

    wheel = ft.Container(
        content=ft.Column([
            ft.Text("👑 DOXACHKAA UC", size=12, weight=ft.FontWeight.BOLD, color="#E066FF"),
            whl_val,
            ft.Text("0 — 81000 UC", size=10, color="#99CCFF"),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        width=210, height=210, border_radius=105, bgcolor="#CC11092B",
        border=ft.border.all(4, "#FF1E56"),
        shadow=[ft.BoxShadow(blur_radius=24, spread_radius=2, color="#B800FF")],
        rotate=ft.Rotate(angle=0, alignment=ft.alignment.center),
        animate_rotation=ft.Animation(1800, ft.AnimationCurve.DECELERATE),
        alignment=ft.alignment.center,
    )

    def upd():
        u = get_u()
        b_s = " 🚫 [BAN]" if u["ban"] else ""
        hdr_txt.value = f"ID: {u['id']} | {RANKS.get(u['rank'], 'Игрок')} ({u['rank']}) | Онлайн: 🟢 {online}{b_s}"
        bal_txt.value = f"💰 {u['uc']} UC  |  💳 {u['rub']} ₽"
        log_txt.value = "\n".join(db["logs"])
        page.update()

    def spin(_):
        u = get_u()
        if u["ban"]:
            res_txt.value, res_txt.color = "🚫 Вы заблокированы!", "#FF4D6D"
            page.update()
            return
        if st["spin"] or u["uc"] < 60:
            if u["uc"] < 60:
                res_txt.value, res_txt.color = "❌ Недостаточно UC (нужно 60)!", "#FF4D6D"
                page.update()
            return
        st["spin"] = True
        u["uc"] -= 60
        win = next(iter(random.choices(SECTORS, weights=WEIGHTS, k=1)))
        st["ang"] += math.pi * 8 + random.uniform(0.5, 5.5)
        wheel.rotate.angle = st["ang"]
        whl_val.value = "🎰 ..."
        res_txt.value, res_txt.color = "🎡 Вращается...", "#99CCFF"
        upd()
        time.sleep(1.85)
        u["uc"] += win
        whl_val.value = f"{win} UC"
        res_txt.value = f"🎉 Выигрыш: {win} UC!" if win > 0 else "💨 Выпало 0 UC!"
        res_txt.color = "#00FFAA" if win >= 3850 else ("#E066FF" if win > 0 else "#FF7373")
        log_act(f"ID {u['id']} крутил (-60 UC) -> {win} UC")
        st["spin"] = False
        upd()

    def reg_id(_):
        nid = db["next_id"]
        if nid <= 100000000:
            db["cur_id"] = nid
            db["next_id"] = nid + 1
            get_u(nid)
            log_act(f"Создан игрок ID {nid}")
            upd()

    sw_in = ft.TextField(label="ID (1..100000000)", width=165, text_size=12, border_color="#B800FF")
    def go_sw(_):
        v = sw_in.value.strip()
        if v.isdigit() and 1 <= int(v) <= 100000000:
            db["cur_id"] = int(v)
            get_u(db["cur_id"])
            upd()

    cmd_in = ft.TextField(label="Команда (/Money, /Unmoney, /Ban, /Unban, /Makeadmins, /UnmakeAdmins)", border_color="#FF1E56", text_size=12)
    qid_in = ft.TextField(label="ID", value="1", width=95, border_color="#FF1E56", text_size=12)
    qamt_in = ft.TextField(label="Сумма", value="1000", width=115, border_color="#FF1E56", text_size=12)

    def run_cmd(raw):
        act = get_u()
        if act["rank"] < 1 and not st["adm"]:
            log_act(f"Отказ прав для ID {act['id']}")
            upd()
            return
        pts = raw.strip().split()
        if not pts:
            return
        it = iter(pts)
        c = next(it).lower()
        nums = [p.replace("₽", "").replace("uc", "") for p in it if p.lower() != "id" and p.replace("₽", "").replace("uc", "").isdigit()]
        try:
            if c == "/money" and len(nums) >= 2:
                ni = iter(nums)
                tid, amt = int(next(ni)), int(next(ni))
                tu = get_u(tid)
                if "₽" in raw:
                    tu["rub"] += amt
                tu["uc"] += amt
                log_act(f"ID {act['id']} пополнил ID {tid} на {amt}{'₽' if '₽' in raw else ' UC'}")
            elif c == "/unmoney" and len(nums) >= 1:
                ni = iter(nums)
                tid = int(next(ni))
                amt = int(next(ni, get_u(tid)["uc"]))
                get_u(tid)["uc"] = max(0, get_u(tid)["uc"] - amt)
                log_act(f"ID {act['id']} снял {amt} UC у ID {tid}")
            elif c == "/ban" and len(nums) >= 1:
                tid = int(next(iter(nums)))
                get_u(tid)["ban"] = True
                log_act(f"ID {act['id']} забанил ID {tid}")
            elif c == "/unban" and len(nums) >= 1:
                tid = int(next(iter(nums)))
                get_u(tid)["ban"] = False
                log_act(f"ID {act['id']} разбанил ID {tid}")
            elif c == "/makeadmins" and len(nums) >= 1:
                ni = iter(nums)
                tid = int(next(ni))
                rnk = max(1, min(8, int(next(ni, 1))))
                get_u(tid)["rank"] = rnk
                log_act(f"ID {act['id']} выдал ID {tid} админа {rnk} ранга ({RANKS[rnk]})")
            elif c == "/unmakeadmins" and len(nums) >= 1:
                tid = int(next(iter(nums)))
                get_u(tid)["rank"] = 0
                log_act(f"ID {act['id']} снял админа с ID {tid}")
            else:
                log_act(f"Ошибка формата: {raw}")
        except Exception as e:
            log_act(f"Сбой: {e}")
        save_db(db)
        upd()

    apwd_in = ft.TextField(label="Пароль Админки", password=True, can_reveal_password=True, width=185, border_color="#FF1E56", text_size=12)
    abox = ft.Column(visible=False, spacing=10)
    def open_adm(_):
        if apwd_in.value.strip() == ADMIN_PWD or get_u()["rank"] >= 1:
            st["adm"] = True
            abox.visible = True
            upd()

    abox.controls = [
        ft.Text("🛡️ АДМИН-ПАНЕЛЬ (1–8 РАНГ)", size=14, weight=ft.FontWeight.BOLD, color="#FF1E56"),
        ft.Row([qid_in, qamt_in, ft.ElevatedButton("💳 Пополнить", on_click=lambda _: run_cmd(f"/Money id {qid_in.value} {qamt_in.value}₽"), bgcolor="#FF1E56", color="#FFFFFF")], wrap=True),
        cmd_in,
        ft.ElevatedButton("▶ Выполнить", on_click=lambda _: run_cmd(cmd_in.value), bgcolor="#8A00E6", color="#FFFFFF"),
        ft.Container(content=log_txt, padding=10, bgcolor="#CC090D1F", border_radius=10, border=ft.border.all(1, "#B800FF"))
    ]

    body = ft.Column([
        ft.Text("DOXACHKAA UC", size=30, weight=ft.FontWeight.W_900, color="#E066FF", style=ft.TextStyle(shadow=[ft.BoxShadow(blur_radius=14, color="#B800FF")])),
        hdr_txt, bal_txt,
        ft.Row([ft.ElevatedButton("➕ Новый ID", on_click=reg_id), sw_in, ft.ElevatedButton("OK", on_click=go_sw)], wrap=True),
        ft.Container(content=wheel, alignment=ft.alignment.center, padding=10),
        ft.Container(content=ft.ElevatedButton("🎡 КРУТИТЬ КОЛЕСО (60 UC)", on_click=spin, bgcolor="#FF1E56", color="#FFFFFF", width=260, height=46), alignment=ft.alignment.center),
        ft.Container(content=res_txt, alignment=ft.alignment.center),
        ft.Row([apwd_in, ft.ElevatedButton("🔐 Админка", on_click=open_adm, bgcolor="#B800FF", color="#FFFFFF")]),
        abox,
    ], spacing=10, scroll=ft.ScrollMode.AUTO)

    layers = [ft.Container(content=body, padding=16, expand=True)]
    if Path("assets/bg.png").exists():
        layers.insert(0, ft.Image(src="bg.png", fit=ft.ImageFit.COVER, width=1080, height=2400, opacity=0.35))
    page.add(ft.Stack(layers, expand=True))
    upd()

ft.app(target=main, assets_dir="assets")
