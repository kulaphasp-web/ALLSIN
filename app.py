# =====================================================================
# ALLSIN  -  นายวิทยุถอดรหัสสัญญาณผสมจากอวกาศ
#
# โครงสร้างตามเอกสาร Streamlit:  INPUT -> CALCULATION -> OUTPUT
#
# ทำไมบอร์ดเกมจึงเป็น HTML/JavaScript?
#   widget ของ Streamlit ทุกตัวสั่งให้เซิร์ฟเวอร์รันสคริปต์ใหม่ทั้งไฟล์ จึงมีหน่วงและกะพริบ
#   เมื่อหมุนลูกบิด เพื่อให้ปรับค่าแล้วเห็นผลทันที (real-time) บอร์ดเกมจึงทำงานในเบราว์เซอร์
#   ส่วน Streamlit ทำหน้าที่: สุ่มโจทย์ด้วย Python, ปุ่มเริ่มเกม, หน้าเว็บ และการ deploy
#
#   ส่วนที่ 1  Python : make_game()   สุ่มสัญญาณผสม คำใบ้ และคำใบ้เพิ่ม
#   ส่วนที่ 2  Python : หน้าเว็บ + ปุ่มเริ่มเกม ส่งโจทย์ให้บอร์ด + เก็บคะแนนรวม
#   ส่วนที่ 3  JS     : BOARD_HTML    ลูกบิด (INPUT) -> รวมคลื่น/ตรวจคำตอบ/ให้คะแนน (CALCULATION)
#                                      -> จอใหญ่/จอเล็ก/หน้าสรุปผล (OUTPUT)
#
# กติกาการส่งตรวจและคะแนน (ค่าคงที่ FULL_SCORE, ATTEMPT_PENALTY, HINT_COST ด้านล่าง ปรับตัวเลขได้ที่นั่น):
#   - คะแนนเต็มของเกมขึ้นกับจำนวนกราฟที่ต้องตอบ: 2 กราฟ = 10, 3 = 12, 4 = 14, 5 = 14, 6 = 16
#   - ส่งตรวจได้สูงสุด 3 ครั้ง ถูกหมดครั้งที่ 1 ได้ เต็ม − คำใบ้ / ครั้งที่ 2 ได้ เต็ม − 2 − คำใบ้ / ครั้งที่ 3 ได้ เต็ม − 4 − คำใบ้
#   - หลังส่งแล้วยังผิด ค่าไหนตรงเฉลยจะถูกล็อกทันที (ลูกบิดสีเขียว ✓) เล่นต่อได้
#   - ขอคำใบ้เพิ่มได้เท่ากับจำนวนกราฟ (hints_allowed) ครั้งละ 1 ค่า และหัก 1 คะแนนต่อครั้ง
#   - ชนะ: คะแนนรวมสะสมต่อเกมถัดไป  /  แพ้ (ส่งครบ 3 ครั้งไม่ถูก หรือหมดเวลา): คะแนนรวมรีเซ็ตเป็น 0 แต่เก็บคะแนนสูงสุดไว้
#     และสรุปผล + เฉลย + ปุ่มเริ่มเกมใหม่ / SANDBOX
#   - จับเวลาถอยหลัง: 2 นาที (2 กราฟ) + 1 นาทีต่อกราฟที่เพิ่ม สูงสุด +4 นาที (TIME_* ด้านล่าง)
#     เวลาไม่มีผลต่อคะแนน แต่หมดเวลาเกมจบทันที (นับเป็นแพ้)
#   - ปุ่ม SANDBOX ที่แถบด้านซ้ายถูกล็อกตั้งแต่เริ่มเกมจนเกมจบ
#   - ด่าน: เริ่มที่ด่าน 1 มีกราฟผสม 2 กราฟ ผ่านครบทุก 3 ด่านเพิ่มอีก 1 กราฟ (สูงสุด 6) ชนะ = ไปด่านถัดไป แพ้ = กลับด่าน 1
#   - ระดับความยาก (แถบเลื่อนด้านซ้าย): เลือกได้ก่อนกดเริ่มเกมเท่านั้น พอกดเริ่มแล้วจะล็อกตลอดทุกด่านของรอบนั้น
#     จนกว่าเกมจะจบ (แพ้/หมดเวลา) จึงเลือกใหม่ได้ (session_state: run_active / run_level)
#       นักเรียน (ง่าย) ไม่จับเวลา + มีปุ่มคำใบ้ / นิสิต (ปานกลาง) จับเวลา + มีปุ่มคำใบ้ / อาจารย์ (ยาก) จับเวลา + ไม่มีปุ่มคำใบ้
#   - เวลาลดลงตั้งแต่ด่าน 16: ด่านละ 10 วินาที (TIME_SHRINK_*) จนเหลือ 3 นาที แล้วคงที่ (เฉพาะระดับที่จับเวลา)
#     ก่อนเข้าด่าน 16 มีหน้าแจ้งเตือนให้กดรับทราบ 1 ครั้งต่อรอบ (ด่านถัดไปไม่แจ้งซ้ำ) -> show_shrink_notice()
#   - ปุ่มในหน้าสรุปอยู่ในบอร์ด (iframe) จึงส่งคำสั่งกลับมาหา Python ผ่าน Streamlit custom component
#   ส่วนเสริม  JS     : SANDBOX_HTML  กดปุ่ม 🧪 SANDBOX ด้านซ้ายแล้วจอหลัก (จอใหญ่) จะเปลี่ยนเป็น
#                                      เครื่องสังเคราะห์อนุกรมฟูเรียร์ ปรับพารามิเตอร์ของสูตร
#                                      f(x) = a0 + Σ_{n=1..6} ( a_n cos(n·x) + b_n sin(n·x) )
#                                        a0       ยกกราฟทั้งหมดขึ้น/ลง (ในเกมเท่ากับ 0 เสมอ)
#                                        n        ความถี่ของแต่ละเทอม (เกมผสมได้สูงสุด 6 กราฟ จึงใช้ n = 1..6)
#                                        a_n,b_n  ตัวกำหนดเฟสของเทอมนั้น: a cosθ + b sinθ = R·sin(θ + φ)
#                                      x วัดเป็นเรเดียน (ถ้าวัด x เป็นจำนวนคาบ t = x/2π จะได้ cos(2πnt) ตามสูตรเดิม)
#                                      (บอร์ดเกมกับ SANDBOX อยู่บนหน้าเดียวกัน สลับดูได้โดยเกมไม่หาย)
#
# ขอบเขตของจอใหญ่ (เกมและ SANDBOX) คงที่เสมอ: x = 0 ถึง 4π เรเดียน, y = −20 ถึง 20
# (ค่าคงที่ X_MAX / Y_LIM อยู่ต้นสคริปต์ของ JavaScript ทั้งสองส่วน)
#
# รัน:  python -m streamlit run app.py
# =====================================================================

import json
import random

import numpy as np
import streamlit as st

# ---------------------------------------------------------------------
# ค่าคงที่ของเกม
# ---------------------------------------------------------------------
N_SCREENS = 6                       # จำนวนจอเล็กทั้งหมด
KNOBS = ("amp", "freq", "phase")    # ลูกบิด 3 ลูกของแต่ละจอ
PHASES = [0, 90, 180, 270]          # ค่าเฟสที่ปรับได้ (องศา)
FULL_SCORE = {2: 10, 3: 12, 4: 14, 5: 14, 6: 16}   # คะแนนเต็มของเกม ขึ้นกับจำนวนกราฟที่ต้องตอบ
ATTEMPT_PENALTY = [0, 2, 4]         # คะแนนที่หักเมื่อส่งถูกหมดในครั้งที่ 1, 2, 3
MAX_ATTEMPTS = len(ATTEMPT_PENALTY)  # ส่งตรวจได้สูงสุด 3 ครั้งต่อเกม
HINT_COST = 1                       # ขอคำใบ้เพิ่ม 1 ครั้ง หัก 1 คะแนน
TIME_BASE = 120                     # เวลาพื้นฐาน 2 นาที (วินาที) สำหรับ 2 กราฟ
TIME_PER_EXTRA_GRAPH = 60           # เพิ่มอีก 1 นาทีต่อกราฟที่ต้องตอบเพิ่ม (นับจาก 2 กราฟ)
TIME_MAX_EXTRA = 240                # เพิ่มได้สูงสุด 4 นาที (6 กราฟ = 6 นาที)
TIME_SHRINK_FROM = 16               # ตั้งแต่ด่าน 16 เวลาของด่านเริ่มลดลง (ผ่านครบ 15 ด่านแล้ว)
TIME_SHRINK_PER_STAGE = 10          # ลดลง 10 วินาที ต่อ 1 ด่าน (ด่าน 16 = −10, ด่าน 17 = −20, ...)
TIME_SHRINK_FLOOR = 180             # ลดได้จนเหลือ 3 นาที แล้วคงที่ (6 กราฟ 6 นาที จึงลดได้สูงสุด 3 นาที)
MIN_GRAPHS = 2                     # ด่านแรกมีกราฟผสม 2 กราฟ
MAX_GRAPHS = N_SCREENS              # มากสุด 6 กราฟ (จอเล็กมี 6 จอ)
STAGES_PER_GRAPH = 3                # ผ่านครบทุก 3 ด่าน เพิ่มกราฟผสม +1 กราฟ
# ระดับความยาก (เรียงจากง่ายไปยาก) เลือกด้วยแถบเลื่อนที่แถบด้านซ้าย
DIFFICULTIES = [
    {"label": "นักเรียน (ง่าย)", "timer": False, "hints": True},        # ไม่จับเวลา + มีปุ่มคำใบ้
    {"label": "นิสิต (ปานกลาง)", "timer": True, "hints": True},         # จับเวลา + มีปุ่มคำใบ้
    {"label": "อาจารย์ (ยาก)", "timer": True, "hints": False},         # จับเวลา + ไม่มีปุ่มคำใบ้
]
DEFAULT_LEVEL = 1                   # เริ่มต้นที่ระดับ นิสิต (ปานกลาง)
BOARD_HEIGHT = 900                  # ความสูงของบอร์ดเกม (px)
SANDBOX_HEIGHT = 840                # ความสูงของ SANDBOX บนจอหลัก (px)
TOL = 1e-6
X = np.linspace(0, 4 * np.pi, 721)  # แกน x ของทุกกราฟ: 0 ถึง 4π เรเดียน (2 คาบของ n = 1)


# =====================================================================
# ส่วนที่ 1: สุ่มโจทย์ (Python)
# =====================================================================
def time_limit(n_graphs, stage=1):
    """เวลาของเกม (วินาที) = 2 นาที + 1 นาทีต่อกราฟที่เพิ่มจาก 2 กราฟ แต่เพิ่มไม่เกิน 4 นาที
    แล้วตั้งแต่ด่าน TIME_SHRINK_FROM (16) หักออกด่านละ 10 วินาที (ด่าน 16 = −10, ด่าน 17 = −20, ...)
    จนเหลือ TIME_SHRINK_FLOOR (3 นาที) แล้วคงที่ที่นั้น  (ด่านก่อนหน้านั้นไม่ถูกหัก)"""
    full = TIME_BASE + min(TIME_MAX_EXTRA, TIME_PER_EXTRA_GRAPH * max(0, n_graphs - 2))
    cut = TIME_SHRINK_PER_STAGE * max(0, stage - TIME_SHRINK_FROM + 1)
    return max(min(full, TIME_SHRINK_FLOOR), full - cut)       # ไม่ต่ำกว่า 3 นาที (และไม่เกินเวลาเต็ม)


def shrink_end_stage():
    """ด่านแรกที่เวลาลดลงจนถึงขีดต่ำสุดแล้ว (6 กราฟ: 6 นาที ลดด่านละ 10 วินาที จนเหลือ 3 นาที = ด่าน 33)"""
    stage = TIME_SHRINK_FROM
    while time_limit(MAX_GRAPHS, stage) > TIME_SHRINK_FLOOR:
        stage += 1
    return stage


def fmt_time(sec):
    """วินาที -> ข้อความไทย เช่น 350 -> '5 นาที 50 วินาที', 180 -> '3 นาที'"""
    m, r = divmod(sec, 60)
    return "%d นาที" % m + (" %d วินาที" % r if r else "")


def graphs_for_stage(stage):
    """จำนวนกราฟผสมของด่านนั้น: ด่าน 1-3 = 2 กราฟ, 4-6 = 3, 7-9 = 4, 10-12 = 5, ด่าน 13 ขึ้นไป = 6 (สูงสุด)"""
    return min(MAX_GRAPHS, MIN_GRAPHS + (max(1, stage) - 1) // STAGES_PER_GRAPH)


def level_index(label):
    """ชื่อระดับความยาก (ข้อความบนแถบเลื่อน) -> ลำดับใน DIFFICULTIES (ไม่รู้จัก = ค่าเริ่มต้น)"""
    for i, d in enumerate(DIFFICULTIES):
        if d["label"] == label:
            return i
    return DEFAULT_LEVEL


def hints_allowed(n_graphs):
    """จำนวนครั้งที่ขอคำใบ้เพิ่มได้ในเกมนั้น = จำนวนกราฟที่ต้องตอบ (กราฟมากขึ้น ค่าที่ต้องหาก็มากขึ้น)"""
    return n_graphs


def wave(amp, freq, phase):
    """กราฟ sin หนึ่งจอ:  y = A * sin(f * x + phase)   (f ตรงกับ n ในอนุกรมฟูเรียร์)"""
    return amp * np.sin(freq * X + np.radians(phase))


def make_game(game_id, n=None, hint_button=True):
    """สุ่มสัญญาณผสม 1 สัญญาณ (n กราฟ; ไม่ระบุ = สุ่ม 2-6) พร้อมคำใบ้เริ่มต้นและคำใบ้เพิ่ม
    hint_button=False (ระดับอาจารย์) = ไม่มีปุ่มคำใบ้เพิ่ม คงเหลือเฉพาะคำใบ้เริ่มต้นจากผู้ดูแล

    หลักการ: sin(fx+φ) ที่ φ = 0/90/180/270 ให้ได้เพียง ±A·sin(kx) หรือ ±A·cos(kx)
    โดย k = |f| = 1, 2, 3 จึงมี "ช่อง" ที่ไม่ซ้ำกันอยู่ 6 ช่อง
    (sin1, cos1, sin2, cos2, sin3, cos3) แต่ละกราฟที่ซ่อนอยู่จะใช้คนละช่อง
    ผลคือสัญญาณผสมแยกเป็นกราฟ sin ได้แบบเดียวเท่านั้น (ตรงกับอนุกรมฟูเรียร์)
    """
    rng = random.Random()
    if n is None:
        n = rng.randint(MIN_GRAPHS, MAX_GRAPHS)

    slots = [(k, kind) for k in (1, 2, 3) for kind in ("sin", "cos")]
    components = []
    for k, kind in rng.sample(slots, n):
        c = rng.choice([-3, -2, -1, 1, 2, 3])
        base = c * (np.sin(k * X) if kind == "sin" else np.cos(k * X))
        # ชุดค่า (A, f, φ) ทั้งหมดที่ให้กราฟเดียวกับ base แล้วสุ่มมาหนึ่งชุด
        options = [
            {"amp": a, "freq": f, "phase": p}
            for a in range(-3, 4) if a != 0
            for f in range(-3, 4) if f != 0
            for p in PHASES
            if np.allclose(wave(a, f, p), base, atol=TOL)
        ]
        components.append(rng.choice(options))

    # คำใบ้เริ่มต้น: ผู้ดูแลให้ค่าที่ถูกต้องแบบสุ่ม จอละ 0-2 ค่า (ไม่เกิน 2)
    hints = [rng.sample(KNOBS, rng.choice([0, 1, 1, 2, 2])) for _ in components]
    if not any(hints):                      # อย่างน้อยให้คำใบ้ 1 ค่า
        hints[0] = [rng.choice(KNOBS)]

    # คำใบ้เพิ่ม: สุ่มจากค่าที่ผู้ดูแลยังไม่ได้บอก (กดครั้งละ 1 ค่า จำนวนครั้งเท่ากับจำนวนกราฟ)
    # แต่ละจอถูกบอกไม่เกิน 2 ค่า จึงเหลือค่าที่ซ่อนอย่างน้อย n ค่าเสมอ (จอละ 1 ค่าขึ้นไป)
    hidden = [(i, k) for i in range(n) for k in KNOBS if k not in hints[i]]
    bonus = [list(p) for p in rng.sample(hidden, min(hints_allowed(n), len(hidden)))] if hint_button else []

    return {"id": game_id, "components": components, "hints": hints, "bonus": bonus}


def run_locked():
    """True ตั้งแต่กดเริ่มเกมจนกว่าเกมจะจบ (แพ้/หมดเวลา) — ระหว่างนี้เปลี่ยนระดับความยากไม่ได้ แม้จะผ่านด่านไปแล้วก็ตาม
    (ถ้าบอร์ดรายงานผลกลับมาไม่ได้ เช่นใช้ HTML ฝังตรง ๆ จะไม่ล็อก เพราะไม่รู้ว่าเกมจบเมื่อไร)"""
    return BOARD_COMPONENT is not None and bool(st.session_state.get("run_active"))


def current_level():
    """ลำดับระดับความยากที่ใช้อยู่: ระหว่างรอบใช้ระดับที่ล็อกไว้ ไม่งั้นใช้ค่าบนแถบเลื่อน"""
    ss = st.session_state
    return ss.get("run_level", DEFAULT_LEVEL) if run_locked() else level_index(ss.get("difficulty"))


def needs_shrink_warning(stage, level):
    """ต้องแจ้งเตือนก่อนเริ่มด่านนี้ไหม: ด่าน 16 ขึ้นไป + ระดับที่จับเวลา + ยังไม่เคยแจ้งในรอบนี้"""
    return (stage >= TIME_SHRINK_FROM and DIFFICULTIES[level]["timer"]
            and not st.session_state.get("shrink_warned"))


def new_game():
    """เริ่มเกม (ด่าน) ใหม่: จำนวนกราฟตามด่านปัจจุบัน และระดับความยากของรอบนี้
    เริ่มรอบใหม่ (ยังไม่ล็อก) = อ่านระดับจากแถบเลื่อนแล้วล็อกไว้ ผ่านด่านต่อไปก็ใช้ระดับเดิมจนเกมจบ"""
    ss = st.session_state
    ss["game_counter"] = ss.get("game_counter", 0) + 1
    stage = ss.get("stage", 1)
    level = current_level()
    ss["run_level"] = level
    ss["run_active"] = True
    ss["shrink_notice"] = False
    game = make_game(ss["game_counter"], n=graphs_for_stage(stage), hint_button=DIFFICULTIES[level]["hints"])
    game["stage"] = stage
    game["difficulty"] = level
    game["base_total"] = st.session_state.get("total_score", 0)    # คะแนนรวมก่อนเริ่มเกมนี้
    game["base_high"] = st.session_state.get("high_score", 0)      # คะแนนสูงสุดก่อนเริ่มเกมนี้
    st.session_state["game"] = game
    st.session_state["mode"] = "game"       # เริ่มเกมใหม่แล้วกลับมาที่หน้าเกมเสมอ


def request_start():
    """ปุ่มเริ่มเกม / ด่านถัดไป ทุกปุ่มมาที่นี่: ปกติเริ่มเกมเลย แต่ก่อนเข้าด่าน 16 (ระดับที่จับเวลา)
    ให้แสดงหน้าแจ้งเตือนเรื่องเวลาที่จะลดลงก่อน แล้วรอผู้เล่นกดรับทราบ (ดู ack_shrink_notice)"""
    ss = st.session_state
    if needs_shrink_warning(ss.get("stage", 1), current_level()):
        ss["shrink_notice"] = True
        ss["mode"] = "game"
    else:
        new_game()


def ack_shrink_notice():
    """ผู้เล่นกดรับทราบการแจ้งเตือนเวลาลดลง: จำไว้ว่าแจ้งแล้ว (ด่านถัดไปไม่แจ้งซ้ำ) แล้วเริ่มด่านเลย"""
    st.session_state["shrink_warned"] = True
    new_game()


def game_score(status, attempts, hints, n_graphs):
    """คะแนนของเกมหนึ่งเกม (ถูกหมดในการส่งครั้งที่ attempts):
        คะแนนเต็มของจำนวนกราฟ − ATTEMPT_PENALTY[ครั้งที่ส่ง] (0, 2, 4) − จำนวนครั้งที่กดคำใบ้ × HINT_COST  (ไม่ติดลบ)
    แพ้ (ส่งครบ 3 ครั้งแล้วไม่ถูก) ได้ 0"""
    if status != "won" or n_graphs not in FULL_SCORE or not 1 <= attempts <= MAX_ATTEMPTS:
        return 0
    return max(0, FULL_SCORE[n_graphs] - ATTEMPT_PENALTY[attempts - 1] - HINT_COST * hints)


# =====================================================================
# ส่วนที่ 3: บอร์ดเกม (HTML + JavaScript ทำงานในเบราว์เซอร์)
# __GAME_JSON__ จะถูกแทนด้วยโจทย์ที่สุ่มจาก Python
# =====================================================================
BOARD_HTML = r"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLSIN board</title>
<style>
:root{
  --bg:#06100b; --bezel:#0d1d15; --panel:#0a1610; --line:#173f2b;
  --ink:#d4f7e2; --dim:#78b394; --mix:#39ff88; --recv:#ffb000; --bad:#ff7a6b;
  --mono:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;
  --sans:"Noto Sans Thai","Leelawadee UI",Tahoma,system-ui,sans-serif;
}
*{box-sizing:border-box}
[hidden]{display:none !important}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.45 var(--sans);-webkit-text-size-adjust:100%}
#app{max-width:1200px;margin:0 auto;padding:10px 12px 14px}
.top{background:var(--bg);padding-bottom:8px}
@media (min-width:700px){.top{position:sticky;top:0;z-index:5}}

.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:flex;align-items:baseline;gap:8px;padding:4px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bezel)}
.chip b{font:600 18px var(--mono);color:var(--mix)}
.chip span{font-size:12px;color:var(--dim)}
.chip em{font:600 12px var(--mono);font-style:normal;color:var(--recv)}
.actions{display:flex;flex-wrap:wrap;gap:8px}
.btn{font:600 14px var(--sans);padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:var(--bezel);color:var(--ink);cursor:pointer}
.btn:hover:not(:disabled){border-color:var(--mix)}
.btn.primary{background:#16a34a;border-color:#22c55e;color:#03140a}
.btn:disabled{opacity:.45;cursor:not-allowed}
:focus-visible{outline:2px solid var(--mix);outline-offset:2px}

.status{margin-top:8px;min-height:34px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bezel);font-size:13px}
.status.ok{border-color:#22c55e;background:#0c2a18}
.status.err{border-color:var(--bad);background:#2a1210}
.status.warn{border-color:var(--recv);background:#2a2008}

.screen{margin-top:8px;padding:6px 8px 4px;border:1px solid var(--line);border-radius:10px;background:var(--bg)}
.screen.solved{box-shadow:0 0 0 2px var(--mix),0 0 22px rgba(57,255,136,.35)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center;font-size:12px;color:var(--dim)}
.stagebadge{padding:1px 8px;border:1px solid var(--line);border-radius:6px;font:700 12px var(--mono);color:var(--recv)}
.timer{margin-left:auto;padding:0 4px;font:700 17px/1.2 var(--mono);color:var(--mix)}
.timer.off{font:600 12px var(--sans);color:var(--dim)}
.timer.warn{color:var(--recv)}
.timer.crit{color:var(--bad)}
.sw{display:inline-block;width:16px;height:4px;border-radius:2px;margin-right:6px;vertical-align:middle}
#big{display:block;width:100%;height:230px}

.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:6px}
@media (max-width:860px){.grid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:560px){.grid{grid-template-columns:1fr}}
.panel{padding:6px 8px 8px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.panel.bad{border-color:var(--bad)}
.ph{display:flex;justify-content:space-between;gap:6px;font:11px var(--mono);color:var(--dim)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.scope{display:block;width:100%;height:92px;margin-top:4px;border-radius:6px}
.knobs{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:6px}
.panel.off .knobs{opacity:.3;pointer-events:none}

.knob{display:flex;flex-direction:column;align-items:center;gap:2px}
.kname{font-size:11px;color:var(--dim);white-space:nowrap}
.dial{position:relative;width:58px;height:58px;border-radius:50%;cursor:grab;touch-action:none}
.dial:active{cursor:grabbing}
.dial svg{position:absolute;inset:0;width:100%;height:100%}
.cap{position:absolute;left:11px;top:11px;width:36px;height:36px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#2a4a39,#10201a);border:2px solid var(--mix);transition:transform .09s ease-out}
.cap::before{content:"";position:absolute;left:50%;top:3px;width:3px;height:12px;margin-left:-1.5px;border-radius:2px;background:var(--mix)}
.knob.locked .cap{border-color:var(--recv)}
.knob.locked .cap::before{background:var(--recv)}
.knob.locked .dial{cursor:not-allowed}
.knob.locked .readout,.knob.locked .kname{color:var(--recv)}
.knob.verified .cap{border-color:#22c55e;box-shadow:0 0 8px rgba(34,197,94,.45)}
.knob.verified .cap::before{background:#22c55e}
.knob.verified .dial{cursor:not-allowed}
.knob.verified .readout,.knob.verified .kname{color:#4ade80}
body.over .dial{cursor:not-allowed}
.dial.flash{animation:flash .9s ease-out 1}
@keyframes flash{0%{box-shadow:0 0 0 0 rgba(255,176,0,.9)}100%{box-shadow:0 0 0 14px rgba(255,176,0,0)}}
@media (prefers-reduced-motion:reduce){.cap{transition:none}.dial.flash{animation:none}}
.row{display:flex;align-items:center;gap:2px}
.step{width:20px;height:22px;padding:0;border:1px solid var(--line);border-radius:5px;background:var(--bezel);color:var(--ink);font-size:10px;cursor:pointer}
.step:disabled{opacity:.35;cursor:not-allowed}
.readout{min-width:50px;text-align:center;font:600 12px var(--mono);color:var(--mix)}

.help{margin:10px 2px 0;font-size:12px;color:var(--dim)}

/* หน้าสรุปผล */
#summary{position:fixed;inset:0;z-index:30;display:flex;align-items:center;justify-content:center;padding:12px;overflow:auto;background:rgba(3,10,6,.84)}
.sumcard{width:min(560px,100%);max-height:100%;overflow:auto;padding:16px 18px;border:2px solid var(--line);border-radius:14px;background:var(--bezel);box-shadow:0 10px 40px rgba(0,0,0,.6)}
.sumcard.win{border-color:#22c55e}
.sumcard.lose{border-color:var(--bad)}
.sumcard h2{margin:0;font-size:20px}
.sumcard h3{margin:14px 0 6px;font-size:14px;color:var(--dim)}
.sumcard p{margin:4px 0 0;font-size:13px;color:var(--dim)}
.scorelist{display:grid;grid-template-columns:1fr auto;gap:4px 0;margin-top:12px;font-size:14px}
.scorelist .v{padding-left:16px;text-align:right;font:600 14px var(--mono)}
.scorelist .big{margin-top:6px;padding-top:6px;border-top:1px solid var(--line);font-weight:700;font-size:16px}
.scorelist .v.big{color:var(--mix);font-size:22px}
.scorelist .tot{font-weight:700}
.scorelist .v.tot{color:var(--mix);font-size:18px}
.scorelist .hs{margin-top:4px;padding-top:6px;border-top:1px solid var(--line);font-weight:700;color:var(--recv)}
.scorelist .v.hs{font-size:18px}
#log table{border-collapse:collapse;font:13px var(--mono);width:100%}
#log th,#log td{padding:3px 12px 3px 0;text-align:left}
#log th{color:var(--dim);font-weight:600}
#log .ok{color:var(--mix)}
#log .no{color:var(--bad)}
.sumbtns{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.sumbtns .btn{flex:1 1 130px}
</style>
</head>
<body>
<div id="app">
  <div class="top">
    <div class="bar">
      <div class="chips">
        <div class="chip" title="จำนวนกราฟ sin ที่ซ่อนอยู่ในสัญญาณผสม"><b id="m-n">0</b><span>กราฟที่ซ่อน</span></div>
        <div class="chip" title="ค่าที่ล็อกแล้ว (🔒 ผู้ดูแลให้ + ✓ ตรงเฉลยจากการส่งตรวจ)"><b id="m-h">0</b><span>ค่าที่ล็อกแล้ว</span></div>
        <div class="chip" title="ส่งตรวจไปแล้วกี่ครั้ง จากสูงสุด 3 ครั้ง"><b id="m-a">0/3</b><span>ส่งตรวจ</span></div>
        <div class="chip" id="m-pbox"><b id="m-p">0</b><span id="m-pl">คะแนนถ้าถูก</span></div>
        <div class="chip" title="คะแนนรวมของเกมที่ชนะต่อเนื่อง (แพ้แล้วรีเซ็ตเป็น 0) · ⭐ = คะแนนสูงสุด เก็บไว้ไม่รีเซ็ต"><b id="m-t">0</b><span>คะแนนรวม</span><em id="m-hs">⭐ 0</em></div>
      </div>
      <div class="actions">
        <button id="hint" class="btn" type="button"></button>
        <button id="submit" class="btn primary" type="button">📤 ส่งให้ผู้ดูแลตรวจสอบ</button>
        <button id="showsum" class="btn" type="button" hidden>📋 สรุปผล</button>
      </div>
    </div>
    <div id="status" class="status" role="status" aria-live="polite"></div>
    <section id="bigscreen" class="screen" aria-label="จอใหญ่">
      <div class="legend">
        <span><i class="sw" style="background:#ffb000"></i>สัญญาณที่รับจากอวกาศ</span>
        <span><i class="sw" style="background:#39ff88"></i>สัญญาณที่คุณผสมได้ (ผลรวมทุกจอ)</span>
        <span id="stage" class="stagebadge"></span>
        <span id="timer" class="timer" role="timer" title="เวลาที่เหลือ (ไม่มีผลต่อคะแนน แต่ถ้าหมดเวลาเกมจะจบทันที)"></span>
      </div>
      <canvas id="big" role="img" aria-label="กราฟสัญญาณที่รับได้เทียบกับสัญญาณที่ผสม"></canvas>
    </section>
  </div>
  <div id="grid" class="grid"></div>
  <p class="help">ลากหมุนลูกบิด กดปุ่ม ◀ ▶ หรือใช้ปุ่มลูกศรบนคีย์บอร์ด · 🔒 สีเหลือง = ผู้ดูแลล็อกให้ · ✓ สีเขียว = ตรงเฉลยจากการส่งตรวจ (ล็อกแล้วเล่นต่อได้)</p>
</div>

<div id="summary" role="dialog" aria-modal="true" aria-labelledby="sum-title" hidden>
  <div id="sumcard" class="sumcard">
    <h2 id="sum-title"></h2>
    <p id="sum-sub"></p>
    <div id="sum-score" class="scorelist"></div>
    <h3 id="sum-key-title"></h3>
    <div id="log"></div>
    <div class="sumbtns">
      <span id="sum-actions" style="display:contents">
        <button id="sum-new" class="btn primary" type="button">🔄 เริ่มเกมใหม่</button>
        <button id="sum-sbx" class="btn" type="button">🧪 SANDBOX</button>
      </span>
      <button id="sum-close" class="btn" type="button">👁 ดูกราฟ</button>
    </div>
    <p id="sum-noact" hidden>ปุ่มเริ่มเกมใหม่และ SANDBOX อยู่ที่แถบด้านซ้าย</p>
  </div>
</div>

<script>
(function(){
"use strict";
const EMBEDDED = __GAME_JSON__;   // โจทย์ที่ฝังมาตรง ๆ (โหมด st.iframe) หรือ null เมื่อทำงานเป็น Streamlit component
let booted = false;

function boot(GAME, host){        // host = ตัวส่งผลกลับไปหา Streamlit (null ถ้าไม่มี)

/* ---------- ค่าคงที่ ---------- */
const N_SCREENS = 6, NPTS = 721, TOL = 1e-6;
const X_MAX = 4 * Math.PI, Y_LIM = 20;      // จอใหญ่ล็อกขอบเขตไว้: x = 0 ถึง 4π (เรเดียน), y = −20 ถึง 20
const FULL = Number.isFinite(GAME.full_score) ? GAME.full_score : 10;                       // คะแนนเต็มของเกมนี้ (ขึ้นกับจำนวนกราฟ)
const ATT_PEN = Array.isArray(GAME.attempt_penalty) && GAME.attempt_penalty.length ? GAME.attempt_penalty : [0, 2, 4];   // หักเมื่อถูกในครั้งที่ 1, 2, 3
const MAX_ATT = ATT_PEN.length;                                                             // ส่งตรวจได้สูงสุดกี่ครั้ง
const HINT_COST = Number.isFinite(GAME.hint_cost) ? GAME.hint_cost : 1;                     // คำใบ้เพิ่ม 1 ครั้ง หักกี่คะแนน
const BASE_TOTAL = Number.isFinite(GAME.base_total) ? GAME.base_total : 0;                  // คะแนนรวมก่อนเริ่มเกมนี้
const BASE_HIGH = Number.isFinite(GAME.base_high) ? GAME.base_high : 0;                     // คะแนนสูงสุดก่อนเริ่มเกมนี้
const TIME_LIMIT = Number.isFinite(GAME.time_limit) ? GAME.time_limit : 0;                  // เวลาของเกมนี้ (วินาที) 0 = ไม่จับเวลา (ระดับนักเรียน)
const TIMED = TIME_LIMIT > 0;
const HINT_BUTTON = GAME.hint_button !== false;                                            // ระดับอาจารย์ = ไม่มีปุ่มคำใบ้เพิ่ม
const STAGE = Number.isFinite(GAME.stage) ? GAME.stage : 1;                                // ด่านที่เล่นอยู่
const LEVEL = typeof GAME.difficulty === "string" ? GAME.difficulty : "";                  // ชื่อระดับความยาก
const T0 = Date.now();                                                                     // เวลาเริ่มเกม (ตอนบอร์ดเริ่มทำงาน)
const DEADLINE = T0 + TIME_LIMIT * 1000;
const PHASES = [0, 90, 180, 270];
const KINDS = ["amp", "freq", "phase"];
const VALUES = {amp:[-3,-2,-1,0,1,2,3], freq:[-3,-2,-1,0,1,2,3], phase:PHASES};
const NAME = {amp:"แอมพลิจูด", freq:"ความถี่", phase:"เฟส"};
const SYM = {amp:"A", freq:"f", phase:"φ"};
const PALETTE = ["#39ff88","#4dd2ff","#ff7ad9","#ffd24d","#b794ff","#ff8a5c"];
const C = {bg:"#06100b", grid:"#14402a", gridMinor:"#0c2a1b", axis:"#2d7a52", ink:"#9fe3bd", recv:"#ffb000", mix:"#39ff88"};
const MONO = 'ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace';
const N = GAME.components.length;
const NEXT_GRAPHS = Number.isFinite(GAME.next_graphs) ? GAME.next_graphs : N;               // ด่านถัดไปมีกี่กราฟ
const $ = (s, r) => (r || document).querySelector(s);
const fmt = v => v < 0 ? "−" + (-v) : String(v);
const fmtVal = (k, v) => fmt(v) + (k === "phase" ? "°" : "");

const X = new Float64Array(NPTS);
for (let j = 0; j < NPTS; j++) X[j] = X_MAX * j / (NPTS - 1);

/* =====================================================================
   CALCULATION: คำนวณคลื่น ตรวจคำตอบ ให้คะแนน
   ===================================================================== */
function wave(a, f, p){
  const out = new Float64Array(NPTS), ph = p * Math.PI / 180;
  for (let j = 0; j < NPTS; j++) out[j] = a * Math.sin(f * X[j] + ph);
  return out;
}

// สัญญาณปริศนา = ผลรวมของกราฟ sin ที่ซ่อนอยู่
const KEY = GAME.components;                                  // เฉลย (A, f, φ) ของแต่ละจอ
const KEYWAVE = KEY.map(c => wave(c.amp, c.freq, c.phase));
const TARGET = new Float64Array(NPTS);
KEYWAVE.forEach(w => { for (let j = 0; j < NPTS; j++) TARGET[j] += w[j]; });

const state = {knobs:[], locked:[], verified:[], bonusLeft:GAME.bonus.length, hintsUsed:0,
               attempts:0, solved:false, over:false, score:0, seq:0, last:null,
               totalAfter:BASE_TOTAL, highAfter:BASE_HIGH, record:false, timedOut:false, timeLeft:TIME_LIMIT, usedSec:0};
for (let i = 0; i < N_SCREENS; i++){
  const on = i < N;
  state.knobs.push(on ? {amp:1, freq:1, phase:0} : {amp:0, freq:0, phase:0});
  state.locked.push({amp:!on, freq:!on, phase:!on});
  state.verified.push({amp:false, freq:false, phase:false});
}
// คำใบ้เริ่มต้นจากผู้ดูแล: ตั้งค่าที่ถูกต้องและล็อกลูกบิดไว้
GAME.hints.forEach((ks, i) => ks.forEach(k => {
  state.knobs[i][k] = KEY[i][k];
  state.locked[i][k] = true;
}));
const queue = GAME.bonus.map(p => p.slice());                 // ลำดับค่าที่จะใบ้เพิ่ม

const cur = new Array(N_SCREENS).fill(null);   // คลื่นปัจจุบันของแต่ละจอ
let MIX = new Float64Array(NPTS);              // ผลรวมของทุกจอ

function recompute(i){
  if (i < N){ const k = state.knobs[i]; cur[i] = wave(k.amp, k.freq, k.phase); }
}
function recomputeMix(){
  MIX = new Float64Array(NPTS);
  for (let i = 0; i < N; i++) for (let j = 0; j < NPTS; j++) MIX[j] += cur[i][j];
}
function checkAnswer(){
  let maxErr = 0, se = 0, st = 0;
  for (let j = 0; j < NPTS; j++){
    const e = MIX[j] - TARGET[j];
    maxErr = Math.max(maxErr, Math.abs(e)); se += e * e; st += TARGET[j] * TARGET[j];
  }
  const match = Math.max(0, 100 * (1 - Math.sqrt(se / NPTS) / Math.sqrt(st / NPTS)));
  return {correct: maxErr < TOL, match};
}
function invalidScreens(){
  const bad = [];
  for (let i = 0; i < N; i++) if (state.knobs[i].amp === 0 || state.knobs[i].freq === 0) bad.push(i + 1);
  return bad;
}
function sameWave(a, b){
  for (let j = 0; j < NPTS; j++) if (Math.abs(a[j] - b[j]) >= TOL) return false;
  return true;
}
// หลังส่งตรวจ: ล็อกค่าที่ตรงกับเฉลยทันที (ถ้าจอนั้นได้กราฟเดียวกับเฉลยแล้ว ล็อกครบทั้ง 3 ลูกบิด)
function lockMatches(){
  let n = 0;
  for (let i = 0; i < N; i++){
    const screenOk = sameWave(cur[i], KEYWAVE[i]);
    KINDS.forEach(k => {
      if (state.locked[i][k]) return;
      if (screenOk || state.knobs[i][k] === KEY[i][k]){ state.locked[i][k] = true; state.verified[i][k] = true; n++; }
    });
  }
  return n;
}
const lockedCount = () => { let n = 0; for (let i = 0; i < N; i++) KINDS.forEach(k => { if (state.locked[i][k]) n++; }); return n; };
// คะแนนถ้าส่งถูกหมดในครั้งที่ att = คะแนนเต็ม − (หักตามครั้งที่ส่ง 0, 2, 4) − (คำใบ้ที่ใช้ × 1)
const scoreFor = (att, hints) => Math.max(0, FULL - ATT_PEN[Math.min(att, MAX_ATT) - 1] - hints * HINT_COST);
const potential = () => scoreFor(state.attempts + 1, state.hintsUsed);          // ถ้าส่งถูกในครั้งถัดไป

/* =====================================================================
   OUTPUT: วาดจอใหญ่ จอเล็ก และข้อความ
   ===================================================================== */
function setup(c){
  const r = c.getBoundingClientRect(), d = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
  if (c.width !== Math.round(w * d) || c.height !== Math.round(h * d)){
    c.width = Math.round(w * d); c.height = Math.round(h * d);
  }
  const g = c.getContext("2d");
  g.setTransform(d, 0, 0, d, 0, 0);
  return {g, w, h};
}
function frame(g, w, h, pad, ylim, yTicks, xLabels, fontPx){
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  const x0 = pad.l, x1 = w - pad.r, y0 = pad.t, y1 = h - pad.b;
  const px = x => x0 + x / X_MAX * (x1 - x0);              // x อยู่ในช่วง 0 ถึง 4π
  const py = y => y0 + (1 - (y + ylim) / (2 * ylim)) * (y1 - y0);
  g.lineWidth = 1; g.strokeStyle = C.grid; g.fillStyle = C.ink; g.font = fontPx + "px " + MONO;
  g.textAlign = "right"; g.textBaseline = "middle";
  yTicks.forEach(t => {
    const y = py(t);
    g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke();
    g.fillText(fmt(t), x0 - 4, y);
  });
  for (let q = 0; q <= 8; q++){                           // เส้นกริดทุก π/2 (เส้นหลักทุก π)
    const x = px(q * Math.PI / 2), major = q % 2 === 0;
    g.strokeStyle = major ? C.grid : C.gridMinor;
    g.beginPath(); g.moveTo(x, y0); g.lineTo(x, y1); g.stroke();
    if (xLabels && major){
      g.fillStyle = C.ink;
      g.textAlign = q === 0 ? "left" : (q === 8 ? "right" : "center");
      g.textBaseline = "top"; g.fillText(xLabels[q / 2], x, y1 + 4);
    }
  }
  g.strokeStyle = C.axis; g.beginPath(); g.moveTo(x0, py(0)); g.lineTo(x1, py(0)); g.stroke();
  return {px, py, x0, x1, y0, y1};
}
function curve(g, F, arr, color, lw, glow){
  g.save();
  g.beginPath(); g.rect(F.x0, F.y0, F.x1 - F.x0, F.y1 - F.y0); g.clip();
  g.beginPath();
  for (let j = 0; j < NPTS; j++){
    const x = F.px(X[j]), y = F.py(arr[j]);
    if (j) g.lineTo(x, y); else g.moveTo(x, y);
  }
  g.strokeStyle = color; g.lineWidth = lw; g.lineJoin = "round";
  if (glow){ g.shadowColor = color; g.shadowBlur = glow; }
  g.stroke();
  g.restore();
}
function drawBig(){
  const {g, w, h} = setup(bigCanvas);
  const ticks = [];
  for (let t = -Y_LIM; t <= Y_LIM; t += 5) ticks.push(t);         // แกน y คงที่ −20 ถึง 20 ไม่ขยายตามกราฟ
  const F = frame(g, w, h, {l:34, r:10, t:8, b:20}, Y_LIM, ticks, ["0","π","2π","3π","4π"], 11);
  curve(g, F, TARGET, C.recv, 3.4, 0);
  curve(g, F, MIX, C.mix, 1.6, state.solved ? 8 : 0);
}
function drawSmall(i){
  const {g, w, h} = setup(els[i].canvas);
  const F = frame(g, w, h, {l:22, r:4, t:3, b:3}, 3.7, [-3,-2,-1,0,1,2,3], null, 9);
  curve(g, F, cur[i], PALETTE[i], 2, 0);
}
function drawOff(i){                                      // จอที่ไม่ได้ใช้: พื้นเรียบ ๆ กับคำว่า NO SIGNAL เท่านั้น (ไม่มีสัญญาณรบกวน)
  const {g, w, h} = setup(els[i].canvas);
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  g.font = "700 " + Math.min(24, Math.max(14, w / 13)) + "px " + MONO;
  g.fillStyle = "#ff7a6b"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("NO SIGNAL", w / 2, h / 2 + 1);
}
function drawScreen(i){ if (i < N) drawSmall(i); else drawOff(i); }

function renderKnob(i, k){
  const K = els[i].knobs[k], on = i < N, v = state.knobs[i][k];
  const vals = VALUES[k], L = vals.length, idx = vals.indexOf(v);
  const locked = state.locked[i][k], ver = state.verified[i][k], frozen = locked || state.over;
  K.cap.style.transform = "rotate(" + (-135 + idx * 270 / (L - 1)) + "deg)";
  K.root.classList.toggle("locked", locked && !ver && on);          // 🔒 สีเหลือง = ผู้ดูแลบอกให้
  K.root.classList.toggle("verified", ver && on);                   // ✓ สีเขียว = ตรงเฉลยจากการส่งตรวจ
  K.name.textContent = (ver && on ? "✓ " : (locked && on ? "🔒 " : "")) + NAME[k];
  K.readout.textContent = on ? SYM[k] + "=" + fmtVal(k, v) : "-";
  K.dec.disabled = frozen; K.inc.disabled = frozen;
  K.dial.tabIndex = on ? 0 : -1;
  K.dial.setAttribute("aria-valuenow", String(idx));
  K.dial.setAttribute("aria-valuetext", on ? NAME[k] + " " + fmtVal(k, v) + (ver ? " (ถูกต้อง ล็อกแล้ว)" : locked ? " (ล็อกแล้ว)" : "") : "ไม่มีสัญญาณ");
  K.dial.setAttribute("aria-disabled", String(frozen));
}
function renderPanel(i){
  const k = state.knobs[i];
  els[i].eq.textContent = i < N ? "y = " + fmt(k.amp) + "·sin(" + fmt(k.freq) + "x + " + k.phase + "°)" : "OFFLINE";
  els[i].panel.classList.toggle("bad", i < N && (k.amp === 0 || k.freq === 0));
}
function renderMeta(){
  $("#m-n").textContent = N;
  $("#m-h").textContent = lockedCount();
  $("#m-a").textContent = state.attempts + "/" + MAX_ATT;
  $("#m-p").textContent = state.over ? state.score : potential();
  $("#m-pl").textContent = state.over ? "คะแนนเกมนี้" : "คะแนนถ้าถูก";
  $("#m-pbox").title = state.over ? "คะแนนของเกมนี้" : "คะแนนที่จะได้ถ้าส่งแล้วถูกในครั้งถัดไป (หักคำใบ้ที่ใช้แล้ว)";
  $("#m-t").textContent = state.totalAfter;
  $("#m-hs").textContent = "⭐ " + state.highAfter;
  const hb = $("#hint");
  hb.textContent = "💡 ขอคำใบ้เพิ่ม (เหลือ " + state.bonusLeft + " ครั้ง)";
  hb.title = "ขอคำใบ้ 1 ครั้ง ผู้ดูแลบอกค่าที่ถูกต้องเพิ่ม 1 ค่า และหัก " + HINT_COST + " คะแนน";
  hb.hidden = !HINT_BUTTON;                                       // ระดับอาจารย์: ไม่มีปุ่มคำใบ้
  hb.disabled = state.over || state.bonusLeft <= 0;
  $("#submit").disabled = state.over;
  $("#showsum").hidden = !state.over;
  document.body.classList.toggle("over", state.over);
}
/* ---- จับเวลาถอยหลัง: คิดจากนาฬิกาจริง (Date.now) ไม่ใช่จำนวนครั้งที่ตัวจับเวลาทำงาน เพราะเบราว์เซอร์หน่วงตัวจับเวลาเมื่อสลับแท็บ ---- */
const mmss = sec => String(Math.floor(sec / 60)).padStart(2, "0") + ":" + String(sec % 60).padStart(2, "0");
const remainingSec = () => TIMED ? Math.max(0, Math.ceil((DEADLINE - Date.now()) / 1000)) : Infinity;
let clockId = null;
function paintTimer(left){
  const el = $("#timer");
  if (!TIMED){ el.textContent = "⏱ ไม่จำกัดเวลา"; el.className = "timer off"; return; }
  el.textContent = "⏱ " + mmss(left);
  el.className = "timer" + (left <= 10 ? " crit" : left <= 30 ? " warn" : "");
}
function tick(){
  if (state.over || !TIMED) return;
  const left = remainingSec();
  paintTimer(left);
  if (left <= 0) timeUp();
}
function stopClock(){
  clearInterval(clockId);
  if (TIMED){
    state.timeLeft = state.timedOut ? 0 : remainingSec();
    state.usedSec = Math.max(0, Math.min(TIME_LIMIT, TIME_LIMIT - state.timeLeft));
    paintTimer(state.timeLeft);
  } else {
    state.usedSec = Math.max(0, Math.round((Date.now() - T0) / 1000));   // ไม่จับเวลา: บอกเวลาที่ใช้จริงไว้ดูเฉย ๆ
  }
}
// เวลาหมด: เกมจบทันที นับเป็นแพ้ (เหมือนส่งครบ 3 ครั้งแล้วไม่ถูก) เวลาไม่มีผลต่อคะแนนอย่างอื่น
function timeUp(){
  if (state.over) return;
  state.over = true; state.timedOut = true; state.score = 0;
  state.totalAfter = 0;
  state.highAfter = Math.max(BASE_HIGH, BASE_TOTAL);
  revealAnswer();
  setStatus("err", "หมดเวลา! เกมจบ ผู้ดูแลเฉลยคำตอบที่ถูกต้องบนลูกบิดให้แล้ว (ได้ 0 คะแนนในเกมนี้ · คะแนนรวมรีเซ็ตเป็น 0 · คะแนนสูงสุด " + state.highAfter + ")");
  renderAll(); drawBig();
  finish();
}

function setStatus(kind, text){
  const s = $("#status"); s.className = "status " + kind; s.textContent = text;
}
function refresh(i){
  if (i === undefined){ for (let s = 0; s < N; s++) recompute(s); } else recompute(i);
  recomputeMix();
  drawBig();
  if (i === undefined){ for (let s = 0; s < N_SCREENS; s++){ drawScreen(s); renderPanel(s); } }
  else { drawScreen(i); renderPanel(i); }
}
function renderAll(){
  for (let i = 0; i < N_SCREENS; i++) KINDS.forEach(k => renderKnob(i, k));
  renderMeta();
}

/* =====================================================================
   INPUT: ลูกบิด 3 ลูกต่อจอ (ลากหมุน, ปุ่ม ◀ ▶, ลูกศรบนคีย์บอร์ด) + ปุ่มคำใบ้ + ปุ่มส่งตรวจ
   ===================================================================== */
const bigCanvas = $("#big");
const els = [];
const ro = new ResizeObserver(entries => entries.forEach(e => { if (e.target._draw) e.target._draw(); }));
bigCanvas._draw = drawBig; ro.observe(bigCanvas);

function buildKnob(i, k, parent){
  const root = document.createElement("div");
  root.className = "knob";
  root.innerHTML =
    '<div class="kname"></div>' +
    '<div class="dial" role="slider"><svg viewBox="0 0 58 58" aria-hidden="true"></svg><div class="cap"></div></div>' +
    '<div class="row"><button class="step" type="button" tabindex="-1">◀</button><span class="readout"></span>' +
    '<button class="step" type="button" tabindex="-1">▶</button></div>';
  parent.appendChild(root);
  const vals = VALUES[k], L = vals.length;
  let ticks = "";
  for (let q = 0; q < L; q++){
    const a = (-135 + q * 270 / (L - 1)) * Math.PI / 180, s = Math.sin(a), c = Math.cos(a);
    ticks += '<line x1="' + (29 + 22 * s).toFixed(1) + '" y1="' + (29 - 22 * c).toFixed(1) +
             '" x2="' + (29 + 27 * s).toFixed(1) + '" y2="' + (29 - 27 * c).toFixed(1) +
             '" stroke="#2f6b4a" stroke-width="2" stroke-linecap="round"/>';
  }
  $("svg", root).innerHTML = ticks;
  const K = {root, name:$(".kname", root), dial:$(".dial", root), cap:$(".cap", root),
             readout:$(".readout", root), dec:$(".step", root), inc:root.querySelectorAll(".step")[1]};
  K.dial.setAttribute("aria-label", "จอ " + (i + 1) + " " + NAME[k]);
  K.dial.setAttribute("aria-valuemin", "0"); K.dial.setAttribute("aria-valuemax", String(L - 1));

  const idxOf = () => vals.indexOf(state.knobs[i][k]);
  function setIdx(idx){
    if (state.locked[i][k] || state.over) return;
    idx = Math.max(0, Math.min(L - 1, idx));
    const v = vals[idx];
    if (v === state.knobs[i][k]) return;
    state.knobs[i][k] = v;
    renderKnob(i, k);
    refresh(i);                       // วาดใหม่ทันที ไม่ผ่านเซิร์ฟเวอร์
    renderMeta();
  }
  K.dec.addEventListener("click", () => setIdx(idxOf() - 1));
  K.inc.addEventListener("click", () => setIdx(idxOf() + 1));
  K.dial.addEventListener("keydown", e => {
    const m = {ArrowLeft:-1, ArrowDown:-1, ArrowRight:1, ArrowUp:1};
    if (e.key in m){ e.preventDefault(); setIdx(idxOf() + m[e.key]); }
    else if (e.key === "Home"){ e.preventDefault(); setIdx(0); }
    else if (e.key === "End"){ e.preventDefault(); setIdx(L - 1); }
  });
  let drag = false;
  function aim(e){
    const r = K.dial.getBoundingClientRect();
    let ang = Math.atan2(e.clientX - (r.left + r.width / 2), -(e.clientY - (r.top + r.height / 2))) * 180 / Math.PI;
    ang = Math.max(-135, Math.min(135, ang));
    setIdx(Math.round((ang + 135) / (270 / (L - 1))));
  }
  K.dial.addEventListener("pointerdown", e => {
    if (state.locked[i][k] || state.over) return;
    drag = true; K.dial.setPointerCapture(e.pointerId);
    K.dial.focus({preventScroll:true}); aim(e);
  });
  K.dial.addEventListener("pointermove", e => { if (drag) aim(e); });
  ["pointerup", "pointercancel"].forEach(t => K.dial.addEventListener(t, () => { drag = false; }));
  return K;
}

function buildPanels(){
  const grid = $("#grid");
  for (let i = 0; i < N_SCREENS; i++){
    const panel = document.createElement("article");
    panel.className = "panel" + (i < N ? "" : " off");
    panel.innerHTML =
      '<div class="ph"><span><i class="dot" style="background:' + (i < N ? PALETTE[i] : "#3d4d44") +
      '"></i>SCREEN ' + (i + 1) + '</span><span class="eq"></span></div>' +
      '<canvas class="scope"></canvas><div class="knobs"></div>';
    grid.appendChild(panel);
    const canvas = $(".scope", panel), hostEl = $(".knobs", panel);
    const entry = {panel, canvas, eq:$(".eq", panel), knobs:{}};
    els.push(entry);
    KINDS.forEach(k => { entry.knobs[k] = buildKnob(i, k, hostEl); });
    canvas._draw = () => drawScreen(i);
    ro.observe(canvas);
  }
}

// ขอคำใบ้เพิ่ม: ผู้ดูแลบอกค่าที่ถูกต้อง 1 ค่า (ข้ามค่าที่ล็อกไปแล้ว) แลกกับการหักคะแนน
function nextPick(){
  while (queue.length){
    const p = queue.shift();
    if (p[0] < N && !state.locked[p[0]][p[1]]) return p;
  }
  const free = [];
  for (let i = 0; i < N; i++) KINDS.forEach(k => { if (!state.locked[i][k]) free.push([i, k]); });
  return free.length ? free[Math.floor(Math.random() * free.length)] : null;
}
function useHint(){
  if (!HINT_BUTTON || state.over || state.bonusLeft <= 0) return;
  if (remainingSec() <= 0){ timeUp(); return; }
  const pick = nextPick();
  if (!pick){ setStatus("warn", "ทุกค่าถูกล็อกไว้หมดแล้ว ไม่มีค่าให้ใบ้เพิ่ม (ไม่หักคะแนน)"); return; }
  const i = pick[0], k = pick[1], v = KEY[i][k];
  state.bonusLeft--; state.hintsUsed++;
  state.knobs[i][k] = v; state.locked[i][k] = true;
  renderKnob(i, k); refresh(i); renderMeta();
  const dial = els[i].knobs[k].dial;
  dial.classList.remove("flash"); void dial.offsetWidth; dial.classList.add("flash");
  setStatus("warn", "ผู้ดูแลให้คำใบ้เพิ่ม: จอ " + (i + 1) + " " + NAME[k] + " " + SYM[k] + " = " + fmtVal(k, v) +
            " (หัก " + HINT_COST + " คะแนน)");
}

function submit(){
  if (state.over) return;
  if (remainingSec() <= 0){ timeUp(); return; }            // เลยเวลาแล้ว (เช่นแท็บอยู่เบื้องหลัง) ไม่รับคำตอบ
  const bad = invalidScreens();
  if (bad.length){
    setStatus("warn", "จอ " + bad.join(", ") + " ยังเป็น A = 0 หรือ f = 0 (ไม่ใช่คลื่น sin) ปรับลูกบิดก่อนส่งตรวจ");
    return;
  }
  state.attempts++;
  state.last = state.knobs.slice(0, N).map(k => ({amp:k.amp, freq:k.freq, phase:k.phase}));   // คำตอบที่ส่งครั้งล่าสุด
  const res = checkAnswer();
  if (res.correct){
    state.solved = true; state.over = true;
    state.score = scoreFor(state.attempts, state.hintsUsed);
    state.totalAfter = BASE_TOTAL + state.score;                       // ชนะ: คะแนนรวมสะสมต่อ
    state.record = state.totalAfter > BASE_HIGH;
    state.highAfter = Math.max(BASE_HIGH, state.totalAfter);
    $("#bigscreen").classList.add("solved");
    setStatus("ok", "ถอดรหัสสำเร็จ! ผู้ดูแลยืนยันว่าแยกได้ครบทั้ง " + N + " กราฟ (ส่งตรวจ " + state.attempts + " ครั้ง) ได้ " + state.score + " คะแนน");
    renderAll(); drawBig();
    finish();
    return;
  }
  const locks = lockMatches();
  if (state.attempts >= MAX_ATT){
    state.over = true; state.score = 0;
    state.totalAfter = 0;                                             // แพ้: คะแนนรวมรีเซ็ตเป็น 0 แต่คะแนนสูงสุดยังอยู่
    state.highAfter = Math.max(BASE_HIGH, BASE_TOTAL);
    revealAnswer();
    setStatus("err", "ส่งตรวจครบ " + MAX_ATT + " ครั้งแล้วยังไม่ถูกต้อง ผู้ดูแลเฉลยคำตอบที่ถูกต้องบนลูกบิดให้แล้ว (ได้ 0 คะแนนในเกมนี้ · คะแนนรวมรีเซ็ตเป็น 0 · คะแนนสูงสุด "
              + state.highAfter + ")");
    renderAll(); drawBig();
    finish();
    return;
  }
  const pct = (Math.floor(res.match * 10) / 10).toFixed(1);
  setStatus("err", "ผู้ดูแลตรวจครั้งที่ " + state.attempts + "/" + MAX_ATT + ": ยังไม่ถูกต้อง สัญญาณตรงกัน " + pct + "% · " +
            (locks ? "ล็อกค่าที่ตรงเฉลยให้ " + locks + " ค่า (✓ สีเขียว)" : "ยังไม่มีค่าไหนตรงเฉลยเพิ่ม") +
            " · เหลือสิทธิ์ส่งอีก " + (MAX_ATT - state.attempts) + " ครั้ง (ถ้าถูกครั้งหน้าได้ " + potential() + " คะแนน)");
  renderAll(); drawBig();
}
function revealAnswer(){                                  // แสดงเฉลยบนลูกบิดของทุกจอที่ใช้งาน
  for (let i = 0; i < N; i++) KINDS.forEach(k => {
    state.knobs[i][k] = KEY[i][k];
    if (!state.locked[i][k]) state.locked[i][k] = true;
  });
  refresh();
}

/* =====================================================================
   OUTPUT: หน้าสรุปผล (ทั้งตอนถูกและตอนหมดสิทธิ์) + ส่งผลกลับไปที่ Streamlit
   ===================================================================== */
function report(extra){
  if (!host) return;
  state.seq++;
  host.send(Object.assign({gid:GAME.id, seq:state.seq, status: state.over ? (state.solved ? "won" : "lost") : "playing",
                           score:state.score, attempts:state.attempts, hints:state.hintsUsed, timeout:state.timedOut}, extra || {}));
}
function answerTable(){
  const lost = !state.solved;
  const rows = KEY.map((c, i) => {
    let yours = "";
    if (lost && state.last){
      const y = state.last[i], whole = sameWave(wave(y.amp, y.freq, y.phase), KEYWAVE[i]);
      yours = "<td>" + KINDS.map(k => '<span class="' + (whole || y[k] === c[k] ? "ok" : "no") + '">' + SYM[k] + "=" + fmtVal(k, y[k]) + "</span>").join(" ") + "</td>";
    }
    return "<tr><td>SCREEN " + (i + 1) + "</td><td>" + fmt(c.amp) + "</td><td>" + fmt(c.freq) + "</td><td>" + c.phase + "°</td>" + yours + "</tr>";
  }).join("");
  return "<table><thead><tr><th>จอ</th><th>A</th><th>f</th><th>φ</th>" + (lost && state.last ? "<th>คำตอบที่ส่งล่าสุดของคุณ</th>" : "") +
         "</tr></thead><tbody>" + rows + "</tbody></table>" +
         "<p>ค่าอื่นที่ให้กราฟเดียวกันก็ถือว่าถูก เช่น A = −1, f = 1, φ = 180° ให้กราฟเดียวกับ A = 1, f = 1, φ = 0°</p>";
}
function scoreRows(){
  const won = state.solved, pen = ATT_PEN[Math.max(1, Math.min(state.attempts, MAX_ATT)) - 1], hp = state.hintsUsed * HINT_COST;
  const r = [["ส่งตรวจ", state.attempts + " / " + MAX_ATT + " ครั้ง", ""],
             ["เวลาที่ใช้ (ไม่มีผลต่อคะแนน)", mmss(state.usedSec) + (TIMED ? " / " + mmss(TIME_LIMIT) : ""), ""]];
  if (won){
    r.push(["คะแนนเต็ม (" + N + " กราฟ)", "+" + FULL, ""]);
    r.push(["ส่งถูกในครั้งที่ " + state.attempts + (pen ? " (หักตามครั้งที่ส่ง)" : " (ไม่หัก)"), fmt(-pen), ""]);
    if (HINT_BUTTON) r.push(["คำใบ้เพิ่มที่ใช้ " + state.hintsUsed + " ครั้ง (ครั้งละ −" + HINT_COST + ")", fmt(-hp), ""]);
    r.push(["คะแนนเกมนี้", String(state.score), "big"]);
    r.push(["คะแนนรวม", String(state.totalAfter), "tot"]);
  } else {
    r.push([state.timedOut ? "หมดเวลา เกมจบทันที" : "ตอบไม่ถูกครบ " + MAX_ATT + " ครั้ง", "0", ""]);
    if (state.hintsUsed) r.push(["คำใบ้เพิ่มที่ใช้ " + state.hintsUsed + " ครั้ง (ไม่หักเพิ่ม เพราะไม่มีคะแนนให้หัก)", "", ""]);
    r.push(["คะแนนเกมนี้", "0", "big"]);
    r.push(["คะแนนรวมสะสมก่อนแพ้", String(BASE_TOTAL), ""]);
    r.push(["คะแนนรวมถูกรีเซ็ต", "0", "tot"]);
  }
  r.push(["⭐ คะแนนสูงสุด" + (won && state.record ? " — สถิติใหม่! 🎉" : ""), String(state.highAfter), "hs"]);
  return r.map(x => '<div class="' + x[2] + '">' + x[0] + '</div><div class="v ' + x[2] + '">' + x[1] + "</div>").join("");
}
function buildSummary(){
  const won = state.solved;
  $("#sumcard").className = "sumcard " + (won ? "win" : "lose");
  $("#sum-title").textContent = won ? "🎉 ถอดรหัสสำเร็จ! ผ่านด่านที่ " + STAGE :
                                state.timedOut ? "⏰ หมดเวลา — เกมจบที่ด่านที่ " + STAGE : "📡 หมดสิทธิ์ส่งตรวจ — เกมจบที่ด่านที่ " + STAGE;
  const reset = " · คะแนนรวมรีเซ็ต กลับไปเริ่มที่ด่านที่ 1";
  $("#sum-sub").textContent = won ? "ผู้ดูแลยืนยันว่าแยกได้ครบทั้ง " + N + " กราฟ" + (NEXT_GRAPHS > N ? " · ด่านถัดไปกราฟผสมเพิ่มเป็น " + NEXT_GRAPHS + " กราฟ" : "") :
                              state.timedOut ? "หมดเวลาก่อนถอดรหัสสำเร็จ (ส่งตรวจไป " + state.attempts + " / " + MAX_ATT + " ครั้ง) นี่คือเฉลย" + reset :
                                               "ส่งตรวจครบ " + MAX_ATT + " ครั้งแล้วยังไม่ถูกต้อง นี่คือเฉลย" + reset;
  $("#sum-new").textContent = won ? "➡ ด่านถัดไป (ด่านที่ " + (STAGE + 1) + " · " + NEXT_GRAPHS + " กราฟ)" : "🔄 เริ่มใหม่ (กลับไปด่านที่ 1)";
  $("#sum-score").innerHTML = scoreRows();
  $("#sum-key-title").textContent = won ? "บันทึกของผู้ดูแล" : "เฉลยที่ถูกต้อง";
  $("#log").innerHTML = answerTable();
}
function openSummary(){
  $("#summary").hidden = false;
  try { $("#sumcard").scrollIntoView({block:"center"}); } catch (e) {}   // ถ้า iframe อยู่นอกจอ ให้เลื่อนมาให้เห็นหน้าสรุป
  const first = host ? $("#sum-new") : $("#sum-close");
  first.focus({preventScroll:true});
}
function closeSummary(){
  $("#summary").hidden = true;
  $("#showsum").focus({preventScroll:true});
}
function finish(){
  stopClock(); buildSummary(); openSummary(); report();
}
function act(name){                                       // ปุ่มในหน้าสรุป: ส่งคำสั่งไปให้ Streamlit ทำต่อ
  if (!host) return;
  const btns = [$("#sum-new"), $("#sum-sbx")];
  btns.forEach(b => { b.disabled = true; });
  report({action:name});
  if (name === "sandbox") $("#summary").hidden = true;   // กลับมาที่เกมเมื่อไรจะเห็นกระดานเดิม เปิดสรุปได้ที่ปุ่ม 📋
  setTimeout(() => btns.forEach(b => { b.disabled = false; }), 5000);    // ถ้าไม่มีอะไรเกิดขึ้น ให้กดใหม่ได้
}

$("#hint").addEventListener("click", useHint);
$("#submit").addEventListener("click", submit);
$("#showsum").addEventListener("click", openSummary);
$("#sum-close").addEventListener("click", closeSummary);
$("#sum-new").addEventListener("click", () => act("new"));
$("#sum-sbx").addEventListener("click", () => act("sandbox"));
document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("#summary").hidden) closeSummary(); });
if (!host){                                               // ไม่ได้ทำงานเป็น Streamlit component: ไม่มีปุ่มที่สื่อสารกลับได้
  $("#sum-actions").hidden = true; $("#sum-noact").hidden = false;
}

buildPanels();
renderAll();
refresh();
$("#stage").textContent = "ด่าน " + STAGE + " · " + N + " กราฟ" + (LEVEL ? " · " + LEVEL : "");
$("#stage").title = "ด่านที่ " + STAGE + " มีกราฟผสม " + N + " กราฟ · ระดับ " + LEVEL;
paintTimer(TIME_LIMIT);
if (TIMED) clockId = setInterval(tick, 250);
document.addEventListener("visibilitychange", tick);       // กลับมาที่แท็บแล้วตรวจเวลาทันที
setStatus("", "จูนลูกบิดจนเส้นสีเขียวทับเส้นสีเหลืองพอดี แล้วกดส่งให้ผู้ดูแลตรวจสอบ (ส่งได้ " + MAX_ATT + " ครั้ง · คะแนนเต็ม " + FULL + " สำหรับ " + N + " กราฟ: ถูกครั้งที่ " +
          ATT_PEN.map((p, q) => (q + 1) + " ได้ " + (FULL - p)).join(", ") + " คะแนน" + (HINT_BUTTON ? " แล้วหักคำใบ้ที่ใช้ครั้งละ " + HINT_COST : "") + ")");
}   // จบ boot

/* =====================================================================
   เริ่มทำงาน: ฝังโจทย์มาตรง ๆ หรือรอรับโจทย์จาก Streamlit (โปรโตคอลของ custom component)
   ===================================================================== */
function post(type, data){
  window.parent.postMessage(Object.assign({isStreamlitMessage:true, type:type}, data || {}), "*");
}
if (EMBEDDED){
  boot(EMBEDDED, null);
} else {
  window.addEventListener("message", ev => {
    const m = ev.data;
    if (!m || m.type !== "streamlit:render") return;
    const a = m.args || {};
    post("streamlit:setFrameHeight", {height: a.height || 900});
    if (!booted && a.game){
      booted = true;
      boot(a.game, {send: v => post("streamlit:setComponentValue", {value:v, dataType:"json"})});
    }
  });
  post("streamlit:componentReady", {apiVersion:1});
}
})();
</script>
</body>
</html>
"""


# =====================================================================
# ส่วนเสริม: SANDBOX (HTML + JavaScript) อยู่ในแถบด้านซ้าย
# กราฟ sin ที่ปรับ A, f, φ ได้อิสระ ไม่มีโจทย์ ไม่จำกัดค่าเหมือนในเกม
# =====================================================================
SANDBOX_HTML = r"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLSIN sandbox</title>
<style>
:root{
  --bg:#06100b; --bezel:#0d1d15; --panel:#0a1610; --line:#173f2b;
  --ink:#d4f7e2; --dim:#78b394; --mix:#39ff88; --sum:#ffb000; --warn:#ffb000;
  --mono:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;
  --sans:"Noto Sans Thai","Leelawadee UI",Tahoma,system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.45 var(--sans);-webkit-text-size-adjust:100%}
#app{max-width:1200px;margin:0 auto;padding:10px 12px 14px}

.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:flex;align-items:baseline;gap:8px;padding:4px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bezel)}
.chip b{font:600 18px var(--mono);color:var(--mix)}
.chip.a0 b{color:var(--sum)}
.chip span{font-size:12px;color:var(--dim)}

.top{position:sticky;top:0;z-index:5;padding:8px 0;background:var(--bg)}
.screen{padding:6px 8px 6px;border:1px solid var(--line);border-radius:10px;background:var(--bg)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12px;color:var(--dim)}
.sw{display:inline-block;width:16px;height:4px;margin-right:6px;border-radius:2px;vertical-align:middle}
#scope{display:block;width:100%;height:250px}
#fx{min-height:20px;margin-top:2px;font:12px/1.5 var(--mono);color:var(--ink);overflow-wrap:anywhere}
.note{margin-top:2px;padding:5px 10px;border:1px solid var(--warn);border-radius:8px;background:#2a2008;font-size:13px}
.note:empty{display:none}

.ctrl{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}
.a0card{flex:1 1 380px;min-width:0;padding:6px 10px 8px;border:1px solid var(--line);border-radius:10px;background:var(--panel);--c:var(--sum)}
.a0h{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 10px}
.a0h b{font:600 14px var(--mono);color:var(--sum)}
.a0h span{font-size:12px;color:var(--dim)}
.tools{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:6px 10px;border:1px solid var(--line);border-radius:10px;background:var(--panel);font-size:13px}
.tools label{display:flex;align-items:center;gap:4px;cursor:pointer;white-space:nowrap}
.tools input{margin:0;accent-color:var(--mix)}
.btn{padding:6px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bezel);color:var(--ink);font:600 13px var(--sans);white-space:nowrap;cursor:pointer}
.btn:hover{border-color:var(--mix)}
:focus-visible{outline:2px solid var(--mix);outline-offset:2px}

.row{display:grid;grid-template-columns:34px minmax(0,1fr) 60px;align-items:center;gap:8px;margin-top:4px}
.row.z{grid-template-columns:34px minmax(0,1fr) 60px 44px}
.sym{font:600 14px var(--mono);color:var(--c);line-height:1.05}
.sym small{display:block;font:10px var(--mono);color:var(--dim)}
.row input[type=range]{width:100%;margin:0;accent-color:var(--c)}
.row input[type=number]{width:100%;padding:3px 4px;border:1px solid var(--line);border-radius:6px;background:var(--bezel);color:var(--ink);font:13px var(--mono)}
.z0{padding:2px 0;border:1px solid var(--line);border-radius:6px;background:var(--bezel);color:var(--ink);font:600 12px var(--mono);cursor:pointer}
.z0:hover{border-color:var(--sum)}

.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:10px}
.card{min-width:0;padding:6px 8px 8px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.card.off{background:transparent}
.ch{display:flex;align-items:center;justify-content:space-between;gap:6px}
.tg{display:flex;align-items:center;gap:6px;font-weight:600;cursor:pointer}
.tg input{margin:0;accent-color:var(--c)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--c)}
.card.off .dot{background:#3d4d44}
.card.off .tg{color:var(--dim);font-weight:400}
.ok{font-size:11px;color:var(--mix)}
.ok:empty,.card.off .ok{display:none}
.mini{display:block;width:100%;height:64px;margin-top:4px;border-radius:6px}
.body{display:grid;grid-template-columns:minmax(0,1fr) 88px;gap:8px;align-items:center;margin-top:4px}
.card.off .body,.card.off .der{display:none}
.pad{display:block;width:88px;height:88px;border-radius:8px;box-shadow:0 0 0 1px var(--line);cursor:crosshair;touch-action:none}
.der{margin-top:4px;font:11px var(--mono);color:var(--dim);overflow-wrap:anywhere}
.help{margin:10px 2px 0;font-size:12px;color:var(--dim)}

@media (max-width:959px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:699px){
  .chips .chip:nth-child(n+3){display:none}
  #scope{height:150px}
  #fx{display:none}
}
@media (max-width:559px){.grid{grid-template-columns:minmax(0,1fr)}}
@media (max-width:459px){.body{grid-template-columns:minmax(0,1fr)} .pad{margin:0 auto}}
</style>
</head>
<body>
<div id="app">
  <div class="chips">
    <div class="chip a0" title="ค่า a₀ ที่ตั้งไว้ (ยกกราฟทั้งหมดขึ้น/ลง)"><b id="c-a0">0</b><span>a₀</span></div>
    <div class="chip" title="จำนวนเทอม n ที่เปิดอยู่ (n = 1 ถึง 6)"><b id="c-on">0</b><span>เทอมที่เปิด (n)</span></div>
    <div class="chip" title="ค่าสูงสุดของ f(x) ในช่วง x = 0 ถึง 4π"><b id="c-max">-</b><span>f(x) สูงสุด</span></div>
    <div class="chip" title="ค่าต่ำสุดของ f(x) ในช่วง x = 0 ถึง 4π"><b id="c-min">-</b><span>f(x) ต่ำสุด</span></div>
  </div>
  <div class="top">
    <section class="screen" aria-label="จอใหญ่ SANDBOX">
      <div class="legend">
        <span><i class="sw" style="background:#ffb000"></i>f(x) = a₀ + Σ (ผลรวมทุกเทอม)</span>
        <span><i class="sw" style="background:linear-gradient(90deg,#39ff88,#4dd2ff,#ff7ad9)"></i>แต่ละเทอม aₙcos(nx) + bₙsin(nx)</span>
        <span><i class="sw" style="background:repeating-linear-gradient(90deg,#ffb000 0 4px,transparent 4px 7px)"></i>เส้น a₀</span>
      </div>
      <canvas id="scope" role="img" aria-label="กราฟ f(x) ของอนุกรมฟูเรียร์ใน SANDBOX"></canvas>
      <div id="fx"></div>
    </section>
    <div id="note" class="note" role="status" aria-live="polite"></div>
  </div>

  <div class="ctrl">
    <section class="a0card" aria-label="a₀">
      <div class="a0h"><b>a₀</b><span>ยกกราฟทั้งหมดขึ้น/ลง (ในเกม a₀ = 0 เสมอ)</span></div>
      <div class="row z">
        <span class="sym">a₀</span>
        <input id="a0rg" type="range" min="-5" max="5" step="0.1" aria-label="a₀ (ยกกราฟทั้งหมด)">
        <input id="a0nb" type="number" min="-50" max="50" step="0.1" aria-label="a₀ (พิมพ์ค่า)">
        <button id="a0z" class="z0" type="button" title="ตั้ง a₀ = 0 เหมือนในเกม">= 0</button>
      </div>
    </section>
    <div class="tools">
      <label><input type="checkbox" id="showParts" checked>แต่ละเทอม</label>
      <label><input type="checkbox" id="showSum" checked>f(x)</label>
      <label><input type="checkbox" id="showA0" checked>เส้น a₀</label>
      <button id="rand" class="btn" type="button" title="สุ่ม aₙ, bₙ ของเทอมที่เปิดอยู่ (a₀ คงเดิม)">🎲 สุ่ม</button>
      <button id="reset" class="btn" type="button">↺ รีเซ็ต</button>
    </div>
  </div>

  <div id="terms" class="grid"></div>
  <p class="help">จอแสดง x = 0 ถึง 4π เรเดียน และ y = −20 ถึง 20 (คงที่ ไม่ขยายตามกราฟ) · เทอม n วนครบ n รอบทุก 2π · aₙ และ bₙ กำหนดเฟสร่วมกัน: aₙcos(θ) + bₙsin(θ) = R·sin(θ + φ) โดย R = √(aₙ² + bₙ²) และ φ = มุมของจุดบนแผงวงกลม (ลากจุดเพื่อปรับ aₙ, bₙ พร้อมกัน) · ช่องตัวเลขรับค่าได้ถึง ±50</p>
</div>

<script>
(function(){
"use strict";
const NPTS = 1201, NT = 6, PADMAX = 4, TAU = 2 * Math.PI, HARD = 50;
const X_MAX = 4 * Math.PI, Y_LIM = 20, MINI_Y = 5;      // จอใหญ่ล็อกขอบเขตไว้: x = 0 ถึง 4π (เรเดียน), y = −20 ถึง 20
const PALETTE = ["#39ff88","#4dd2ff","#ff7ad9","#ffd24d","#b794ff","#ff8a5c"];
const C = {bg:"#06100b", grid:"#14402a", gridMinor:"#0c2a1b", axis:"#2d7a52", ink:"#9fe3bd", dim:"#4b7d62", sum:"#ffb000"};
const MONO = 'ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace';
const SUB = ["₀","₁","₂","₃","₄","₅","₆"];
const STORE = "allsin.sandbox.v2";
const $ = (s, r) => (r || document).querySelector(s);
const clamp = (v, h) => Math.max(-h, Math.min(h, v));
const minus = t => t.charAt(0) === "-" ? "−" + t.slice(1) : t;
const r2 = v => Math.round(v * 100) / 100;
const fmt = v => minus(String(r2(v)));
const fx2 = v => minus((Math.abs(v) < 0.005 ? 0 : v).toFixed(2));

const X = new Float64Array(NPTS);                       // แกน x: 0 ถึง 4π เรเดียน
for (let j = 0; j < NPTS; j++) X[j] = X_MAX * j / (NPTS - 1);

/* =====================================================================
   INPUT: f(x) = a0 + Σ_{n=1..6} ( a_n cos(n·x) + b_n sin(n·x) )     (x เป็นเรเดียน)
   สถานะ = a0 และ (เปิด/ปิด, a_n, b_n) ของ n = 1..6  จำค่าไว้ในเบราว์เซอร์
   ===================================================================== */
function defaults(){
  return {parts:true, sum:true, base:true, a0:0, terms:[
    {on:true,  a:0,   b:2}, {on:true,  a:1, b:0}, {on:true,  a:0.5, b:0.5},
    {on:false, a:0,   b:1}, {on:false, a:0, b:1}, {on:false, a:0,   b:1}]};
}
function sanitize(o){
  if (!o || !Number.isFinite(o.a0) || !Array.isArray(o.terms) || o.terms.length !== NT) return null;
  const terms = [];
  for (const t of o.terms){
    if (!t || !Number.isFinite(t.a) || !Number.isFinite(t.b)) return null;
    terms.push({on:!!t.on, a:clamp(t.a, HARD), b:clamp(t.b, HARD)});
  }
  return {parts:o.parts !== false, sum:o.sum !== false, base:o.base !== false, a0:clamp(o.a0, HARD), terms};
}
let S = defaults();
try {
  const raw = localStorage.getItem(STORE);
  const saved = raw ? sanitize(JSON.parse(raw)) : null;
  if (saved) S = saved;
} catch (e) { /* ใช้ค่าเริ่มต้นถ้าเบราว์เซอร์ไม่ให้จำค่า */ }
function save(){ try { localStorage.setItem(STORE, JSON.stringify(S)); } catch (e) {} }

/* =====================================================================
   CALCULATION: เทอมที่ n = a_n cos(n·x) + b_n sin(n·x)   ผลรวม = a0 + Σ เทอมที่เปิด
   และแปลง (a_n, b_n) เป็นขนาด R = √(a²+b²) กับเฟส φ ที่ทำให้ a·cosθ + b·sinθ = R·sin(θ + φ)
   ===================================================================== */
let PARTS = [], SUM = new Float64Array(NPTS), ON = 0;
function compute(){
  SUM = new Float64Array(NPTS).fill(S.a0); PARTS = []; ON = 0;
  S.terms.forEach((t, i) => {
    if (!t.on){ PARTS[i] = null; return; }
    ON++;
    const n = i + 1, w = new Float64Array(NPTS);
    for (let j = 0; j < NPTS; j++){
      const th = n * X[j];
      w[j] = t.a * Math.cos(th) + t.b * Math.sin(th);
      SUM[j] += w[j];
    }
    PARTS[i] = w;
  });
}
function polar(t){
  const R = Math.hypot(t.a, t.b);
  if (R < 1e-9) return {R:0, phi:null};
  let phi = Math.atan2(t.a, t.b) * 180 / Math.PI;        // b = R cos φ,  a = R sin φ
  if (phi < 0) phi += 360;
  phi = Math.round(phi * 10) / 10;
  if (phi >= 360) phi -= 360;
  return {R, phi};
}
function gameForm(t){                                     // ถ้าค่านี้ตรงกับที่ลูกบิดในเกมทำได้ จะได้ A กับ φ
  const {R, phi} = polar(t);
  if (phi === null) return null;
  const onAxis = Math.min(Math.abs(t.a), Math.abs(t.b)) < 1e-9;
  const intR = Math.abs(R - Math.round(R)) < 1e-9 && Math.round(R) >= 1 && Math.round(R) <= 3;
  return onAxis && intR ? {A:Math.round(R), phi} : null;
}
const maxAbs = a => { let m = 0; for (let j = 0; j < a.length; j++) m = Math.max(m, Math.abs(a[j])); return m; };
function fixedTicks(lim, step){                          // เส้นกริดแกน y ที่คงที่ ไม่ขยายตามกราฟ
  const ticks = [];
  for (let t = -lim; t <= lim + 1e-9; t += step) ticks.push(t);
  return {ticks, step};
}

/* =====================================================================
   OUTPUT: จอใหญ่ (f(x)) จอเล็กของแต่ละเทอม แผงวงกลมของ (a_n, b_n) ตัวเลขสรุป และข้อความ
   ===================================================================== */
const scope = $("#scope");
function setup(c){
  const r = c.getBoundingClientRect(), d = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
  if (c.width !== Math.round(w * d) || c.height !== Math.round(h * d)){
    c.width = Math.round(w * d); c.height = Math.round(h * d);
  }
  const g = c.getContext("2d");
  g.setTransform(d, 0, 0, d, 0, 0);
  return {g, w, h, shown: r.width > 8 && r.height > 8};   // shown = false ตอนถูกซ่อนอยู่ (เช่น การ์ดปิด หรือหน้า SANDBOX ถูกซ่อน)
}
function frame(g, w, h, pad, ylim, tk, xLabels, fontPx){
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  const x0 = pad.l, x1 = w - pad.r, y0 = pad.t, y1 = h - pad.b;
  const px = x => x0 + x / X_MAX * (x1 - x0);             // x อยู่ในช่วง 0 ถึง 4π
  const py = y => y0 + (1 - (y + ylim) / (2 * ylim)) * (y1 - y0);
  g.lineWidth = 1; g.strokeStyle = C.grid; g.fillStyle = C.ink; g.font = fontPx + "px " + MONO;
  g.textAlign = "right"; g.textBaseline = "middle";
  tk.ticks.forEach(t => {
    const y = py(t);
    g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke();
    g.fillText(tk.step >= 1 ? fmt(t) : minus(t.toFixed(1)), x0 - 4, y);
  });
  for (let q = 0; q <= 8; q++){                           // เส้นกริดทุก π/2 (เส้นหลักทุก π)
    const x = px(q * Math.PI / 2), major = q % 2 === 0;
    g.strokeStyle = major ? C.grid : C.gridMinor;
    g.beginPath(); g.moveTo(x, y0); g.lineTo(x, y1); g.stroke();
    if (xLabels && major){
      g.fillStyle = C.ink;
      g.textAlign = q === 0 ? "left" : (q === 8 ? "right" : "center");
      g.textBaseline = "top"; g.fillText(xLabels[q / 2], x, y1 + 4);
    }
  }
  g.strokeStyle = C.axis; g.beginPath(); g.moveTo(x0, py(0)); g.lineTo(x1, py(0)); g.stroke();
  return {px, py, x0, x1, y0, y1};
}
function curve(g, F, arr, color, lw, alpha){
  g.save();
  g.beginPath(); g.rect(F.x0, F.y0, F.x1 - F.x0, F.y1 - F.y0); g.clip();
  g.beginPath();
  for (let j = 0; j < NPTS; j++){
    const x = F.px(X[j]), y = F.py(arr[j]);
    if (j) g.lineTo(x, y); else g.moveTo(x, y);
  }
  g.globalAlpha = alpha; g.strokeStyle = color; g.lineWidth = lw; g.lineJoin = "round"; g.stroke();
  g.restore();
}
function drawBig(){
  const {g, w, h, shown} = setup(scope);
  if (!shown) return;
  const F = frame(g, w, h, {l:34, r:10, t:8, b:20}, Y_LIM, fixedTicks(Y_LIM, 5), ["0", "π", "2π", "3π", "4π"], 11);
  if (S.base && Math.abs(S.a0) >= 0.005 && Math.abs(S.a0) <= Y_LIM){                  // เส้นประ = ระดับ a0 ที่ยกกราฟทั้งหมดขึ้น/ลง
    const y = F.py(S.a0);
    g.save();
    g.setLineDash([6, 4]); g.strokeStyle = C.sum; g.globalAlpha = 0.6; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(F.x0, y); g.lineTo(F.x1, y); g.stroke();
    g.setLineDash([]); g.globalAlpha = 1; g.fillStyle = C.sum; g.font = "11px " + MONO;
    g.textAlign = "right"; g.textBaseline = S.a0 > 0 ? "bottom" : "top";
    g.fillText("a₀ = " + fmt(S.a0), F.x1 - 4, y + (S.a0 > 0 ? -2 : 2));
    g.restore();
  }
  if (S.parts) PARTS.forEach((a, i) => { if (a) curve(g, F, a, PALETTE[i], 1.4, 0.9); });
  if (S.sum) curve(g, F, SUM, C.sum, 3, 1);
}
function drawMini(i){
  const c = cards[i], t = S.terms[i], {g, w, h, shown} = setup(c.mini);
  if (!shown) return;
  const F = frame(g, w, h, {l:22, r:4, t:3, b:3}, MINI_Y, fixedTicks(MINI_Y, 5), null, 9);
  if (t.on && PARTS[i]) curve(g, F, PARTS[i], PALETTE[i], 2, 1);
  else {
    g.fillStyle = C.dim; g.font = "11px " + MONO; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText("ปิดอยู่", (F.x0 + F.x1) / 2, h / 2);
  }
}
function padGeom(w, h){ return {cx:w / 2, cy:h / 2, r:Math.min(w, h) / 2 - 6}; }
function drawPad(i){
  const c = cards[i], t = S.terms[i], {g, w, h, shown} = setup(c.pad), {cx, cy, r} = padGeom(w, h);
  if (!shown) return;
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  g.lineWidth = 1; g.strokeStyle = C.grid;
  for (let k = 1; k <= PADMAX; k++){ g.beginPath(); g.arc(cx, cy, r * k / PADMAX, 0, TAU); g.stroke(); }
  g.strokeStyle = C.axis;
  g.beginPath(); g.moveTo(cx - r, cy); g.lineTo(cx + r, cy); g.moveTo(cx, cy - r); g.lineTo(cx, cy + r); g.stroke();
  g.fillStyle = C.ink; g.font = "9px " + MONO; g.textBaseline = "middle";
  g.textAlign = "right"; g.fillText("b", w - 2, cy - 7);
  g.textAlign = "left"; g.fillText("a", cx + 3, 7);
  const bx = cx + clamp(t.b, PADMAX) / PADMAX * r, ay = cy - clamp(t.a, PADMAX) / PADMAX * r;
  const {phi} = polar(t), color = PALETTE[i];
  if (t.on && phi !== null){
    g.strokeStyle = color; g.lineWidth = 1.5;
    g.beginPath(); g.arc(cx, cy, 15, 0, -phi * Math.PI / 180, true); g.stroke();   // มุม φ วัดจากแกน b ทวนเข็ม
  }
  g.globalAlpha = t.on ? 1 : 0.35;
  g.strokeStyle = color; g.lineWidth = 2;
  g.beginPath(); g.moveTo(cx, cy); g.lineTo(bx, ay); g.stroke();
  g.fillStyle = color; g.beginPath(); g.arc(bx, ay, 5, 0, TAU); g.fill();
  g.globalAlpha = 1;
}
const arg = n => (n === 1 ? "" : n) + "x";                // ข้างในวงเล็บของ cos/sin: x, 2x, 3x ...
function fxText(){
  const parts = [];
  S.terms.forEach((t, i) => {
    if (!t.on) return;
    if (Math.abs(t.a) >= 0.005) parts.push({v:t.a, s:"cos(" + arg(i + 1) + ")"});
    if (Math.abs(t.b) >= 0.005) parts.push({v:t.b, s:"sin(" + arg(i + 1) + ")"});
  });
  let out = "f(x) = ", first = true;
  if (Math.abs(S.a0) >= 0.005 || !parts.length){ out += fmt(S.a0); first = false; }
  parts.forEach(p => {
    const neg = p.v < 0;
    out += first ? (neg ? "−" : "") : (neg ? " − " : " + ");
    out += r2(Math.abs(p.v)) + "·" + p.s; first = false;
  });
  return out;
}
function renderChips(){
  $("#c-a0").textContent = fmt(S.a0);
  $("#c-on").textContent = ON;
  let mx = -Infinity, mn = Infinity;
  for (let j = 0; j < NPTS; j++){ mx = Math.max(mx, SUM[j]); mn = Math.min(mn, SUM[j]); }
  $("#c-max").textContent = fx2(mx); $("#c-min").textContent = fx2(mn);
  $("#fx").textContent = fxText();
}
function renderNote(){
  const msg = [];
  if (!S.parts && !S.sum) msg.push("ปิดการแสดงผลทั้งสองแบบอยู่ ติ๊ก “แต่ละเทอม” หรือ “f(x)” อย่างน้อย 1 อย่าง");
  else if (ON === 0) msg.push("ยังไม่ได้เปิดเทอม n ใดเลย f(x) จึงเป็นเส้นตรงที่ระดับ a₀ ติ๊กเปิดเทอมที่การ์ดด้านล่าง");
  let m = 0;
  if (S.sum) m = Math.max(m, maxAbs(SUM));
  if (S.parts) PARTS.forEach(a => { if (a) m = Math.max(m, maxAbs(a)); });
  if (m > Y_LIM) msg.push("บางส่วนของกราฟเกินขอบเขต y = ±" + Y_LIM + " จึงถูกตัดออกจากจอ (ดูค่าจริงได้จากช่อง f(x) สูงสุด/ต่ำสุด)");
  $("#note").textContent = msg.join(" · ");
}

/* =====================================================================
   INPUT: a0 (แถบเลื่อน + ช่องตัวเลข) และการ์ดของแต่ละเทอม n (เปิด/ปิด, a_n, b_n, แผงวงกลม)
   ===================================================================== */
const cards = [];
const KEYS = ["a", "b"];
const KEYNAME = {a:"cos", b:"sin"};
function rowHtml(k, n){
  const label = k + SUB[n] + " (สัมประสิทธิ์ของ " + KEYNAME[k] + ", n = " + n + ")";
  return '<div class="row"><span class="sym">' + k + SUB[n] + '<small>' + KEYNAME[k] + '</small></span>' +
    '<input class="rg" type="range" min="-5" max="5" step="0.1" aria-label="' + label + '">' +
    '<input class="nb" type="number" min="' + (-HARD) + '" max="' + HARD + '" step="0.1" aria-label="' + label + ' (พิมพ์ค่า)"></div>';
}
function renderCard(i){                                   // ตั้งตัวควบคุมของการ์ดให้ตรงกับสถานะ แล้ววาดใหม่
  const t = S.terms[i], c = cards[i], {R, phi} = polar(t), g = gameForm(t);
  c.root.classList.toggle("off", !t.on);
  c.on.checked = t.on;
  KEYS.forEach(k => {
    if (document.activeElement !== c.nb[k]) c.nb[k].value = String(r2(t[k]));
    c.rg[k].value = String(t[k]);
  });
  c.der.textContent = phi === null ? "R = 0 (ไม่มีสัญญาณ)" :
    fmt(R) + "·sin(" + arg(i + 1) + " + " + phi + "°) · R = " + fmt(R) + ", φ = " + phi + "°";
  c.ok.textContent = g ? "✓ ใช้ในเกมได้" : "";
  c.ok.title = g ? "ในเกม: A = " + g.A + ", f = " + (i + 1) + ", φ = " + g.phi + "°" : "";
  c.pad.setAttribute("aria-label", "แผงปรับ a" + SUB[i + 1] + " และ b" + SUB[i + 1] + ": a = " + fmt(t.a) + ", b = " + fmt(t.b));
  drawMini(i); drawPad(i);
}
function renderA0(){
  if (document.activeElement !== $("#a0nb")) $("#a0nb").value = String(r2(S.a0));
  $("#a0rg").value = String(S.a0);
}
function afterChange(i){
  compute(); drawBig(); renderChips(); renderNote();
  if (i === undefined) S.terms.forEach((_, n) => renderCard(n)); else renderCard(i);
  renderA0(); save();
}
function syncAll(){
  $("#showParts").checked = S.parts; $("#showSum").checked = S.sum; $("#showA0").checked = S.base;
}
const snapPad = v => { const h = Math.round(v * 2) / 2; return Math.abs(v - h) <= 0.12 ? h : Math.round(v * 10) / 10; };
function buildCards(){
  const host = $("#terms");
  S.terms.forEach((_, i) => {
    const n = i + 1, root = document.createElement("article");
    root.className = "card";
    root.style.setProperty("--c", PALETTE[i]);
    root.innerHTML =
      '<div class="ch"><label class="tg"><input class="on" type="checkbox" aria-label="เปิดเทอม n = ' + n + '">' +
      '<i class="dot"></i><span>n = ' + n + '</span></label><span class="ok"></span></div>' +
      '<canvas class="mini" role="img" aria-label="กราฟของเทอม n = ' + n + '"></canvas>' +
      '<div class="body"><div class="rows">' + KEYS.map(k => rowHtml(k, n)).join("") + '</div>' +
      '<canvas class="pad" tabindex="0" role="application" title="ลากจุดเพื่อปรับ a และ b พร้อมกัน (มุม = เฟส φ)"></canvas></div>' +
      '<div class="der"></div>';
    host.appendChild(root);
    const c = {root, on:$(".on", root), ok:$(".ok", root), mini:$(".mini", root), pad:$(".pad", root),
               der:$(".der", root), rg:{}, nb:{}};
    root.querySelectorAll(".row").forEach((row, q) => { c.rg[KEYS[q]] = $(".rg", row); c.nb[KEYS[q]] = $(".nb", row); });
    cards.push(c);
    c.on.addEventListener("change", () => { S.terms[i].on = c.on.checked; afterChange(i); });
    KEYS.forEach(k => {
      c.rg[k].addEventListener("input", () => {            // ลากแถบเลื่อน: กราฟเปลี่ยนทันที
        S.terms[i][k] = parseFloat(c.rg[k].value); afterChange(i);
      });
      c.nb[k].addEventListener("input", () => {            // พิมพ์ตัวเลข: ใช้ค่าได้เกินช่วงของแถบเลื่อน
        const v = parseFloat(c.nb[k].value);
        if (!Number.isFinite(v)) return;
        S.terms[i][k] = clamp(v, HARD); afterChange(i);
      });
      c.nb[k].addEventListener("change", () => { c.nb[k].blur(); renderCard(i); });   // จัดรูปค่า / ย้อนกลับถ้าว่าง
    });
    // แผงวงกลม: แกนนอน = b (sin) แกนตั้ง = a (cos) มุมของจุด = เฟส φ ระยะจากจุดศูนย์กลาง = R
    let drag = false;
    function aim(e){
      const r = c.pad.getBoundingClientRect(), {r: rad} = padGeom(r.width, r.height);
      const b = snapPad(clamp((e.clientX - (r.left + r.width / 2)) / rad * PADMAX, PADMAX));
      const a = snapPad(clamp(-(e.clientY - (r.top + r.height / 2)) / rad * PADMAX, PADMAX));
      S.terms[i].a = a; S.terms[i].b = b; afterChange(i);
    }
    c.pad.addEventListener("pointerdown", e => { drag = true; c.pad.setPointerCapture(e.pointerId); c.pad.focus({preventScroll:true}); aim(e); });
    c.pad.addEventListener("pointermove", e => { if (drag) aim(e); });
    ["pointerup", "pointercancel"].forEach(t => c.pad.addEventListener(t, () => { drag = false; }));
    c.pad.addEventListener("keydown", e => {
      const step = e.shiftKey ? 1 : 0.1, m = {ArrowRight:["b", 1], ArrowLeft:["b", -1], ArrowUp:["a", 1], ArrowDown:["a", -1]};
      if (!(e.key in m)) return;
      e.preventDefault();
      const [k, s] = m[e.key], t = S.terms[i];
      t[k] = clamp(Math.round((t[k] + s * step) * 10) / 10, HARD);
      afterChange(i);
    });
    c.mini._draw = () => drawMini(i); c.pad._draw = () => drawPad(i);
    ro.observe(c.mini); ro.observe(c.pad);
  });
}

const ro = new ResizeObserver(entries => entries.forEach(e => { if (e.target._draw) e.target._draw(); }));
scope._draw = drawBig; ro.observe(scope);

$("#a0rg").addEventListener("input", () => { S.a0 = parseFloat($("#a0rg").value); afterChange(); });
$("#a0nb").addEventListener("input", () => {
  const v = parseFloat($("#a0nb").value);
  if (Number.isFinite(v)){ S.a0 = clamp(v, HARD); afterChange(); }
});
$("#a0nb").addEventListener("change", () => { $("#a0nb").blur(); renderA0(); });
$("#a0z").addEventListener("click", () => { S.a0 = 0; afterChange(); });
$("#showParts").addEventListener("change", e => { S.parts = e.target.checked; afterChange(); });
$("#showSum").addEventListener("change", e => { S.sum = e.target.checked; afterChange(); });
$("#showA0").addEventListener("change", e => { S.base = e.target.checked; afterChange(); });
$("#reset").addEventListener("click", () => { S = defaults(); syncAll(); afterChange(); });
$("#rand").addEventListener("click", () => {
  const pick = () => Math.floor(Math.random() * 13 - 6) / 2;              // −3 ถึง 3 ทีละ 0.5
  S.terms.forEach(t => {
    if (!t.on) return;
    t.a = pick(); t.b = pick();
    if (Math.random() < 0.5) { if (Math.random() < 0.5) t.a = 0; else t.b = 0; }   // บางครั้งให้เฟสเป็นมุมฉากเหมือนในเกม
    if (t.a === 0 && t.b === 0) t.b = 1;
  });
  afterChange();
});

buildCards();
syncAll();
afterChange();
})();
</script>
</body>
</html>
"""


def embed(html, height):
    """แสดง HTML/JavaScript บนหน้าเว็บ Streamlit ด้วยความสูงที่กำหนด"""
    if hasattr(st, "iframe"):
        # Streamlit รุ่นใหม่: st.components.v1.html ถูกประกาศเลิกใช้ (deprecated) แล้ว
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height, scrolling=True)


def make_board_component():
    """สร้างบอร์ดเกมเป็น Streamlit custom component (สื่อสารสองทาง)

    ปุ่ม 🔄 เริ่มเกมใหม่ และ 🧪 SANDBOX ในหน้าสรุปผลอยู่ในบอร์ด (iframe) จึงต้องส่งค่ากลับมาให้ Python ได้
    ฟังก์ชันนี้เขียน BOARD_HTML ลงโฟลเดอร์ชั่วคราวแล้วลงทะเบียนเป็น component จึงใช้ไฟล์เดียว (app.py) ได้เหมือนเดิม
    ถ้าทำไม่ได้ (เช่น รุ่นเก่า หรือเขียนไฟล์ไม่ได้) จะคืน None แล้วใช้การฝัง HTML ตรง ๆ แทน
    ซึ่งเกมยังเล่นได้ครบ เพียงแต่ปุ่มในหน้าสรุปจะไม่แสดง (ใช้ปุ่มที่แถบด้านซ้ายแทน)
    """
    try:
        import hashlib
        import os
        import tempfile
        import streamlit.components.v1 as components

        html = BOARD_HTML.replace("__GAME_JSON__", "null")      # null = รอรับโจทย์จาก Streamlit
        tag = hashlib.sha256(html.encode("utf-8")).hexdigest()[:10]
        folder = os.path.join(tempfile.gettempdir(), "allsin_board_" + tag)
        page = os.path.join(folder, "index.html")
        if not os.path.exists(page):
            os.makedirs(folder, exist_ok=True)
            tmp = page + ".%d.tmp" % os.getpid()
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(html)
            os.replace(tmp, page)
        return components.declare_component("allsin_board_" + tag, path=folder)
    except Exception:
        return None


BOARD_COMPONENT = make_board_component()


def board_payload(game):
    """ข้อมูลที่ส่งให้บอร์ด: โจทย์ + กติกาคะแนน"""
    payload = {k: game[k] for k in ("id", "components", "hints", "bonus")}
    n = len(game["components"])
    level = DIFFICULTIES[game.get("difficulty", DEFAULT_LEVEL)]
    stage = game.get("stage", 1)
    payload.update(
        stage=stage,
        next_graphs=graphs_for_stage(stage + 1),             # ด่านถัดไปมีกี่กราฟ (ไว้เขียนบนปุ่มหน้าสรุป)
        difficulty=level["label"],
        hint_button=level["hints"],                         # ระดับอาจารย์ = ซ่อนปุ่มคำใบ้
        full_score=FULL_SCORE[n],                           # คะแนนเต็มของเกมนี้ (ขึ้นกับจำนวนกราฟ)
        time_limit=time_limit(n, stage) if level["timer"] else 0,   # เวลาของเกมนี้ (วินาที; ตั้งแต่ด่าน 16 ลดลงด่านละ 10 วิ) 0 = ไม่จับเวลา (ระดับนักเรียน)
        attempt_penalty=ATTEMPT_PENALTY,
        hint_cost=HINT_COST,
        base_total=game.get("base_total", 0),
        base_high=game.get("base_high", 0),
    )
    return payload


def show_board(game):
    """แสดงบอร์ดเกม (HTML/JS) พร้อมโจทย์ คืนค่าเหตุการณ์ล่าสุดที่บอร์ดส่งกลับมา (หรือ None)"""
    payload = board_payload(game)
    if BOARD_COMPONENT is not None:
        # key เปลี่ยนทุกเกม -> เริ่มเกมใหม่จะได้บอร์ดใหม่เอี่ยม
        return BOARD_COMPONENT(game=payload, height=BOARD_HEIGHT, key="board_%d" % game["id"], default=None)
    embed(BOARD_HTML.replace("__GAME_JSON__", json.dumps(payload)), BOARD_HEIGHT)
    return None


def handle_board_event(event, game):
    """รับเหตุการณ์จากบอร์ด: เก็บคะแนน (เกมละครั้ง) และทำตามปุ่มในหน้าสรุปผล

    ชนะ -> คะแนนรวมบวกคะแนนเกมนี้ อัปเดตคะแนนสูงสุดถ้าคะแนนรวมสูงกว่าเดิม และไปด่านถัดไป (ระดับความยากยังล็อกอยู่)
    แพ้ -> คะแนนรวมรีเซ็ตเป็น 0 (คะแนนสูงสุดยังอยู่) กลับไปด่าน 1 และเกมจบ: ปลดล็อกแถบเลือกระดับความยาก
    """
    if not isinstance(event, dict) or event.get("gid") != game["id"]:
        return
    ss = st.session_state
    status = event.get("status")
    if status in ("won", "lost") and ss.get("scored_gid") != game["id"]:
        ss["scored_gid"] = game["id"]
        try:
            attempts, hints = int(event.get("attempts", 0)), int(event.get("hints", 0))
        except (TypeError, ValueError):
            attempts, hints = 0, 0
        # คิดคะแนนใหม่ฝั่ง Python จากจำนวนครั้งที่ส่งและคำใบ้ ไม่เชื่อค่าคะแนนที่บอร์ดบอกมาตรง ๆ
        hints = max(0, min(hints, len(game["bonus"])))
        score = game_score(status, attempts, hints, len(game["components"]))
        ss["last_status"] = status
        if status == "won":
            ss["total_score"] = ss.get("total_score", 0) + score
            ss["high_score"] = max(ss.get("high_score", 0), ss["total_score"])
            ss["stage"] = game.get("stage", 1) + 1          # ผ่านด่าน -> ด่านถัดไป
        else:
            ss["high_score"] = max(ss.get("high_score", 0), ss.get("total_score", 0))
            ss["total_score"] = 0
            ss["stage"] = 1                                 # แพ้ -> กลับไปเริ่มที่ด่าน 1
            ss["run_active"] = False                        # เกมจบ -> เลือกระดับความยากใหม่ได้
            ss["shrink_warned"] = False                     # รอบหน้าถ้าไปถึงด่าน 16 อีกครั้งจะแจ้งเตือนอีกหนึ่งครั้ง
    action, key = event.get("action"), (event.get("gid"), event.get("seq"))
    if action in ("new", "sandbox") and ss.get("handled_event") != key:
        ss["handled_event"] = key              # เหตุการณ์เดิมยังคืนมาอีกในรอบถัดไป จึงต้องกันไม่ให้ทำซ้ำ
        if action == "new":
            request_start()
        else:
            set_mode("sandbox")
        st.rerun()


def show_sandbox():
    """เครื่องสังเคราะห์อนุกรมฟูเรียร์ (ไม่ขึ้นกับโจทย์ ไม่ทำให้เกมรีเซ็ต)"""
    embed(SANDBOX_HTML, SANDBOX_HEIGHT)


def game_running():
    """True ตั้งแต่เริ่มเกมจนเกมจบ (บอร์ดรายงานว่าชนะ/แพ้/หมดเวลาแล้ว) ช่วงนี้ห้ามเข้า SANDBOX
    (ถ้าบอร์ดรายงานกลับมาไม่ได้ เช่นใช้ HTML ฝังตรง ๆ จะไม่ล็อก เพราะไม่รู้ว่าเกมจบเมื่อไร)"""
    ss = st.session_state
    game = ss.get("game")
    return BOARD_COMPONENT is not None and game is not None and ss.get("scored_gid") != game["id"]


def set_mode(mode):
    """สลับหน้าจอหลักระหว่าง "game" กับ "sandbox" (ใช้เป็น callback ของปุ่ม)"""
    if mode == "sandbox" and game_running():
        return                              # ระหว่างเล่นเกมเข้า SANDBOX ไม่ได้
    st.session_state["mode"] = mode


def toggle_sandbox():
    set_mode("game" if st.session_state.get("mode") == "sandbox" else "sandbox")


def box(key):
    """กล่องที่มีชื่อ (key) ไว้ให้ CSS อ้างถึง: Streamlit จะใส่ class "st-key-<key>" ให้"""
    try:
        return st.container(key=key)
    except TypeError:                     # Streamlit รุ่นเก่าไม่มี key: ยังใช้งานได้ แต่แสดงทั้งสองหน้าซ้อนกัน
        return st.container()


def wide_button(label, **kwargs):
    """ปุ่มเต็มความกว้างของแถบด้านซ้าย"""
    try:
        return st.button(label, width="stretch", **kwargs)
    except TypeError:                     # Streamlit รุ่นเก่า
        return st.button(label, use_container_width=True, **kwargs)


def stage_table():
    """ตารางด่านสำหรับข้อความกติกา เช่น 'ด่าน 1–3 = 2 กราฟ · ... · ด่าน 13 ขึ้นไป = 6 กราฟ'"""
    parts = []
    for n in range(MIN_GRAPHS, MAX_GRAPHS + 1):
        first = (n - MIN_GRAPHS) * STAGES_PER_GRAPH + 1
        rng = "ด่าน %d ขึ้นไป" % first if n == MAX_GRAPHS else "ด่าน %d–%d" % (first, first + STAGES_PER_GRAPH - 1)
        parts.append("%s = %d กราฟ" % (rng, n))
    return " · ".join(parts)


def shrink_text():
    """ข้อความอธิบายเรื่องเวลาลดลง ใช้ทั้งในหน้าแจ้งเตือนและในกติกา"""
    n = MAX_GRAPHS
    return ("ตั้งแต่ **ด่านที่ %d** เวลาจะลดลงทุก ๆ **%d วินาที ต่อ 1 ด่าน** "
            "(ด่านที่ %d เหลือ %s, ด่านที่ %d เหลือ %s, ...) "
            "ลดไปเรื่อย ๆ จนเหลือ **%d นาที** ที่ด่านที่ %d แล้วคงที่ %d นาทีไปจนจบเกม"
            % (TIME_SHRINK_FROM, TIME_SHRINK_PER_STAGE,
               TIME_SHRINK_FROM, fmt_time(time_limit(n, TIME_SHRINK_FROM)),
               TIME_SHRINK_FROM + 1, fmt_time(time_limit(n, TIME_SHRINK_FROM + 1)),
               TIME_SHRINK_FLOOR // 60, shrink_end_stage(), TIME_SHRINK_FLOOR // 60))


def show_shrink_notice():
    """หน้าแจ้งเตือนก่อนเข้าด่าน 16: เวลาจะลดลงด่านละ 10 วินาที — แสดง 1 ครั้งต่อรอบ รอกดรับทราบแล้วจึงเริ่มด่าน
    (กดรับทราบแล้วจะไม่แจ้งอีกในด่านถัดไป)"""
    st.warning(
        "**⚠️ แจ้งเตือนก่อนเข้าด่านที่ %d**\n\n%s\n\nข้อความนี้จะแจ้งครั้งเดียว ด่านถัดไปจะไม่แจ้งซ้ำ"
        % (TIME_SHRINK_FROM, shrink_text())
    )
    if st.button("✅ รับทราบ — เริ่มด่านที่ %d" % TIME_SHRINK_FROM, type="primary", key="ack_shrink"):
        ack_shrink_notice()
        st.rerun()


def show_rules():
    full_table =" · ".join("%d กราฟ = %d" % (n, v) for n, v in sorted(FULL_SCORE.items()))
    time_table = " · ".join("%d กราฟ = %d นาที" % (n, time_limit(n) // 60) for n in sorted(FULL_SCORE))
    st.markdown(
        f"""
**วิธีเล่น**
1. กด **เริ่มเกม** ระบบจะสุ่มสัญญาณผสมที่ประกอบด้วยกราฟ sin จำนวน *n* กราฟ ตามด่านที่เล่นอยู่
2. **ด่าน** เริ่มที่ด่าน 1 ซึ่งมีกราฟผสมแค่ {MIN_GRAPHS} กราฟ ผ่านครบทุก {STAGES_PER_GRAPH} ด่านจะเพิ่มกราฟผสม +1 กราฟ (สูงสุด {MAX_GRAPHS} กราฟ): {stage_table()} ถ้าชนะจะได้เล่นด่านถัดไป ถ้าแพ้จะกลับไปเริ่มที่ด่าน 1
3. **ระดับความยาก** เลือกด้วยแถบเลื่อนที่แถบด้านซ้าย เลือกได้ **ก่อนกดเริ่มเกมเท่านั้น** พอกดเริ่มแล้วจะล็อกตลอดทุกด่านจนกว่าเกมจะจบ (แพ้หรือหมดเวลา) จึงเลือกใหม่ได้:
   - **{DIFFICULTIES[0]["label"]}** ไม่จับเวลา และมีปุ่มคำใบ้
   - **{DIFFICULTIES[1]["label"]}** จับเวลา และมีปุ่มคำใบ้
   - **{DIFFICULTIES[2]["label"]}** จับเวลา และไม่มีปุ่มคำใบ้
4. จอเล็กที่ใช้งานได้จะมี *n* จอ ส่วนจอที่เหลือจะขึ้นคำว่า **NO SIGNAL**
5. แต่ละจอมีลูกบิด 3 อัน และแสดงกราฟ y = A·sin(f·x + φ)
   - **แอมพลิจูด A** เป็นจำนวนเต็มตั้งแต่ −3 ถึง 3
   - **ความถี่ f** เป็นจำนวนเต็มตั้งแต่ −3 ถึง 3
   - **เฟส φ** เลือกได้ 0°, 90°, 180° หรือ 270°
6. ผู้ดูแลจะบอกค่าที่ถูกต้องให้แบบสุ่ม (ลูกบิดสีเหลืองที่ล็อก 🔒) ไม่เกิน 2 ค่าต่อจอ (ทุกระดับ)
7. ปุ่ม **💡 ขอคำใบ้เพิ่ม** (ระดับนักเรียนและนิสิต) กดได้ **เท่ากับจำนวนกราฟที่ต้องตอบ** (เช่น 3 กราฟ กดได้ 3 ครั้ง) แต่ละครั้งผู้ดูแลจะบอกค่าที่ถูกต้องเพิ่ม 1 ค่า (สุ่มจากค่าที่ยังไม่รู้) และ **หัก {HINT_COST} คะแนน** ระดับอาจารย์ไม่มีปุ่มนี้
8. จอใหญ่แสดงสัญญาณที่รับได้ (สีเหลือง) ซ้อนกับผลรวมของทุกจอที่คุณจูน (สีเขียว) เป้าหมายคือให้สองเส้นทับกันพอดี (ขอบเขตคงที่: x = 0 ถึง 4π เรเดียน, y = −20 ถึง 20)
9. **⏱ จับเวลาถอยหลัง** (ระดับนิสิตและอาจารย์) เริ่มนับเมื่อกดเริ่มเกม: เวลาพื้นฐาน {TIME_BASE // 60} นาที และ +{TIME_PER_EXTRA_GRAPH // 60} นาทีต่อกราฟที่ต้องตอบเพิ่ม (สูงสุด +{TIME_MAX_EXTRA // 60} นาที): {time_table} เวลา **ไม่มีผลต่อคะแนน** แต่ถ้าเวลาหมดเกมจะ **จบทันที** (นับเป็นแพ้) ระดับนักเรียนไม่จับเวลา
   - **เวลาลดลงเมื่อเล่นไปไกล:** {shrink_text()} (จะมีแจ้งเตือนก่อนเข้าด่านที่ {TIME_SHRINK_FROM} หนึ่งครั้ง)
10. เมื่อมั่นใจแล้วกด **ส่งให้ผู้ดูแลตรวจสอบ** ส่งได้สูงสุด **{MAX_ATTEMPTS} ครั้ง** ผู้ดูแลตรวจจากรูปคลื่น ถ้าได้กราฟเดียวกันก็ถือว่าถูก เช่น A = −1, f = 1, φ = 180° ให้กราฟเดียวกับ A = 1, f = 1, φ = 0°
11. ถ้าส่งแล้วยังไม่ถูก ค่าไหนที่ตรงกับเฉลยแล้วจะ **ถูกล็อกทันที** (ลูกบิดสีเขียว ✓) แล้วคุณปรับค่าที่เหลือเล่นต่อได้
12. **คะแนนเต็ม** ขึ้นกับจำนวนกราฟที่ต้องตอบ: {full_table}
   - ถูกหมดตั้งแต่ครั้งที่ 1 ได้ **เต็ม − จำนวนครั้งที่กดคำใบ้**
   - ถูกหมดในครั้งที่ 2 ได้ **เต็ม − {ATTEMPT_PENALTY[1]} − จำนวนครั้งที่กดคำใบ้**
   - ถูกหมดในครั้งที่ 3 ได้ **เต็ม − {ATTEMPT_PENALTY[2]} − จำนวนครั้งที่กดคำใบ้**
13. ชนะแล้วคะแนนจะ **สะสมเป็นคะแนนรวม** และได้เล่นด่านถัดไป แต่ถ้าส่งครบ {MAX_ATTEMPTS} ครั้งแล้วยังไม่ถูก หรือเวลาหมด คุณจะแพ้: **คะแนนรวมรีเซ็ตเป็น 0 และกลับไปด่าน 1** (ระบบยังเก็บ **⭐ คะแนนสูงสุด** ไว้ให้) พร้อมสรุปผล เฉลยที่ถูกต้อง และปุ่ม **🔄 เริ่มเกมใหม่** กับ **🧪 SANDBOX**

อยากลองเล่นกับกราฟก่อน? กดปุ่ม **🧪 SANDBOX** ด้านซ้าย จอหลักจะเปลี่ยนเป็นเครื่องสังเคราะห์อนุกรมฟูเรียร์ ปรับ a₀, aₙ, bₙ ของแต่ละ n ได้ตามใจ
ปุ่มนี้ใช้ได้ **ก่อนเริ่มเกมและหลังเกมจบเท่านั้น** ตั้งแต่เริ่มเกมจนเกมจบปุ่มจะถูกล็อก
"""
    )


SANDBOX_HELP = r"""
- **a₀** ยกกราฟทั้งหมดขึ้นหรือลง (เลื่อนในแนวตั้ง) ในเกม a₀ เท่ากับ 0 เสมอ แต่ใน SANDBOX ปรับได้
- **n** (1 ถึง 6) เป็นความถี่ของแต่ละเทอม: cos(nx) และ sin(nx) วนครบ n รอบทุก 2π
  เกมผสมกราฟได้สูงสุด 6 กราฟ จึงมีเทอม n = 1 ถึง 6 (ความถี่ f ของลูกบิดในเกมก็คือ n)
- **aₙ, bₙ** เป็นสัมประสิทธิ์ของ cos และ sin ของเทอมที่ n สองค่านี้กำหนด **เฟส** ของคลื่นร่วมกัน
  (และขนาดของคลื่นด้วย): ลากจุดบนแผงวงกลม มุมของจุดคือเฟส φ ระยะจากกลางวงคือขนาด R
- **ขอบเขตของจอ** คงที่เสมอ: x = 0 ถึง 4π เรเดียน (2 คาบของ n = 1), y = −20 ถึง 20
- ในที่นี้ x วัดเป็นเรเดียน ถ้าวัด x เป็นจำนวนคาบ (t = x/2π) จะเขียนเทอมเดียวกันเป็น cos(2πnt) และ sin(2πnt)
  ซึ่งเป็นอนุกรมฟูเรียร์ชุดเดียวกัน
"""


# =====================================================================
# ส่วนที่ 2: หน้าเว็บ Streamlit (ปุ่มเริ่มเกม + แสดงบอร์ด + SANDBOX)
# =====================================================================
st.set_page_config(page_title="ALLSIN", page_icon="📡", layout="wide")

if st.session_state.get("mode") == "sandbox" and game_running():
    st.session_state["mode"] = "game"       # กันไว้: ระหว่างเล่นเกมต้องอยู่ที่หน้าเกมเสมอ
has_game = "game" in st.session_state
sandbox_on = st.session_state.get("mode") == "sandbox"

# หน้าเกมกับหน้า SANDBOX ถูกสร้างไว้ทั้งคู่ แล้วใช้ CSS ซ่อนหน้าที่ไม่ได้ดูอยู่
# (ไม่ถอดออกจากหน้าเว็บ) เพื่อให้ลูกบิด คำใบ้ และจำนวนครั้งที่ส่งตรวจของเกมอยู่ครบเมื่อสลับกลับมา
st.markdown(
    "<style>.st-key-%s{display:none}</style>" % ("board_box" if sandbox_on else "sandbox_box"),
    unsafe_allow_html=True,
)
board_page = box("board_box")          # สร้างกล่องไว้ก่อน เติมเนื้อหาทีหลัง (ลำดับบนหน้าเว็บไม่เปลี่ยน)
sandbox_page = box("sandbox_box")

# ---- หน้าเกม: ต้องวาดบอร์ดก่อนแถบด้านซ้าย เพื่อให้คะแนนรวมที่แถบด้านซ้ายเป็นค่าล่าสุดเสมอ ----
with board_page:
    st.title("📡 ALLSIN")
    if has_game and st.session_state.get("shrink_notice"):
        show_shrink_notice()               # ก่อนเข้าด่าน 16: แจ้งเรื่องเวลาที่จะลดลง รอกดรับทราบ (ยังไม่เริ่มด่าน)
    elif has_game:
        board_event = show_board(st.session_state["game"])
        handle_board_event(board_event, st.session_state["game"])    # เก็บคะแนน / ทำตามปุ่มในหน้าสรุป
    else:
        # ยังไม่เริ่มเกม: แสดงเรื่องราวและกติกา รอผู้เล่นกดเริ่ม
        st.markdown(
            "คุณคือ **นายวิทยุ** ประจำสถานีรับสัญญาณ คืนนี้เสาอากาศจับสัญญาณปริศนาจากอวกาศได้ "
            "สัญญาณนี้เป็นคลื่นผสมของกราฟ sin หลายตัว ตามอนุกรมฟูเรียร์"
        )
        st.latex(r"f(x)=a_0+\sum_{n=1}^{\infty}\left(a_n\cos(nx)+b_n\sin(nx)\right)")
        st.markdown(
            "งานของคุณคือ **แยกสัญญาณผสมออกมาเป็นกราฟ sin ให้ครบทุกตัว** "
            "ด้วยเครื่องจูน 6 จอ แล้วส่งให้ผู้ดูแลตรวจสอบ"
        )
        show_rules()
        if st.button("▶ เริ่มเกม", type="primary", key="start_main"):
            request_start()
            st.rerun()

playing = game_running()               # ด่านนี้กำลังเล่นอยู่ (ยังไม่จบ) -> SANDBOX ถูกล็อก
game_over = has_game and BOARD_COMPONENT is not None and not playing
stage_now = st.session_state.get("stage", 1)
level_locked = run_locked()            # ทั้งรอบ (ทุกด่านจนกว่าจะแพ้) -> ระดับความยากถูกล็อก

with st.sidebar:
    st.header("📡 ALLSIN")
    st.caption("เกมนายวิทยุ: แยกสัญญาณผสมให้เป็นกราฟ sin")
    if not has_game:
        start_label = "▶ เริ่มเกม"
    elif not game_over:
        start_label = "🔄 เริ่มเกมใหม่"               # กดกลางเกม = สุ่มโจทย์ใหม่ในด่านเดิม (ไม่ถือว่าแพ้)
    elif st.session_state.get("last_status") == "won":
        start_label = "➡ ด่านถัดไป"
    else:
        start_label = "🔄 เริ่มใหม่ (กลับไปด่าน 1)"
    if st.button(start_label, key="start_side"):
        request_start()
        st.rerun()
    # ระดับความยาก: แถบเลื่อน 3 ระดับ เลือกได้ก่อนกดเริ่มเกมเท่านั้น กดเริ่มแล้วล็อกตลอดทุกด่านจนกว่าเกมจะจบ (แพ้/หมดเวลา)
    level_labels = [d["label"] for d in DIFFICULTIES]
    chosen = st.select_slider("ระดับความยาก", options=level_labels, value=level_labels[DEFAULT_LEVEL], key="difficulty",
                              disabled=level_locked,
                              help="เลือกก่อนกดเริ่มเกม พอกดเริ่มแล้วจะเปลี่ยนไม่ได้ตลอดทุกด่านจนกว่าเกมจะจบ แล้วจึงเลือกใหม่ได้")
    level = DIFFICULTIES[current_level()]
    st.caption(("⏱ จับเวลา" if level["timer"] else "⏱ ไม่จับเวลา") + " · " +
               ("💡 มีปุ่มคำใบ้" if level["hints"] else "🚫 ไม่มีปุ่มคำใบ้") +
               (" · 🔒 ล็อกจนกว่าเกมจะจบ" if level_locked else ""))
    if BOARD_COMPONENT is not None:
        st.metric("🎯 ด่านถัดไป" if game_over else "🎯 ด่าน", stage_now,
                  help="ผ่านครบทุก %d ด่านจะเพิ่มกราฟผสม +1 (สูงสุด %d กราฟ) ถ้าแพ้จะกลับไปด่าน 1" % (STAGES_PER_GRAPH, MAX_GRAPHS))
        n_now = graphs_for_stage(stage_now)
        st.caption("ด่านนี้มีกราฟผสม %d กราฟ" % n_now + (" · ⏱ เวลา %s" % fmt_time(time_limit(n_now, stage_now)) if level["timer"] else ""))
        st.metric("🏆 คะแนนรวม", st.session_state.get("total_score", 0),
                  help="รวมคะแนนของเกมที่ชนะต่อเนื่องกัน ถ้าแพ้จะรีเซ็ตเป็น 0 (กดเริ่มเกมใหม่กลางเกมไม่ถือว่าแพ้)")
        st.metric("⭐ คะแนนสูงสุด", st.session_state.get("high_score", 0),
                  help="คะแนนรวมที่สูงที่สุดที่ทำได้ ไม่ถูกรีเซ็ตเมื่อแพ้ (ถ้ารีเฟรชหน้าเว็บจะเริ่มนับใหม่)")
    # (กติกา/วิธีเล่นอยู่ที่จอหลักหน้าแรกแล้ว จึงไม่มีตัวขยาย "วิธีเล่น" ที่แถบด้านซ้าย)
    # ปุ่ม SANDBOX: กดแล้วจอหลักเปลี่ยนเป็น SANDBOX กดอีกครั้งเพื่อกลับไปที่เกม
    sandbox_locked = playing
    wide_button("🧪 SANDBOX", key="sandbox_toggle", on_click=toggle_sandbox,
                type="primary" if sandbox_on else "secondary", disabled=sandbox_locked,
                help="ล็อกอยู่ระหว่างเล่นเกม ใช้ได้เมื่อเกมจบ" if sandbox_locked else None)
    st.caption(
        "🔒 ล็อกอยู่ระหว่างเล่นเกม จะใช้ได้เมื่อเกมจบ" if sandbox_locked
        else "กำลังแสดง SANDBOX บนจอใหญ่ · กดอีกครั้งเพื่อกลับไปหน้าเกม" if sandbox_on
        else "ทดลองปรับอนุกรมฟูเรียร์บนจอใหญ่ (ใช้ได้ก่อนเริ่มเกมและหลังเกมจบ)"
    )

with sandbox_page:
    st.title("🧪 SANDBOX")
    st.latex(r"f(x)=a_0+\sum_{n=1}^{6}\left(a_n\cos(nx)+b_n\sin(nx)\right)")
    if has_game:
        st.button("🎮 กลับไปหน้าเกม", key="back_game", on_click=set_mode, args=("game",))
    else:
        st.button("▶ ไปเริ่มเกม", key="back_start", on_click=set_mode, args=("game",))
    show_sandbox()
    with st.expander("📖 ความหมายของพารามิเตอร์", expanded=False):
        st.markdown(SANDBOX_HELP)