# =====================================================================
# SINALL  -  นายวิทยุถอดรหัสสัญญาณผสมจากอวกาศ   (เดิมชื่อ ALLSIN)
#
# โครงสร้างตามเอกสาร Streamlit:  INPUT -> CALCULATION -> OUTPUT
#
# ทำไมบอร์ดเกมจึงเป็น HTML/JavaScript?
#   widget ของ Streamlit ทุกตัวสั่งให้เซิร์ฟเวอร์รันสคริปต์ใหม่ทั้งไฟล์ จึงมีหน่วงและกะพริบ
#   เมื่อหมุนลูกบิด เพื่อให้ปรับค่าแล้วเห็นผลทันที (real-time) บอร์ดเกมจึงทำงานในเบราว์เซอร์
#   ส่วน Streamlit ทำหน้าที่: สุ่มโจทย์ด้วย Python, ปุ่มเริ่มเกม, หน้าเว็บ และการ deploy
#
#   ส่วนที่ 1  Python : make_game()   สุ่มสัญญาณผสม คำใบ้ และคำใบ้เพิ่ม
#   ส่วนที่ 2  Python : หน้าเว็บ (หน้าแรก / หน้าเกม / SANDBOX / Tutorial) ส่งโจทย์ให้บอร์ด + เก็บคะแนนรวมและคะแนนสูงสุดแยกตามระดับ
#   ส่วนที่ 3  JS     : BOARD_HTML    ลูกบิด (INPUT) -> รวมคลื่น/ตรวจคำตอบ/ให้คะแนน (CALCULATION)
#                                      -> จอใหญ่/จอเล็ก/หน้าสรุปผล (OUTPUT)
#
# กติกาการส่งตรวจและคะแนน (ค่าคงที่ FULL_SCORE, ATTEMPT_PENALTY, HINT_COST ด้านล่าง ปรับตัวเลขได้ที่นั่น):
#   - คะแนนเต็มของเกมขึ้นกับจำนวนกราฟที่ต้องตอบ: 2 กราฟ = 10, 3 = 12, 4 = 14, 5 = 16, 6 = 18
#   - ส่งตรวจได้สูงสุด 3 ครั้ง ถูกหมดครั้งที่ 1 ได้ เต็ม − คำใบ้ / ครั้งที่ 2 ได้ เต็ม − 2 − คำใบ้ / ครั้งที่ 3 ได้ เต็ม − 4 − คำใบ้
#   - หลังส่งแล้วยังผิด ค่าไหนตรงเฉลยลูกบิดนั้นจะเรืองแสงวาบหนึ่ง (เหมือนตอนขอคำใบ้) แล้วถูกล็อกทันที (ล็อกแบบเดียวกับคำใบ้เริ่มต้น: ลูกบิดสีเหลือง 🔒) เล่นต่อได้
#     ส่วนค่าที่ยังไม่ถูก ขีดบนลูกบิดจะเป็นสีแดง และจำค่าผิดไว้ หมุนไปมาแล้วกลับมาชี้ค่าผิดเดิมก็เป็นขีดแดงอีก (markWrong)
#   - คำใบ้ (ปุ่ม 💡) กดครั้งละ 1 ค่า หัก 1 คะแนนต่อครั้ง จำนวนครั้งเป็นคำใบ้สะสมของรอบ (session_state: hint_pool):
#     เริ่มรอบตาม start_hints ของระดับ (ง่าย 2 / ปานกลาง 3 / ยาก 5) ผ่านด่านได้เพิ่ม +1 (HINT_PER_STAGE) สะสมได้ไม่จำกัด
#     คำใบ้ที่ใช้ไปแล้วหมดไป ขึ้นด่านใหม่ไม่รีเซ็ต เหลือเท่าที่สะสมไว้ (แพ้/กลับหน้าแรกแล้วเริ่มนับใหม่)
#   - ชนะ: คะแนนรวมสะสมต่อเกมถัดไป  /  แพ้ (ส่งครบ 3 ครั้งไม่ถูก หรือหมดเวลา): คะแนนรวมรีเซ็ตเป็น 0 แต่เก็บคะแนนสูงสุดของระดับนั้นไว้
#     และสรุปผล + เฉลย + ปุ่มเริ่มเกมใหม่ / SANDBOX
#   - จับเวลาถอยหลัง: 2 นาที (2 กราฟ) + 1 นาทีต่อกราฟที่เพิ่ม สูงสุด +4 นาที (TIME_* ด้านล่าง)
#     เวลาไม่มีผลต่อคะแนน แต่หมดเวลาเกมจบทันที (นับเป็นแพ้)
#   - ปุ่ม SANDBOX (หน้าแรกและแผงควบคุมบนหน้าเกม) ถูกล็อกตั้งแต่เริ่มเกมจนเกมจบ
#   - กดเริ่มเกมแล้วสุ่มโจทย์ใหม่ (รีโรล) ไม่ได้: ปุ่มเริ่มเกมบนหน้าเกมถูกล็อกจนเกมจบ และ request_start()/new_game()
#     ไม่ทำงานระหว่างเล่น (เช็กด้วย game_running())
#   - ปุ่ม 🏠 กลับหน้าแรก (แผงควบคุมบนหน้าเกม) -> go_home(): จบรอบทั้งรอบ คะแนนรวมรีเซ็ตเป็น 0 กลับไปด่าน 1
#     เก็บคะแนนสูงสุดของระดับนั้นไว้ ปลดล็อกระดับความยาก ถ้ากดกลางเกมนับเป็นแพ้ (ไม่งั้นจะเป็นช่องรีโรล) ต้องกดยืนยันก่อน
#   - ด่าน: เริ่มที่ด่าน 1 มีกราฟผสม 2 กราฟ ผ่านครบทุก 3 ด่านเพิ่มอีก 1 กราฟ (สูงสุด 6) ชนะ = ไปด่านถัดไป แพ้ = กลับด่าน 1
#   - ระดับความยาก (แถบเลื่อนบนแผงควบคุมหน้าเกม): เลือกได้ก่อนกดเริ่มเกมเท่านั้น พอกดเริ่มแล้วจะล็อกตลอดทุกด่านของรอบนั้น
#     จนกว่าเกมจะจบ (แพ้/หมดเวลา) จึงเลือกใหม่ได้ (session_state: run_active / run_level)
#       แต่ละระดับต่างกันที่ช่วงของลูกบิดแอมพลิจูด A และความถี่ f (จำนวนเต็ม [-max, max] ยกเว้น 0 เฟสเหมือนเดิม) และคำใบ้เริ่มต้น
#       (ดู DIFFICULTIES; โจทย์ที่สุ่มก็อยู่ในช่วงเดียวกัน):
#       นักเรียน (ง่าย) ไม่จับเวลา ±3 คำใบ้ 2 / นิสิต (ปานกลาง) จับเวลา ±5 คำใบ้ 3 / อาจารย์ (ยาก) จับเวลา ±10 คำใบ้ 5
#   - เวลาลดลงตั้งแต่ด่าน 16: ด่านละ 10 วินาที (TIME_SHRINK_*) จนเหลือ 3 นาที แล้วคงที่ (เฉพาะระดับที่จับเวลา)
#     ก่อนเข้าด่าน 16 มีหน้าแจ้งเตือนให้กดรับทราบ 1 ครั้งต่อรอบ (ด่านถัดไปไม่แจ้งซ้ำ) -> show_shrink_notice()
#   - ปุ่มในหน้าสรุปอยู่ในบอร์ด (iframe) จึงส่งคำสั่งกลับมาหา Python ผ่าน Streamlit custom component
#   ส่วนเสริม  JS     : SANDBOX_HTML  กดปุ่ม 🧪 SANDBOX (หน้าแรก/หน้าเกม) แล้วจอหลักจะเปลี่ยนเป็น
#                                      เครื่องสังเคราะห์อนุกรมฟูเรียร์ ปรับพารามิเตอร์ของสูตร
#                                      f(x) = a0 + Σ_{n=1..6} ( a_n cos(n·x) + b_n sin(n·x) )
#                                        a0       ยกกราฟทั้งหมดขึ้น/ลง (ในเกมเท่ากับ 0 เสมอ)
#                                        n        ความถี่ของแต่ละเทอม (เกมผสมได้สูงสุด 6 กราฟ จึงใช้ n = 1..6)
#                                        a_n,b_n  ตัวกำหนดเฟสของเทอมนั้น: a cosθ + b sinθ = R·sin(θ + φ)
#                                      x วัดเป็นเรเดียน (ถ้าวัด x เป็นจำนวนคาบ t = x/2π จะได้ cos(2πnt) ตามสูตรเดิม)
#                                      (บอร์ดเกมกับ SANDBOX อยู่บนหน้าเดียวกัน สลับดูได้โดยเกมไม่หาย)
#
# หน้าเว็บ (st.session_state["mode"]):
#   home     หน้าแรก: กราฟตัวอักษร SINALL จากอนุกรมฟูเรียร์ (HOME_HTML, letters_data()) + แถบเลื่อนจำนวนเทอม N เพียงอันเดียว
#            + ปุ่ม เริ่มเกม / กติกา / SANDBOX  ข้อความกติกา (show_story + show_rules) โผล่เมื่อกดปุ่ม กติกา เท่านั้น
#   game     หน้าเกม: แผงควบคุม (ระดับความยาก ด่าน คำใบ้สะสม คะแนนรวม ปุ่มเริ่ม/ด่านถัดไป 🏠 กลับหน้าแรก 🧪 SANDBOX) + บอร์ดเกม
#   sandbox  เครื่องสังเคราะห์อนุกรมฟูเรียร์ (ปุ่มกลับไปยังหน้าที่เข้ามา)
#   tutorial ด่านลองเล่นบนบอร์ดจริงที่มีไกด์พาทำทีละขั้น: ลอยติดกับส่วนที่ไฮไลต์ รอให้ลองหมุนลูกบิด ขอคำใบ้ ส่งตรวจจริง (คะแนนไม่นับ)
#            หลังกดเริ่มเกมครั้งแรกจะถามว่าอยากดูไหม ถามครั้งเดียวจนกว่าจะรีเฟรชหน้าเว็บ (tutorial_asked) ดูซ้ำได้จากหน้ากติกา
#   แถบด้านซ้าย: แสดงเฉพาะ ⭐ คะแนนสูงสุดของแต่ละระดับความยาก (high_scores) เริ่มนับใหม่เมื่อรีเฟรชหน้าเว็บ
#
# ขอบเขตของจอใหญ่: แกน x คงที่เสมอ 0 ถึง 4π เรเดียน (ค่าคงที่ X_MAX ต้นสคริปต์ JavaScript ทั้งสองส่วน)
#   - เกม: แกน y ตรึงไว้ตลอดด่านตามกราฟปริศนาของด่านนั้น = (ค่าต่ำสุด − 1) ถึง (ค่าสูงสุด + 1) เช่น สูงสุด 10 ต่ำสุด −5 -> −6 ถึง 11
#          (Y_TOP / Y_BOT ในบอร์ด)
#          จอเล็กแต่ละจอตรึงแกน y ด้วยกฎเดียวกัน แต่ใช้กราฟเฉลยของจอนั้น (SMALL_Y ในบอร์ด) = (ต่ำสุด − 1) ถึง (สูงสุด + 1)
#          เช่น เฉลยของจอนั้นคือ A = 3 -> y = −4 ถึง 4  (หมายเหตุ: ขอบเขตนี้บอกขนาด |A| ของจอนั้นไปในตัว)
#   - SANDBOX: จอใหญ่ y = −20 ถึง 20 (Y_LIM ใน SANDBOX_HTML)
#              จอเล็กของแต่ละเทอมตรึง y = −(10√2 + 1) ถึง 10√2 + 1 ≈ ±15.14 (MINI_Y) ตามค่าสูงสุดที่เทอมหนึ่งเป็นไปได้
#              เมื่อ a₀, aₙ, bₙ ปรับได้ −10 ถึง 10 ทีละ 0.01 (HARD ใน SANDBOX_HTML)
#
# รัน:  python -m streamlit run app.py
# =====================================================================

import json
import random
import string

import numpy as np
import streamlit as st

# ---------------------------------------------------------------------
# ค่าคงที่ของเกม
# ---------------------------------------------------------------------
N_SCREENS = 6                       # จำนวนจอเล็กทั้งหมด
KNOBS = ("amp", "freq", "phase")    # ลูกบิด 3 ลูกของแต่ละจอ
PHASES = [0, 90, 180, 270]          # ค่าเฟสที่ปรับได้ (องศา)
FULL_SCORE = {2: 10, 3: 12, 4: 14, 5: 16, 6: 18}   # คะแนนเต็มของเกม ขึ้นกับจำนวนกราฟที่ต้องตอบ (กราฟละ +2)
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
# ระดับความยาก (เรียงจากง่ายไปยาก) เลือกด้วยแถบเลื่อนบนแผงควบคุมหน้าเกม
# amp_max / freq_max: แอมพลิจูด A และความถี่ f ที่ลูกบิดปรับได้ = จำนวนเต็ม [-max, max] ยกเว้น 0 (เฟสปรับได้ 0/90/180/270 เหมือนกันทุกระดับ)
#                     โจทย์ที่สุ่มก็อยู่ในช่วงนี้ (A ไม่เกิน amp_max และความถี่ไม่เกิน freq_max)
# start_hints: จำนวนคำใบ้ (ปุ่ม 💡) ตอนเริ่มรอบ ผ่านด่านแล้ว +HINT_PER_STAGE ที่เหลือสะสมต่อไปด่านถัดไป
DIFFICULTIES = [
    {"label": "นักเรียน (ง่าย)", "timer": False, "hints": True, "amp_max": 3, "freq_max": 3, "start_hints": 2},     # ไม่จับเวลา
    {"label": "นิสิต (ปานกลาง)", "timer": True, "hints": True, "amp_max": 5, "freq_max": 5, "start_hints": 3},      # จับเวลา
    {"label": "อาจารย์ (ยาก)", "timer": True, "hints": True, "amp_max": 10, "freq_max": 10, "start_hints": 5},      # จับเวลา
]
HINT_PER_STAGE = 1                  # ทุกครั้งที่ผ่านด่านได้คำใบ้เพิ่ม 1 ครั้ง (สะสมได้เรื่อย ๆ ไม่มีเพดาน)
DEFAULT_LEVEL = 1                   # เริ่มต้นที่ระดับ นิสิต (ปานกลาง)
BOARD_HEIGHT = 900                  # ความสูงของบอร์ดเกม (px)
SANDBOX_HEIGHT = 840                # ความสูงของ SANDBOX บนจอหลัก (px)
HOME_HEIGHT = 300                   # ความสูงของกราฟ SINALL + แถบเลื่อนบนหน้าแรก (px)
# กราฟตัวอักษร SINALL บนหน้าแรก: ตัวอักษรละ 1 เส้นโค้งปิด (S I N A L L) เขียนด้วยอนุกรมฟูเรียร์ของ x(t), y(t) ดู letters_data()
LETTER_N = 30                       # จำนวนเทอม (ฮาร์มอนิก) สูงสุดต่อตัวอักษร = ค่ามากสุดของแถบเลื่อนบนหน้าแรก
LETTER_N0 = 9.0                     # ความกว้างของหน้าต่าง Gaussian exp(-(n/n0)²/2) ที่ทำให้มุมของตัวอักษรโค้งมน
LETTER_H = 2.0                      # ความสูงของตัวอักษร
LETTER_GAP = 0.35                   # ช่องว่างระหว่างตัวอักษร
LETTER_SAMPLES = 4096               # จำนวนจุดต่อตัวอักษรที่ใช้ทำ FFT
LETTER_DEC = 5                      # จำนวนทศนิยมของสัมประสิทธิ์
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


def wave(amp, freq, phase):
    """กราฟ sin หนึ่งจอ:  y = A * sin(f * x + phase)   (f ตรงกับ n ในอนุกรมฟูเรียร์)"""
    return amp * np.sin(freq * X + np.radians(phase))


def equivalent_settings(kind, k, c):
    """ทุกชุดลูกบิด (A, f, φ) ที่ให้กราฟเดียวกับ c·sin(kx) (kind = "sin") หรือ c·cos(kx) (kind = "cos")
    เมื่อ φ เป็นได้แค่ 0/90/180/270: sin(fx + φ) เหลือเพียง ±sin(kx) หรือ ±cos(kx) ตามตารางนี้ (f = ±k)
        φ = 0° -> sin(fx)   φ = 90° -> cos(kx)   φ = 180° -> −sin(fx)   φ = 270° -> −cos(kx)   (sin(−kx) = −sin(kx))
    จึงมีให้เลือก 4 ชุดเสมอ (f = +k หรือ −k, φ อีก 2 ค่า) และ |A| = |c| ไม่เกินช่วงของแอมพลิจูดเสมอ
    (เขียนเป็นสูตรตรง ๆ แทนการไล่ลองทุกชุดแล้วเทียบกราฟ เพราะช่วงลูกบิดกว้างถึง ±10 ซึ่งช้าลงมาก)"""
    options = []
    for f in (k, -k):
        s = 1 if f > 0 else -1
        if kind == "sin":
            options.append({"amp": c * s, "freq": f, "phase": 0})
            options.append({"amp": -c * s, "freq": f, "phase": 180})
        else:
            options.append({"amp": c, "freq": f, "phase": 90})
            options.append({"amp": -c, "freq": f, "phase": 270})
    return options


def make_game(game_id, n=None, hint_button=True, amp_max=3, freq_max=3):
    """สุ่มสัญญาณผสม 1 สัญญาณ (n กราฟ; ไม่ระบุ = สุ่ม 2-6) พร้อมคำใบ้เริ่มต้นและลำดับคำใบ้เพิ่ม
    amp_max / freq_max = ช่วงของแอมพลิจูดและความถี่ของระดับที่เล่น (จำนวนเต็ม [-max, max] ยกเว้น 0)
    hint_button=False = ไม่มีปุ่มคำใบ้เพิ่ม คงเหลือเฉพาะคำใบ้เริ่มต้นจากผู้ดูแล

    หลักการ: sin(fx+φ) ที่ φ = 0/90/180/270 ให้ได้เพียง ±A·sin(kx) หรือ ±A·cos(kx)
    โดย k = |f| = 1 ถึง freq_max จึงมี "ช่อง" ที่ไม่ซ้ำกันอยู่ 2·freq_max ช่อง
    (sin1, cos1, sin2, cos2, ... ง่าย 6 ช่อง / ปานกลาง 10 ช่อง / ยาก 20 ช่อง) แต่ละกราฟที่ซ่อนอยู่จะใช้คนละช่อง
    ผลคือสัญญาณผสมแยกเป็นกราฟ sin ได้แบบเดียวเท่านั้น (ตรงกับอนุกรมฟูเรียร์)
    """
    rng = random.Random()
    if n is None:
        n = rng.randint(MIN_GRAPHS, MAX_GRAPHS)

    amps = [a for a in range(-amp_max, amp_max + 1) if a != 0]
    slots = [(k, kind) for k in range(1, freq_max + 1) for kind in ("sin", "cos")]
    n = min(n, len(slots))
    # แต่ละช่องสุ่มขนาด c แล้วสุ่มชุดลูกบิดหนึ่งชุดจากทุกชุดที่ให้กราฟเดียวกัน
    components = [rng.choice(equivalent_settings(kind, k, rng.choice(amps))) for k, kind in rng.sample(slots, n)]

    # คำใบ้เริ่มต้น: ผู้ดูแลให้ค่าที่ถูกต้องแบบสุ่ม จอละ 0-2 ค่า (ไม่เกิน 2) ล็อกไว้ตั้งแต่เริ่มด่าน
    hints = [rng.sample(KNOBS, rng.choice([0, 1, 1, 2, 2])) for _ in components]
    if not any(hints):                      # อย่างน้อยให้คำใบ้ 1 ค่า
        hints[0] = [rng.choice(KNOBS)]

    # ลำดับคำใบ้เพิ่ม (ปุ่ม 💡): สับค่าที่ผู้ดูแลยังไม่ได้บอกทั้งหมด กดแต่ละครั้งบอกค่าถัดไปในลำดับ 1 ค่า
    # จำนวนครั้งที่กดได้ไม่ได้อยู่ที่นี่ แต่เป็นคำใบ้สะสมของรอบ (hint_pool) ที่ new_game ใส่ให้
    hidden = [(i, k) for i in range(n) for k in KNOBS if k not in hints[i]]
    bonus = [list(p) for p in rng.sample(hidden, len(hidden))] if hint_button else []

    return {"id": game_id, "components": components, "hints": hints, "bonus": bonus}


def run_locked():
    """True ตั้งแต่กดเริ่มเกมจนกว่าเกมจะจบ (แพ้/หมดเวลา) — ระหว่างนี้เปลี่ยนระดับความยากไม่ได้ แม้จะผ่านด่านไปแล้วก็ตาม
    (ถ้าบอร์ดรายงานผลกลับมาไม่ได้ เช่นใช้ HTML ฝังตรง ๆ จะไม่ล็อก เพราะไม่รู้ว่าเกมจบเมื่อไร)"""
    return BOARD_COMPONENT is not None and bool(st.session_state.get("run_active"))


def current_level():
    """ลำดับระดับความยากที่ใช้อยู่: ระหว่างรอบใช้ระดับที่ล็อกไว้ ไม่งั้นใช้ค่าบนแถบเลื่อน"""
    ss = st.session_state
    return ss.get("run_level", DEFAULT_LEVEL) if run_locked() else level_index(ss.get("difficulty"))


def hint_pool_now():
    """คำใบ้ที่มีตอนเริ่มด่าน (แสดงบนแผงควบคุมหน้าเกม): ระหว่างรอบ = ที่สะสมไว้ (ชนะแล้วรวม +1 ของด่านที่ผ่านแล้ว)
    ยังไม่เริ่มรอบ = ค่าเริ่มต้นของระดับที่เลือกอยู่"""
    if run_locked():
        return st.session_state.get("hint_pool", 0)
    return DIFFICULTIES[current_level()]["start_hints"]


def high_score_of(level):
    """คะแนนสูงสุดที่เคยทำได้ในระดับความยากนั้น (เก็บแยกตามระดับ อยู่ใน session_state จึงเริ่มนับใหม่เมื่อรีเฟรชหน้าเว็บ)"""
    return st.session_state.get("high_scores", {}).get(level, 0)


def record_high(level, total):
    """ถ้าคะแนนรวมของรอบนี้สูงกว่าคะแนนสูงสุดของระดับนั้น ให้จำค่าใหม่ (ไม่ลดลงเอง)"""
    scores = dict(st.session_state.get("high_scores", {}))
    if total > scores.get(level, 0):
        scores[level] = total
    st.session_state["high_scores"] = scores


def needs_shrink_warning(stage, level):
    """ต้องแจ้งเตือนก่อนเริ่มด่านนี้ไหม: ด่าน 16 ขึ้นไป + ระดับที่จับเวลา + ยังไม่เคยแจ้งในรอบนี้"""
    return (stage >= TIME_SHRINK_FROM and DIFFICULTIES[level]["timer"]
            and not st.session_state.get("shrink_warned"))


def new_game():
    """เริ่มเกม (ด่าน) ใหม่: จำนวนกราฟตามด่านปัจจุบัน และระดับความยากของรอบนี้
    เริ่มรอบใหม่ (ยังไม่ล็อก) = อ่านระดับจากแถบเลื่อนแล้วล็อกไว้ ผ่านด่านต่อไปก็ใช้ระดับเดิมจนเกมจบ
    ห้ามเรียกระหว่างที่เกมยังเล่นไม่จบ: กดเริ่มแล้วสุ่มโจทย์ใหม่ (รีโรล) ไม่ได้ ออกได้ทางเดียวคือ go_home()"""
    if game_running():
        return
    ss = st.session_state
    ss["confirm_quit"] = False
    ss["game_counter"] = ss.get("game_counter", 0) + 1
    stage = ss.get("stage", 1)
    new_run = not run_locked()              # ต้องเช็กก่อนตั้ง run_active ด้านล่าง: เริ่มรอบใหม่ = คำใบ้กลับไปเริ่มต้นตามระดับ
    level = current_level()
    cfg = DIFFICULTIES[level]
    if new_run:
        ss["hint_pool"] = cfg["start_hints"]    # คำใบ้เริ่มต้นของระดับ (ผ่านด่านต่อ ๆ ไปสะสมเพิ่ม ดู handle_board_event)
    ss["run_level"] = level
    ss["run_active"] = True
    ss["shrink_notice"] = False
    game = make_game(ss["game_counter"], n=graphs_for_stage(stage), hint_button=cfg["hints"],
                     amp_max=cfg["amp_max"], freq_max=cfg["freq_max"])
    game["hint_pool"] = ss.get("hint_pool", 0) if cfg["hints"] else 0   # คำใบ้ที่กดได้ในด่านนี้ = ที่สะสมไว้ตอนเริ่มด่าน
    game["stage"] = stage
    game["difficulty"] = level
    game["base_total"] = st.session_state.get("total_score", 0)    # คะแนนรวมก่อนเริ่มเกมนี้
    game["base_high"] = high_score_of(level)                       # คะแนนสูงสุดของระดับนี้ก่อนเริ่มเกมนี้
    st.session_state["game"] = game
    st.session_state["mode"] = "game"       # เริ่มเกมใหม่แล้วกลับมาที่หน้าเกมเสมอ
    ss["tutorial_ask"] = False              # เริ่มเล่นแล้ว ไม่ต้องถามเรื่อง Tutorial ค้างไว้อีก


def request_start():
    """ปุ่มเริ่มเกม / ด่านถัดไป ทุกปุ่มมาที่นี่: ปกติเริ่มเกมเลย แต่ก่อนเข้าด่าน 16 (ระดับที่จับเวลา)
    ให้แสดงหน้าแจ้งเตือนเรื่องเวลาที่จะลดลงก่อน แล้วรอผู้เล่นกดรับทราบ (ดู ack_shrink_notice)
    ระหว่างที่เกมยังเล่นไม่จบจะไม่ทำอะไรเลย (กันการสุ่มโจทย์ใหม่หลังกดเริ่มเกมแล้ว)"""
    if game_running():
        return
    ss = st.session_state
    ss["confirm_quit"] = False
    ss["tutorial_ask"] = False              # เริ่มเล่นแล้ว ไม่ถามเรื่อง Tutorial ค้างไว้อีก
    if needs_shrink_warning(ss.get("stage", 1), current_level()):
        ss["shrink_notice"] = True
        ss["mode"] = "game"
    else:
        new_game()


def ack_shrink_notice():
    """ผู้เล่นกดรับทราบการแจ้งเตือนเวลาลดลง: จำไว้ว่าแจ้งแล้ว (ด่านถัดไปไม่แจ้งซ้ำ) แล้วเริ่มด่านเลย"""
    st.session_state["shrink_warned"] = True
    new_game()


def ask_quit():
    """ปุ่ม 🏠 กลับหน้าแรก (กดครั้งแรก): ขอให้ยืนยันก่อน เพราะการกลับหน้าแรกกลางเกมนับเป็นแพ้"""
    st.session_state["confirm_quit"] = True


def cancel_quit():
    st.session_state["confirm_quit"] = False


def go_home():
    """กลับไปหน้าแรก (กราฟ SINALL + ปุ่มเริ่มเกม / กติกา / SANDBOX): จบรอบปัจจุบันทั้งรอบ
    - ถ้ากำลังเล่นอยู่ = ยอมแพ้ ถือเท่ากับแพ้: คะแนนรวมรีเซ็ตเป็น 0 กลับไปด่าน 1 (เก็บ ⭐ คะแนนสูงสุดของระดับไว้)
      ไม่งั้นจะกลายเป็นช่องทางรีโรลโจทย์ (กลับหน้าแรกแล้วกดเริ่มใหม่)
    - ถ้าเกมจบแล้ว (ชนะ/แพ้/หมดเวลา) = ล้างโจทย์เก่าและเริ่มรอบใหม่ตั้งแต่ด่าน 1 เช่นกัน
    ปลดล็อกการเลือกระดับความยาก และ SANDBOX (ไม่มีเกมค้างอยู่แล้ว)"""
    ss = st.session_state
    record_high(ss.get("run_level", DEFAULT_LEVEL), ss.get("total_score", 0))
    ss["total_score"] = 0
    ss["stage"] = 1
    ss["run_active"] = False
    ss["shrink_warned"] = False
    ss["shrink_notice"] = False
    ss["confirm_quit"] = False
    ss["tutorial_ask"] = False
    ss["mode"] = "home"
    ss.pop("game", None)
    ss.pop("last_status", None)
    ss.pop("hint_pool", None)               # คำใบ้สะสมหายไปพร้อมรอบ (รอบใหม่เริ่มที่ start_hints ของระดับ)


def press_start():
    """ปุ่ม ▶ เริ่มเกม ที่หน้าแรก: ไปหน้าเกม (ยังไม่สุ่มโจทย์ ต้องเลือกระดับแล้วกดเริ่มที่หน้าเกมอีกที)
    การกดครั้งแรกของเซสชัน จะถามก่อนว่าต้องการดู Tutorial ไหม ถามครั้งเดียว: จำไว้ใน tutorial_asked
    จนกว่าจะรีเฟรชหน้าเว็บ (session_state ถูกล้าง) จึงจะถามใหม่"""
    ss = st.session_state
    ss["mode"] = "game"
    ss["show_rules"] = False
    if not ss.get("tutorial_asked"):
        ss["tutorial_asked"] = True
        ss["tutorial_ask"] = True


def skip_tutorial_question():
    st.session_state["tutorial_ask"] = False


def open_tutorial(back="game"):
    """เปิดหน้า Tutorial (back = หน้าที่จะกลับไปเมื่อจบ: "game" ถ้ามาจากคำถามหลังกดเริ่มเกม / "home" ถ้ามาจากหน้ากติกา)"""
    ss = st.session_state
    ss["mode"] = "tutorial"
    ss["tutorial_back"] = back
    ss["tutorial_count"] = ss.get("tutorial_count", 0) + 1     # key ของบอร์ดลองเล่นเปลี่ยนทุกครั้งที่เข้า: ได้บอร์ดใหม่เอี่ยม ไกด์เริ่มที่ขั้นแรก
    ss["tutorial_ask"] = False
    ss["show_rules"] = False


def close_tutorial():
    """ออกจาก Tutorial: กลับไปหน้าที่มา (หน้าเกมหรือหน้าแรก)"""
    ss = st.session_state
    ss["mode"] = ss.get("tutorial_back", "game")
    ss["tutorial_ask"] = False


def current_theme():
    """ธีมที่เลือกอยู่: "dark" (มืด ค่าเริ่มต้น) หรือ "light" (สว่าง) เก็บใน session_state จึงกลับเป็นโหมดมืดเมื่อรีเฟรชหน้าเว็บ"""
    t = st.session_state.get("theme", DEFAULT_THEME)
    return t if t in THEMES else DEFAULT_THEME


def toggle_theme():
    """ปุ่มสลับโหมดสว่าง/มืด (ใช้เป็น callback)"""
    st.session_state["theme"] = "light" if current_theme() == "dark" else "dark"


def toggle_rules():
    st.session_state["show_rules"] = not st.session_state.get("show_rules", False)


def game_score(status, attempts, hints, n_graphs):
    """คะแนนของเกมหนึ่งเกม (ถูกหมดในการส่งครั้งที่ attempts):
        คะแนนเต็มของจำนวนกราฟ − ATTEMPT_PENALTY[ครั้งที่ส่ง] (0, 2, 4) − จำนวนครั้งที่กดคำใบ้ × HINT_COST  (ไม่ติดลบ)
    แพ้ (ส่งครบ 3 ครั้งแล้วไม่ถูก) ได้ 0"""
    if status != "won" or n_graphs not in FULL_SCORE or not 1 <= attempts <= MAX_ATTEMPTS:
        return 0
    return max(0, FULL_SCORE[n_graphs] - ATTEMPT_PENALTY[attempts - 1] - HINT_COST * hints)


# ---------------------------------------------------------------------
# กราฟ SINALL บนหน้าแรก: ตัวอักษร S I N A L L ที่ 6 เส้นโค้งปิด แต่ละเส้นเขียนด้วยอนุกรมฟูเรียร์ (t = 0 ถึง 1)
#     x(t) = P + Σ_{n=1..N} [ Aₙ cos(2πnt) + Bₙ sin(2πnt) ]
#     y(t) = Q + Σ_{n=1..N} [ Cₙ cos(2πnt) + Dₙ sin(2πnt) ]
# หาสัมประสิทธิ์จากเส้นกึ่งกลางของตัวอักษรด้วย FFT แล้วคูณหน้าต่าง Gaussian ให้มุมโค้งมน (ไม่มีริปเปิลแบบ Gibbs)
# P เลื่อนตัวอักษรไปตามแนวนอน (เหมือน a₀ ในเกม) Q = 0  ฝั่งเบราว์เซอร์ (HOME_HTML) รวมแค่ N เทอมแรกตามแถบเลื่อน
# ---------------------------------------------------------------------
def _arc(cx, cy, r, a_from, a_to, n=300):
    th = np.deg2rad(np.linspace(a_from, a_to, n))
    return np.column_stack([cx + r * np.cos(th), cy + r * np.sin(th)])


def _retrace(path):
    """เส้นเปิด -> เส้นปิด โดยไปแล้วย้อนกลับ"""
    return np.vstack([path, path[-2:0:-1]])


def _letter_loops():
    top = _arc(0.55, 1.5, 0.5, 35, 270)
    bottom = _arc(0.55, 0.5, 0.5, 90, -145)
    path_s = np.vstack([top, bottom[1:]])
    path_i = np.array([[0.0, 0.0], [0.0, 2.0]])
    path_n = np.array([[0, 0], [0, 2], [1.15, 0], [1.15, 2]], float)
    path_l = np.array([[0, 2], [0, 0], [0.9, 0]], float)
    loop_a = np.array([[0, 0], [0.55, 2], [1.1, 0], [0.9075, 0.7], [0.1925, 0.7]], float)
    return [("S", _retrace(path_s)), ("I", _retrace(path_i)), ("N", _retrace(path_n)),
            ("A", loop_a), ("L", _retrace(path_l)), ("L", _retrace(path_l))]


def _resample_closed(pts, m):
    closed = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(closed, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, s[-1], m, endpoint=False)
    return np.column_stack([np.interp(u, s, closed[:, 0]), np.interp(u, s, closed[:, 1])])


def _fourier(sig, n, w):
    spec = np.fft.rfft(sig) / len(sig)
    return spec[0].real, 2 * spec[n].real * w, -2 * spec[n].imag * w


def _series(c0, a, b, t):
    n = np.arange(1, len(a) + 1)[:, None]
    ang = 2 * np.pi * n * t[None, :]
    return c0 + (a[:, None] * np.cos(ang) + b[:, None] * np.sin(ang)).sum(axis=0)


def letters_data():
    """สัมประสิทธิ์ฟูเรียร์ของตัวอักษร S I N A L L (ทุกตัวสูงเท่ากัน LETTER_H วางต่อกันเป็นแถวเดียว) ส่งให้ HOME_HTML เป็น JSON"""
    td = np.linspace(0, 1, 8192, endpoint=False)
    n_idx = np.arange(1, LETTER_N + 1)
    window = np.exp(-0.5 * (n_idx / LETTER_N0) ** 2)
    letters, offset = [], 0.0
    for name, pts in _letter_loops():
        xy = _resample_closed(pts - pts.min(axis=0), LETTER_SAMPLES)
        cx0, ax, bx = _fourier(xy[:, 0], n_idx, window)
        cy0, ay, by = _fourier(xy[:, 1], n_idx, window)
        xs, ys = _series(cx0, ax, bx, td), _series(cy0, ay, by, td)
        s = LETTER_H / (ys.max() - ys.min())                   # ทุกตัวอักษรสูง LETTER_H พอดี
        p, q = s * (cx0 - xs.min()) + offset, s * (cy0 - ys.min())
        r = lambda v: np.round(v, LETTER_DEC)
        letters.append({"name": name, "P": float(r(p)), "Q": float(r(q)),
                        "A": r(s * ax).tolist(), "B": r(s * bx).tolist(),
                        "C": r(s * ay).tolist(), "D": r(s * by).tolist()})
        offset += s * (xs.max() - xs.min()) + LETTER_GAP
    return {"n_max": LETTER_N, "n_start": LETTER_N, "letters": letters}


# =====================================================================
# ธีมสี: โหมดมืด (dark) / โหมดสว่าง (light) ใช้ร่วมกันทุกหน้า
# ตารางสีอยู่ที่เดียว (THEME_COLORS) แล้วสร้างเป็น (1) ตัวแปร CSS --ชื่อ ใส่ในทุกหน้า HTML (บอร์ด หน้าแรก SANDBOX)
# (2) ตารางสีของ JavaScript สำหรับวาด canvas (3) CSS ของหน้าเว็บ Streamlit เอง (page_css)
# =====================================================================
THEMES = ("dark", "light")
DEFAULT_THEME = "dark"
THEME_COLORS = {
    "dark": {
        "bg": "#06100b", "bezel": "#0d1d15", "panel": "#0a1610", "line": "#173f2b", "ink": "#d4f7e2", "dim": "#78b394",
        "mix": "#39ff88", "mixtxt": "#39ff88", "recv": "#ffb000", "recvtxt": "#ffb000", "sum": "#ffb000", "warn": "#ffb000",
        "bad": "#ff7a6b", "okbg": "#0c2a18", "errbg": "#2a1210", "warnbg": "#2a2008",
        "pbg": "#16a34a", "pborder": "#22c55e", "pink": "#03140a",
        "cap1": "#2a4a39", "cap2": "#10201a", "tick": "#2f6b4a", "off": "#3d4d44",
        "scrim": "rgba(3,10,6,.84)", "shadow": "rgba(0,0,0,.6)", "glow": "rgba(57,255,136,.35)", "flash": "rgba(255,176,0,.9)",
        "grid": "#14402a", "grid2": "#0c2a1b", "axis": "#2d7a52", "ctext": "#9fe3bd", "cdim": "#4b7d62",
        "palette": ["#39ff88", "#4dd2ff", "#ff7ad9", "#ffd24d", "#b794ff", "#ff8a5c"], "blur": 7,
    },
    "light": {
        "bg": "#f4f8f5", "bezel": "#e6efe9", "panel": "#ffffff", "line": "#b8cbc0", "ink": "#10281c", "dim": "#4a6a58",
        "mix": "#15803d", "mixtxt": "#0f6b33", "recv": "#bd7a00", "recvtxt": "#8f5a00", "sum": "#bd7a00", "warn": "#bd7a00",
        "bad": "#d92d20", "okbg": "#dcf3e3", "errbg": "#fde4e1", "warnbg": "#fdf0d0",
        "pbg": "#15803d", "pborder": "#0f6b33", "pink": "#ffffff",
        "cap1": "#ffffff", "cap2": "#d3e2d9", "tick": "#7fa08b", "off": "#b7c4bc",
        "scrim": "rgba(244,248,245,.86)", "shadow": "rgba(16,40,28,.28)", "glow": "rgba(21,128,61,.30)", "flash": "rgba(189,122,0,.9)",
        "grid": "#c6d8cd", "grid2": "#e1ebe5", "axis": "#6f9a82", "ctext": "#35564a", "cdim": "#6f8c7c",
        "palette": ["#15803d", "#0b78b5", "#c026a3", "#b78103", "#6d4fd1", "#d9531e"], "blur": 0,
    },
}


def theme_css_vars():
    """ตัวแปร CSS ของทั้งสองธีม: :root = โหมดมืด และ :root[data-theme="light"] = โหมดสว่าง (ชื่อ --bg, --ink, --p0..--p5 ฯลฯ)"""
    def block(selector, name):
        c = THEME_COLORS[name]
        items = ["--%s:%s" % (k, v) for k, v in c.items() if k not in ("palette", "blur")]
        items += ["--p%d:%s" % (i, v) for i, v in enumerate(c["palette"])]
        return "%s{%s;color-scheme:%s}" % (selector, ";".join(items), name)
    return block(":root", "dark") + "\n" + block(':root[data-theme="light"]', "light")


THEME_JS = """
const THEMES = %s;                 // ตารางสีของ canvas ทั้งสองธีม (สร้างจาก THEME_COLORS)
let THEME = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
let TH = THEMES[THEME], PALETTE = TH.palette, C = null;
function paintColors(){            // ชื่อสีที่โค้ดวาดใช้อยู่ (C.bg, C.grid, ...) มาจากธีมปัจจุบัน
  C = {bg:TH.bg, grid:TH.grid, gridMinor:TH.grid2, axis:TH.axis, ink:TH.ctext, dim:TH.cdim, recv:TH.recv, mix:TH.mix, sum:TH.sum, bad:TH.bad};
}
function applyTheme(t){            // สลับธีม (บอร์ดที่เป็น Streamlit component รับธีมใหม่ทางอาร์กิวเมนต์โดยไม่โหลดหน้าใหม่)
  THEME = t === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", THEME);
  TH = THEMES[THEME]; PALETTE = TH.palette; paintColors();
}
paintColors();
""" % json.dumps(THEME_COLORS)


def fill_theme(html):
    """ใส่ตัวแปรสี (__THEME_CSS__) และตารางสีของ JavaScript (__THEME_JS__) ลงใน HTML ของแต่ละหน้า"""
    return html.replace("__THEME_CSS__", theme_css_vars()).replace("__THEME_JS__", THEME_JS)


def themed(html, theme):
    """เลือกธีมของหน้า HTML ที่จะฝัง (ค่าเริ่มต้นของแอตทริบิวต์ data-theme บน <html>)"""
    return html.replace("__THEME__", theme if theme in THEMES else DEFAULT_THEME)


# =====================================================================
# ส่วนที่ 3: บอร์ดเกม (HTML + JavaScript ทำงานในเบราว์เซอร์)
# __GAME_JSON__ จะถูกแทนด้วยโจทย์ที่สุ่มจาก Python
# =====================================================================
BOARD_HTML = r"""<!doctype html>
<html lang="th" data-theme="__THEME__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SINALL board</title>
<style>
__THEME_CSS__
:root{
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
.chip b{font:600 18px var(--mono);color:var(--mixtxt)}
.chip span{font-size:12px;color:var(--dim)}
.chip em{font:600 12px var(--mono);font-style:normal;color:var(--recvtxt)}
.actions{display:flex;flex-wrap:wrap;gap:8px}
.btn{font:600 14px var(--sans);padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:var(--bezel);color:var(--ink);cursor:pointer}
.btn:hover:not(:disabled){border-color:var(--mix)}
.btn.primary{background:var(--pbg);border-color:var(--pborder);color:var(--pink)}
.btn:disabled{opacity:.45;cursor:not-allowed}
:focus-visible{outline:2px solid var(--mix);outline-offset:2px}

.status{margin-top:8px;min-height:34px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bezel);font-size:13px}
.status:empty{display:none}
.status.ok{border-color:var(--mix);background:var(--okbg)}
.status.err{border-color:var(--bad);background:var(--errbg)}
.status.warn{border-color:var(--recv);background:var(--warnbg)}

.screen{margin-top:8px;padding:6px 8px 4px;border:1px solid var(--line);border-radius:10px;background:var(--bg)}
.screen.solved{box-shadow:0 0 0 2px var(--mix),0 0 22px var(--glow)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center;font-size:12px;color:var(--dim)}
.stagebadge{padding:1px 8px;border:1px solid var(--line);border-radius:6px;font:700 12px var(--mono);color:var(--recvtxt)}
.timer{margin-left:auto;padding:0 4px;font:700 17px/1.2 var(--mono);color:var(--mixtxt)}
.timer.off{font:600 12px var(--sans);color:var(--dim)}
.timer.warn{color:var(--recvtxt)}
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
  background:radial-gradient(circle at 35% 30%,var(--cap1),var(--cap2));border:2px solid var(--mix);transition:transform .09s ease-out}
.cap::before{content:"";position:absolute;left:50%;top:3px;width:3px;height:12px;margin-left:-1.5px;border-radius:2px;background:var(--mix)}
.knob.locked .cap{border-color:var(--recv)}
.knob.locked .cap::before{background:var(--recv)}
.knob.locked .dial{cursor:not-allowed}
.knob.locked .readout,.knob.locked .kname{color:var(--recvtxt)}
.dial svg line{stroke:var(--tick);stroke-width:2;stroke-linecap:round}
.knob.wrong .cap::before{background:#ff3b3b;box-shadow:0 0 6px rgba(255,59,59,.75)}   /* ขีดที่ชี้ค่าที่ยังไม่ถูก (ผิดจากที่เคยส่งตรวจ) = สีแดง */
body.over .dial{cursor:not-allowed}
.dial.flash{animation:flash .9s ease-out 1}
@keyframes flash{0%{box-shadow:0 0 0 0 var(--flash)}100%{box-shadow:0 0 0 14px transparent}}   /* เรืองแสงวาบหนึ่ง: ใช้ทั้งตอนขอคำใบ้และตอนส่งตรวจแล้วค่านั้นถูก */
@media (prefers-reduced-motion:reduce){.cap{transition:none}.dial.flash{animation:none}}
.row{display:flex;align-items:center;gap:2px}
.step{width:20px;height:22px;padding:0;border:1px solid var(--line);border-radius:5px;background:var(--bezel);color:var(--ink);font-size:10px;cursor:pointer}
.step:disabled{opacity:.35;cursor:not-allowed}
.readout{min-width:50px;text-align:center;font:600 12px var(--mono);color:var(--mixtxt)}

/* หน้าสรุปผล */
#summary{position:fixed;inset:0;z-index:30;display:flex;align-items:center;justify-content:center;padding:12px;overflow:auto;background:var(--scrim)}
.sumcard{width:min(560px,100%);max-height:100%;overflow:auto;padding:16px 18px;border:2px solid var(--line);border-radius:14px;background:var(--bezel);box-shadow:0 10px 40px var(--shadow)}
.sumcard.win{border-color:var(--mix)}
.sumcard.lose{border-color:var(--bad)}
.sumcard h2{margin:0;font-size:20px}
.sumcard h3{margin:14px 0 6px;font-size:14px;color:var(--dim)}
.sumcard p{margin:4px 0 0;font-size:13px;color:var(--dim)}
.scorelist{display:grid;grid-template-columns:1fr auto;gap:4px 0;margin-top:12px;font-size:14px}
.scorelist .v{padding-left:16px;text-align:right;font:600 14px var(--mono)}
.scorelist .big{margin-top:6px;padding-top:6px;border-top:1px solid var(--line);font-weight:700;font-size:16px}
.scorelist .v.big{color:var(--mixtxt);font-size:22px}
.scorelist .tot{font-weight:700}
.scorelist .v.tot{color:var(--mixtxt);font-size:18px}
.scorelist .hs{margin-top:4px;padding-top:6px;border-top:1px solid var(--line);font-weight:700;color:var(--recvtxt)}
.scorelist .v.hs{font-size:18px}
#log table{border-collapse:collapse;font:13px var(--mono);width:100%}
#log th,#log td{padding:3px 12px 3px 0;text-align:left}
#log th{color:var(--dim);font-weight:600}
#log .ok{color:var(--mixtxt)}
#log .no{color:var(--bad)}
.sumbtns{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.sumbtns .btn{flex:1 1 130px}

/* ไกด์ Tutorial (เฉพาะด่านลองเล่น): กล่องไกด์ลอยอยู่ติดกับส่วนที่ไฮไลต์ */
#app{position:relative}
#coachspan{position:absolute;left:0;width:1px;pointer-events:none;visibility:hidden}
#coach{position:absolute;z-index:20;width:min(360px,calc(100% - 12px));padding:9px 14px 12px;border:2px solid var(--mix);border-radius:12px;background:var(--bezel);color:var(--ink);box-shadow:0 10px 30px var(--shadow)}
#coach::before{content:"";position:absolute;left:var(--ax,40px);width:14px;height:14px;margin-left:-7px;background:var(--bezel);border:2px solid var(--mix);transform:rotate(45deg)}
#coach.below::before{top:-9px;border-right:0;border-bottom:0}
#coach.above::before{bottom:-9px;border-left:0;border-top:0}
.ctop{display:flex;align-items:center;justify-content:space-between;gap:8px;font:600 11px var(--mono);color:var(--dim)}
.cdots{display:flex;gap:3px;flex:1;margin:0 8px}
.cdots i{flex:1;max-width:16px;height:4px;border-radius:2px;background:var(--line)}
.cdots i.on{background:var(--mix)}
.cx{border:0;background:transparent;color:var(--dim);font-size:14px;line-height:1;cursor:pointer;padding:2px 4px}
#coach h3{margin:6px 0 4px;font-size:15px}
.cbody{font-size:13px;line-height:1.55}
.cbody p{margin:0 0 4px}
.cvis{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start;justify-content:center;margin:8px 0 2px}
.fig{margin:0;text-align:center}
.fig svg{display:block}
.fig figcaption{margin-top:2px;font:600 11px var(--mono);color:var(--dim)}
.cok{margin-top:8px;padding:4px 8px;border:1px solid var(--mix);border-radius:6px;background:var(--okbg);font-size:12.5px}
.cwait{margin-top:8px;font:600 12.5px var(--sans);color:var(--recvtxt)}
.cnav{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.cnav .sp{flex:1}
.cbtn{padding:5px 10px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--ink);font:600 12.5px var(--sans);cursor:pointer}
.cbtn:hover:not(:disabled){border-color:var(--mix)}
.cbtn.primary{background:var(--pbg);border-color:var(--pborder);color:var(--pink)}
.cbtn:disabled{opacity:.4;cursor:not-allowed}
.hl{position:relative;z-index:6;border-radius:10px;box-shadow:0 0 0 3px var(--mix),0 0 16px 4px var(--glow);animation:hlp 1.3s ease-in-out infinite}
.knob.hl{padding:3px 2px}
@keyframes hlp{50%{box-shadow:0 0 0 5px var(--mix),0 0 24px 8px var(--glow)}}
@media (prefers-reduced-motion:reduce){.hl{animation:none}}
.y{color:var(--recvtxt);font-weight:700}
.g{color:var(--mixtxt);font-weight:700}
.r{color:var(--bad);font-weight:700}
</style>
</head>
<body>
<div id="app">
  <div class="top">
    <div class="bar">
      <div class="chips">
        <div class="chip" title="จำนวนกราฟ sin ที่ซ่อนอยู่ในสัญญาณผสม"><b id="m-n">0</b><span>กราฟที่ซ่อน</span></div>
        <div class="chip" title="ค่าที่ล็อกแล้ว (🔒 ผู้ดูแลให้ตอนเริ่ม + ที่ตรงเฉลยจากการส่งตรวจ)"><b id="m-h">0</b><span>ค่าที่ล็อกแล้ว</span></div>
        <div class="chip" title="ส่งตรวจไปแล้วกี่ครั้ง จากสูงสุด 3 ครั้ง"><b id="m-a">0/3</b><span>ส่งตรวจ</span></div>
        <div class="chip" id="m-pbox"><b id="m-p">0</b><span id="m-pl">คะแนนถ้าถูก</span></div>
        <div class="chip" title="คะแนนรวมของเกมที่ชนะต่อเนื่อง (แพ้แล้วรีเซ็ตเป็น 0) · ⭐ = คะแนนสูงสุดของระดับนี้ เก็บไว้ไม่รีเซ็ต"><b id="m-t">0</b><span>คะแนนรวม</span><em id="m-hs">⭐ 0</em></div>
      </div>
      <div class="actions">
        <button id="hint" class="btn" type="button"></button>
        <button id="submit" class="btn primary" type="button">📤 ส่งให้ผู้ดูแลตรวจสอบ</button>
        <button id="tourbtn" class="btn" type="button" hidden>🎓 ไกด์</button>
        <button id="showsum" class="btn" type="button" hidden>📋 สรุปผล</button>
      </div>
    </div>
    <div id="status" class="status" role="status" aria-live="polite"></div>
    <section id="bigscreen" class="screen" aria-label="จอใหญ่">
      <div class="legend">
        <span><i class="sw" style="background:var(--recv)"></i>สัญญาณที่รับจากอวกาศ</span>
        <span><i class="sw" style="background:var(--mix)"></i>สัญญาณที่คุณผสมได้ (ผลรวมทุกจอ)</span>
        <span id="stage" class="stagebadge"></span>
        <span id="timer" class="timer" role="timer" title="เวลาที่เหลือ (ไม่มีผลต่อคะแนน แต่ถ้าหมดเวลาเกมจะจบทันที)"></span>
      </div>
      <canvas id="big" role="img" aria-label="กราฟสัญญาณที่รับได้เทียบกับสัญญาณที่ผสม"></canvas>
    </section>
  </div>
  <div id="grid" class="grid"></div>
  <div id="coachspan"></div>
  <div id="coach" role="dialog" aria-live="polite" aria-label="ไกด์สอนเล่น" hidden></div>
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
    <p id="sum-noact" hidden></p>
  </div>
</div>

<script>
(function(){
"use strict";
__THEME_JS__
const EMBEDDED = __GAME_JSON__;   // โจทย์ที่ฝังมาตรง ๆ (โหมด st.iframe) หรือ null เมื่อทำงานเป็น Streamlit component
let booted = false;

let onTheme = null;               // boot ตั้งให้: วาด canvas ใหม่เมื่อเปลี่ยนธีม
function boot(GAME, host){        // host = ตัวส่งผลกลับไปหา Streamlit (null ถ้าไม่มี)
let tour = null;                  // ไกด์ Tutorial (มีเฉพาะด่านลองเล่น)

/* ---------- ค่าคงที่ ---------- */
const N_SCREENS = 6, NPTS = 721, TOL = 1e-6;
const X_MAX = 4 * Math.PI;                  // จอใหญ่: x = 0 ถึง 4π (เรเดียน) ส่วนแกน y ตรึงตามกราฟปริศนาของด่านนี้ (Y_TOP / Y_BOT ด้านล่าง)
const FULL = Number.isFinite(GAME.full_score) ? GAME.full_score : 10;                       // คะแนนเต็มของเกมนี้ (ขึ้นกับจำนวนกราฟ)
const ATT_PEN = Array.isArray(GAME.attempt_penalty) && GAME.attempt_penalty.length ? GAME.attempt_penalty : [0, 2, 4];   // หักเมื่อถูกในครั้งที่ 1, 2, 3
const MAX_ATT = ATT_PEN.length;                                                             // ส่งตรวจได้สูงสุดกี่ครั้ง
const HINT_COST = Number.isFinite(GAME.hint_cost) ? GAME.hint_cost : 1;                     // คำใบ้เพิ่ม 1 ครั้ง หักกี่คะแนน
const BASE_TOTAL = Number.isFinite(GAME.base_total) ? GAME.base_total : 0;                  // คะแนนรวมก่อนเริ่มเกมนี้
const BASE_HIGH = Number.isFinite(GAME.base_high) ? GAME.base_high : 0;                     // คะแนนสูงสุดก่อนเริ่มเกมนี้
const TIME_LIMIT = Number.isFinite(GAME.time_limit) ? GAME.time_limit : 0;                  // เวลาของเกมนี้ (วินาที) 0 = ไม่จับเวลา (ระดับนักเรียน)
const TIMED = TIME_LIMIT > 0;
const HINT_BUTTON = GAME.hint_button !== false;                                            // false = ไม่มีปุ่มคำใบ้เพิ่ม (ตอนนี้ทุกระดับมีปุ่ม)
const HINT_POOL = Number.isFinite(GAME.hint_pool) ? GAME.hint_pool : GAME.bonus.length;     // คำใบ้ที่กดได้ในด่านนี้ (สะสมมาจากด่านก่อน ๆ)
const HINT_PER_STAGE = Number.isFinite(GAME.hint_per_stage) ? GAME.hint_per_stage : 1;      // ผ่านด่านนี้แล้วได้คำใบ้เพิ่มกี่ครั้ง
const AMP_MAX = Number.isFinite(GAME.amp_max) ? GAME.amp_max : 3;                           // ลูกบิดแอมพลิจูด: จำนวนเต็ม [-AMP_MAX, AMP_MAX] ยกเว้น 0
const FREQ_MAX = Number.isFinite(GAME.freq_max) ? GAME.freq_max : 3;                        // ลูกบิดความถี่: จำนวนเต็ม [-FREQ_MAX, FREQ_MAX] ยกเว้น 0
const STAGE = Number.isFinite(GAME.stage) ? GAME.stage : 1;                                // ด่านที่เล่นอยู่
const PRACTICE = GAME.practice === true;                                                   // ด่านลองเล่นใน Tutorial: ไม่ส่งคะแนนกลับไปหา Streamlit (ฝังตรง ๆ)
const LEVEL = typeof GAME.difficulty === "string" ? GAME.difficulty : "";                  // ชื่อระดับความยาก
const T0 = Date.now();                                                                     // เวลาเริ่มเกม (ตอนบอร์ดเริ่มทำงาน)
const DEADLINE = T0 + TIME_LIMIT * 1000;
const PHASES = [0, 90, 180, 270];
const KINDS = ["amp", "freq", "phase"];
const intRange = m => { const v = []; for (let q = -m; q <= m; q++) if (q !== 0) v.push(q); return v; };   // −m..m ไม่รวม 0
const VALUES = {amp:intRange(AMP_MAX), freq:intRange(FREQ_MAX), phase:PHASES};
const NAME = {amp:"แอมพลิจูด", freq:"ความถี่", phase:"เฟส"};
const SYM = {amp:"A", freq:"f", phase:"φ"};
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

// ขอบเขตแกน y ที่ตรึงไว้ตลอดด่าน = ค่าต่ำสุด − 1 ถึง ค่าสูงสุด + 1 ของกราฟปริศนา (เช่น สูงสุด 10 ต่ำสุด −5 -> −6 ถึง 11)
// กราฟที่ผู้เล่นผสม/หมุนอาจเกินขอบเขตนี้ได้ ส่วนที่เกินจะถูกตัดออกจากจอ (แกน y ไม่ขยายตามกราฟของผู้เล่น)
function ySpan(arr){
  let hi = -Infinity, lo = Infinity;
  for (let j = 0; j < arr.length; j++){ hi = Math.max(hi, arr[j]); lo = Math.min(lo, arr[j]); }
  return {top: hi + 1, bot: lo - 1};
}
const {top: Y_TOP, bot: Y_BOT} = ySpan(TARGET);          // จอใหญ่: ตามกราฟปริศนา (ผลรวมของทุกจอ)
const SMALL_Y = KEYWAVE.map(ySpan);                      // จอเล็กแต่ละจอ: กฎเดียวกัน แต่ใช้กราฟเฉลยของจอนั้น (ตรึงตลอดด่านเช่นกัน)

const state = {knobs:[], locked:[], wrong:[], bonusLeft:HINT_POOL, hintsUsed:0,
               attempts:0, solved:false, over:false, score:0, seq:0, last:null,
               totalAfter:BASE_TOTAL, highAfter:BASE_HIGH, record:false, timedOut:false, timeLeft:TIME_LIMIT, usedSec:0};
for (let i = 0; i < N_SCREENS; i++){
  const on = i < N;
  state.knobs.push(on ? {amp:1, freq:1, phase:0} : {amp:0, freq:0, phase:0});
  state.locked.push({amp:!on, freq:!on, phase:!on});
  state.wrong.push({amp:new Set(), freq:new Set(), phase:new Set()});   // ค่าที่ส่งตรวจแล้วรู้ว่ายังไม่ถูก (ต่อลูกบิด) ใช้ทำขีดแดง
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
// ลูกบิดที่ยังไม่ล็อกแต่ค่าถูกแล้ว (ตรงเฉลย หรือจอนั้นได้กราฟเดียวกับเฉลยแล้ว = ครบทั้ง 3 ลูกบิด) ในรูป [[จอ, ชนิด], ...]
function matchingKnobs(){
  const r = [];
  for (let i = 0; i < N; i++){
    const screenOk = sameWave(cur[i], KEYWAVE[i]);
    KINDS.forEach(k => {
      if (state.locked[i][k]) return;
      if (screenOk || state.knobs[i][k] === KEY[i][k]) r.push([i, k]);
    });
  }
  return r;
}
// หลังส่งตรวจ: ล็อกค่าที่ตรงกับเฉลยทันที เป็นการล็อกแบบเดียวกับคำใบ้เริ่มต้นเลย (สีเหลือง 🔒) คืนรายการที่เพิ่งล็อก
function lockMatches(){
  const hits = matchingKnobs();
  hits.forEach(h => { state.locked[h[0]][h[1]] = true; });
  return hits;
}
// ลูกบิดเรืองแสงวาบหนึ่ง (เอฟเฟกต์เดียวกับตอนขอคำใบ้)
function flashKnob(i, k){
  const dial = els[i].knobs[k].dial;
  dial.classList.remove("flash"); void dial.offsetWidth; dial.classList.add("flash");
  dial.onanimationend = () => dial.classList.remove("flash");        // เล่นจบแล้วเอาคลาสออก (เล่นซ้ำได้ครั้งต่อไป)
}
// หลังส่งตรวจ (หลัง lockMatches): ลูกบิดที่ยังไม่ล็อก = ค่าที่ชี้อยู่ยังไม่ถูก จำค่านั้นไว้
// ขีดบนลูกบิดจะเป็นสีแดงทุกครั้งที่ชี้ค่านี้ ทั้งตอนนี้ และตอนหมุนไปมาแล้วเผลอกลับมาชี้ค่าเดิมที่ผิดอีก
function markWrong(){
  for (let i = 0; i < N; i++) KINDS.forEach(k => { if (!state.locked[i][k]) state.wrong[i][k].add(state.knobs[i][k]); });
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
function frame(g, w, h, pad, yMin, yMax, yTicks, xLabels, fontPx){
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  const x0 = pad.l, x1 = w - pad.r, y0 = pad.t, y1 = h - pad.b;
  const px = x => x0 + x / X_MAX * (x1 - x0);              // x อยู่ในช่วง 0 ถึง 4π
  const py = y => y0 + (1 - (y - yMin) / (yMax - yMin)) * (y1 - y0);   // y อยู่ในช่วง yMin ถึง yMax
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
function niceTicks(lo, hi, want){                                  // เส้นกริดแกน y ประมาณ want เส้น (ปกติ 8) ขั้นเป็นจำนวนเต็ม 1, 2, 5, 10, 20, 50, ...
  const raw = (hi - lo) / (want || 8);
  let step = 1;
  if (raw > 1){
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    step = [1, 2, 5, 10].map(m => m * mag).find(s => s >= raw);
  }
  const ticks = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) ticks.push(t);
  return ticks;
}
function drawBig(){
  const {g, w, h} = setup(bigCanvas);
  // แกน y ตรึงตามกราฟปริศนาของด่านนี้ (Y_BOT ถึง Y_TOP = ต่ำสุด − 1 ถึง สูงสุด + 1) ไม่ขยายตามกราฟที่ผสม
  const F = frame(g, w, h, {l:34, r:10, t:8, b:20}, Y_BOT, Y_TOP, niceTicks(Y_BOT, Y_TOP), ["0","π","2π","3π","4π"], 11);
  curve(g, F, TARGET, C.recv, 3.4, 0);
  curve(g, F, MIX, C.mix, 1.6, state.solved ? 8 : 0);
}
function drawSmall(i){                                    // จอเล็ก: แกน y ตรึงตลอดด่านเหมือนจอใหญ่ = ต่ำสุด − 1 ถึง สูงสุด + 1 ของกราฟเฉลยของจอนั้น
  const {g, w, h} = setup(els[i].canvas), Y = SMALL_Y[i];
  const F = frame(g, w, h, {l:22, r:4, t:6, b:6}, Y.bot, Y.top, niceTicks(Y.bot, Y.top, 4), null, 9);
  curve(g, F, cur[i], PALETTE[i], 2, 0);
}
function drawOff(i){                                      // จอที่ไม่ได้ใช้: พื้นเรียบ ๆ กับคำว่า NO SIGNAL เท่านั้น (ไม่มีสัญญาณรบกวน)
  const {g, w, h} = setup(els[i].canvas);
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  g.font = "700 " + Math.min(24, Math.max(14, w / 13)) + "px " + MONO;
  g.fillStyle = C.bad; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("NO SIGNAL", w / 2, h / 2 + 1);
}
function drawScreen(i){ if (i < N) drawSmall(i); else drawOff(i); }

function renderKnob(i, k){
  const K = els[i].knobs[k], on = i < N, v = state.knobs[i][k];
  const vals = VALUES[k], L = vals.length, idx = vals.indexOf(v);
  const locked = state.locked[i][k], frozen = locked || state.over;
  // ขีดแดง: ลูกบิดที่ยังไม่ล็อก และตอนนี้ชี้ค่าที่เคยส่งตรวจแล้วรู้ว่ายังไม่ถูก (ชนะแล้วไม่ต้องแดงอีก)
  const wrong = on && !locked && !state.solved && state.wrong[i][k].has(v);
  const pos = idx < 0 ? (L - 1) / 2 : idx;                          // จอที่ไม่ใช้ค่าเป็น 0 ซึ่งไม่อยู่ในช่วงลูกบิด -> ชี้ตรงกลาง
  K.cap.style.transform = "rotate(" + (-135 + pos * 270 / (L - 1)) + "deg)";
  K.root.classList.toggle("locked", locked && on);                  // 🔒 สีเหลือง = ล็อกแล้ว (ผู้ดูแลบอกให้ตอนเริ่ม หรือตรงเฉลยจากการส่งตรวจ ล็อกเหมือนกัน)
  K.root.classList.toggle("wrong", wrong);                          // ขีดแดง = ค่าที่ชี้อยู่ยังไม่ถูก
  K.name.textContent = (locked && on ? "🔒 " : "") + NAME[k];
  K.readout.textContent = on ? SYM[k] + "=" + fmtVal(k, v) : "-";
  K.dec.disabled = frozen; K.inc.disabled = frozen;
  K.dial.tabIndex = on ? 0 : -1;
  K.dial.setAttribute("aria-valuenow", String(idx));
  K.dial.setAttribute("aria-valuetext", on ? NAME[k] + " " + fmtVal(k, v) + (locked ? " (ล็อกแล้ว)" : wrong ? " (ยังไม่ถูก)" : "") : "ไม่มีสัญญาณ");
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
  hb.title = "ขอคำใบ้ 1 ครั้ง ผู้ดูแลบอกค่าที่ถูกต้องเพิ่ม 1 ค่า และหัก " + HINT_COST + " คะแนน · คำใบ้ที่ใช้แล้วหมดไป ที่เหลือสะสมไปด่านถัดไป และผ่านด่านได้เพิ่ม +" + HINT_PER_STAGE;
  hb.hidden = !HINT_BUTTON;                                       // HINT_BUTTON = false: ไม่มีปุ่มคำใบ้ (ตอนนี้ทุกระดับมีปุ่ม)
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
             '" x2="' + (29 + 27 * s).toFixed(1) + '" y2="' + (29 - 27 * c).toFixed(1) + '"/>';
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
    if (tour) tour.event("knob", {k});
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
      '<div class="ph"><span><i class="dot" style="background:' + (i < N ? "var(--p" + i + ")" : "var(--off)") +
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
  flashKnob(i, k);
  setStatus("warn", "ผู้ดูแลให้คำใบ้เพิ่ม: จอ " + (i + 1) + " " + NAME[k] + " " + SYM[k] + " = " + fmtVal(k, v) +
            " (หัก " + HINT_COST + " คะแนน)");
  if (tour) tour.event("hint");
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
  const hits = lockMatches();           // ค่าที่ถูก -> ล็อก (สีเหลือง 🔒 เหมือนคำใบ้เริ่มต้น) และเรืองแสงหลังวาดใหม่
  markWrong();                          // ค่าที่ยังไม่ถูก -> จำไว้ ขีดบนลูกบิดเป็นสีแดง
  if (state.attempts >= MAX_ATT){
    state.over = true; state.score = 0;
    state.totalAfter = 0;                                             // แพ้: คะแนนรวมรีเซ็ตเป็น 0 แต่คะแนนสูงสุดยังอยู่
    state.highAfter = Math.max(BASE_HIGH, BASE_TOTAL);
    revealAnswer();
    setStatus("err", "ส่งตรวจครบ " + MAX_ATT + " ครั้งแล้วยังไม่ถูกต้อง ผู้ดูแลเฉลยคำตอบที่ถูกต้องบนลูกบิดให้แล้ว (ได้ 0 คะแนนในเกมนี้ · คะแนนรวมรีเซ็ตเป็น 0 · คะแนนสูงสุด "
              + state.highAfter + ")");
    renderAll(); drawBig();
    hits.forEach(h => flashKnob(h[0], h[1]));
    finish();
    return;
  }
  const pct = (Math.floor(res.match * 10) / 10).toFixed(1);
  setStatus("err", "ผู้ดูแลตรวจครั้งที่ " + state.attempts + "/" + MAX_ATT + ": ยังไม่ถูกต้อง สัญญาณตรงกัน " + pct + "% · " +
            (hits.length ? "ล็อกค่าที่ตรงเฉลยให้ " + hits.length + " ค่า (🔒 สีเหลือง)" : "ยังไม่มีค่าไหนตรงเฉลยเพิ่ม") + " · ค่าที่ยังไม่ถูกขึ้นขีดสีแดง" +
            " · เหลือสิทธิ์ส่งอีก " + (MAX_ATT - state.attempts) + " ครั้ง (ถ้าถูกครั้งหน้าได้ " + potential() + " คะแนน)");
  renderAll(); drawBig();
  hits.forEach(h => flashKnob(h[0], h[1]));            // ลูกบิดที่ปรับถูกแล้วเรืองแสงวาบหนึ่งเหมือนตอนขอคำใบ้
  if (tour) tour.event("submit");
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
  if (!host || PRACTICE) return;                          // ด่านลองเล่นไม่ส่งคะแนนกลับไปหา Streamlit
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
         "</tr></thead><tbody>" + rows + "</tbody></table>";
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
    if (HINT_BUTTON) r.push(["💡 คำใบ้สะสมไปด่านถัดไป (เหลือ " + state.bonusLeft + " + ผ่านด่าน +" + HINT_PER_STAGE + ")", String(state.bonusLeft + HINT_PER_STAGE), ""]);
  } else {
    r.push([state.timedOut ? "หมดเวลา เกมจบทันที" : "ตอบไม่ถูกครบ " + MAX_ATT + " ครั้ง", "0", ""]);
    if (state.hintsUsed) r.push(["คำใบ้เพิ่มที่ใช้ " + state.hintsUsed + " ครั้ง (ไม่หักเพิ่ม เพราะไม่มีคะแนนให้หัก)", "", ""]);
    r.push(["คะแนนเกมนี้", "0", "big"]);
    r.push(["คะแนนรวมสะสมก่อนแพ้", String(BASE_TOTAL), ""]);
    r.push(["คะแนนรวมถูกรีเซ็ต", "0", "tot"]);
  }
  r.push(["⭐ คะแนนสูงสุดของระดับนี้" + (won && state.record ? " — สถิติใหม่! 🎉" : ""), String(state.highAfter), "hs"]);
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
  if (tour) tour.event("finish");
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
if (!host || PRACTICE){                                   // ไม่ได้ทำงานเป็น Streamlit component (หรือเป็นด่านลองเล่น): ไม่มีปุ่มที่สื่อสารกลับได้
  $("#sum-actions").hidden = true; $("#sum-noact").hidden = false;
  $("#sum-noact").textContent = PRACTICE ? "นี่คือด่านลองเล่นของ Tutorial คะแนนไม่ถูกนับ กด “ดูกราฟ” แล้วกด ✖ ออกจาก Tutorial ที่ด้านบนของหน้านี้เมื่อพร้อม"
                                         : "ปุ่มเริ่มเกมใหม่และ SANDBOX อยู่ที่แผงควบคุมด้านบนของหน้าเกม";
}

buildPanels();
renderAll();
refresh();
$("#stage").textContent = "ด่าน " + STAGE + " · " + N + " กราฟ" + (LEVEL ? " · " + LEVEL : "");
$("#stage").title = "ด่านที่ " + STAGE + " มีกราฟผสม " + N + " กราฟ · ระดับ " + LEVEL;
paintTimer(TIME_LIMIT);
if (TIMED) clockId = setInterval(tick, 250);
document.addEventListener("visibilitychange", tick);       // กลับมาที่แท็บแล้วตรวจเวลาทันที
onTheme = () => { refresh(); renderAll(); };               // เปลี่ยนธีม: วาดจอทั้งหมดใหม่ด้วยสีของธีมใหม่ (ส่วนที่เป็น CSS เปลี่ยนเอง)

/* =====================================================================
   ไกด์ Tutorial: ทำงานเฉพาะด่านลองเล่น (GAME.tutorial) พาทำทีละขั้นบนบอร์ดจริง
   ไฮไลต์ส่วนที่พูดถึง แล้วรอให้ผู้เล่นลองทำจริง (หมุนลูกบิด ขอคำใบ้ ส่งตรวจ) ก่อนไปขั้นถัดไป ข้ามขั้นได้ตลอด
   ===================================================================== */
function makeTour(){
  const coach = $("#coach"), span = $("#coachspan"), app = $("#app");
  const info = GAME.tour_info || {};
  let idx = 0, closed = false, ended = false, hl = [], cur = null;
  const done = new Set();
  const pickUnlocked = kind => { for (let i = 0; i < N; i++) if (!state.locked[i][kind]) return i; return -1; };
  const knobRoot = (i, k) => els[i].knobs[k].root;
  const lockedKnobs = () => { const r = []; for (let i = 0; i < N; i++) KINDS.forEach(k => { if (state.locked[i][k]) r.push(knobRoot(i, k)); }); return r; };
  const wrongKnobs = () => { const r = []; for (let i = 0; i < N; i++) KINDS.forEach(k => { if (knobRoot(i, k).classList.contains("wrong")) r.push(knobRoot(i, k)); }); return r; };

  // รูปคลื่นเล็ก ๆ ประกอบคำอธิบาย: curves = [{a, f, p, color, w}] ทุกรูปในชุดเดียวกันใช้สเกลความสูง scale เท่ากัน
  function fig(curves, cap, scale){
    const W = 112, H = 46, M = 5;
    let svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" aria-hidden="true">' +
      '<rect x="0.5" y="0.5" width="' + (W - 1) + '" height="' + (H - 1) + '" rx="6" style="fill:var(--bg);stroke:var(--line)"/>' +
      '<line x1="0" y1="' + H / 2 + '" x2="' + W + '" y2="' + H / 2 + '" style="stroke:var(--grid)"/>';
    curves.forEach(c => {
      let d = "";
      for (let j = 0; j <= 96; j++){
        const t = j / 96, y = H / 2 - (c.a / scale) * (H / 2 - M) * Math.sin(c.f * t * 4 * Math.PI + (c.p || 0) * Math.PI / 180);
        d += (j ? "L" : "M") + (t * W).toFixed(1) + " " + y.toFixed(1);
      }
      svg += '<path d="' + d + '" fill="none" style="stroke:' + c.color + '" stroke-width="' + (c.w || 2) + '" stroke-linejoin="round"/>';
    });
    return '<figure class="fig">' + svg + '</svg><figcaption>' + cap + '</figcaption></figure>';
  }
  const YEL = "var(--recv)", GRN = "var(--mix)";

  const STEPS = [
    {id:"goal", title:"🎯 เป้าหมาย: ทำให้เส้นทับกัน", targets:() => [$("#bigscreen")],
     body:() => '<p>เส้น <span class="y">สีเหลือง</span> คือ <b>สัญญาณปริศนา</b> จากอวกาศ (กราฟ sin หลายตัวผสมกัน)</p>' +
                '<p>เส้น <span class="g">สีเขียว</span> คือสัญญาณที่ <b>คุณผสมเอง</b> จากจอเล็กด้านล่าง</p>' +
                '<p><b>ทำให้เส้นเขียวทับเส้นเหลืองพอดี</b> = ถอดรหัสสำเร็จ</p>',
     vis:() => fig([{a:2, f:1, color:YEL, w:3}, {a:1, f:1, p:90, color:GRN}], "ยังไม่ทับ", 2) +
               fig([{a:2, f:1, color:YEL, w:3.4}, {a:2, f:1, color:GRN, w:1.4}], "ทับกันพอดี ✓", 2)},
    {id:"amp", title:"ลูกบิด A · แอมพลิจูด", wait:"amp", skip:() => pickUnlocked("amp") < 0,
     targets:() => [knobRoot(pickUnlocked("amp"), "amp")],
     body:() => '<p><b>A</b> คือ <b>ความสูงของคลื่น</b> (ติดลบ = คลื่นกลับหัว)</p>' +
                '<p>ลอง <b>หมุนลูกบิด A</b> ของจอที่ ' + (pickUnlocked("amp") + 1) + ' ที่ไฮไลต์อยู่ ด้วยการ <b>ลาก</b> · กดปุ่ม <b>◀ ▶</b> · หรือใช้ <b>ลูกศรบนคีย์บอร์ด</b> แล้วดูเส้นเขียวบนจอใหญ่เปลี่ยนตาม</p>',
     vis:() => fig([{a:1, f:1, color:GRN}], "A = 1", 3) + fig([{a:3, f:1, color:GRN}], "A = 3", 3),
     ok:"เห็นไหม? ค่า A เปลี่ยน คลื่นก็สูงขึ้นหรือต่ำลงทันที"},
    {id:"freq", title:"ลูกบิด f · ความถี่", wait:"freq", skip:() => pickUnlocked("freq") < 0,
     targets:() => [knobRoot(pickUnlocked("freq"), "freq")],
     body:() => '<p><b>f</b> คือ <b>จำนวนรอบของคลื่น</b> ยิ่งมาก คลื่นยิ่งถี่</p>' +
                '<p>ลองหมุนลูกบิด <b>f</b> ของจอที่ ' + (pickUnlocked("freq") + 1) + '</p>',
     vis:() => fig([{a:1, f:1, color:GRN}], "f = 1", 1) + fig([{a:1, f:3, color:GRN}], "f = 3", 1),
     ok:"f มากขึ้น คลื่นก็ถี่ขึ้น"},
    {id:"phase", title:"ลูกบิด φ · เฟส", wait:"phase", skip:() => pickUnlocked("phase") < 0,
     targets:() => [knobRoot(pickUnlocked("phase"), "phase")],
     body:() => '<p><b>φ</b> คือ <b>การเลื่อนคลื่นไปทางซ้าย/ขวา</b> เลือกได้ 0° · 90° · 180° · 270°</p>' +
                '<p>ลองหมุนลูกบิด <b>φ</b> ของจอที่ ' + (pickUnlocked("phase") + 1) + '</p>',
     vis:() => fig([{a:1, f:1, p:0, color:GRN}], "φ = 0°", 1) + fig([{a:1, f:1, p:90, color:GRN}], "φ = 90°", 1),
     ok:"คลื่นเลื่อนไปตามค่าเฟสที่เลือก"},
    {id:"lock", title:"🔒 ลูกบิดสีเหลือง = ผู้ดูแลบอกให้แล้ว", skip:() => lockedKnobs().length === 0,
     targets:() => lockedKnobs(),
     body:() => '<p>ลูกบิดที่ <b>เป็นสีเหลืองและมีรูปกุญแจ</b> (ไฮไลต์อยู่) ผู้ดูแลบอกค่าที่ถูกต้องให้ <b>ฟรีตอนเริ่มด่าน</b> หมุนไม่ได้อีก</p>' +
                '<p>จอที่ขึ้น <b>NO SIGNAL</b> คือจอที่ด่านนี้ไม่ได้ใช้</p>'},
    {id:"hint", title:"💡 ขอคำใบ้เพิ่ม", wait:"hint", skip:() => !HINT_BUTTON || state.bonusLeft <= 0,
     targets:() => [$("#hint")],
     body:() => '<p>ติดแล้ว? ปุ่มนี้ให้ผู้ดูแลบอกค่าที่ถูกต้อง <b>เพิ่ม 1 ค่า</b> (และล็อกให้) แต่ <b>หัก ' + HINT_COST + ' คะแนน</b> ต่อครั้ง และคำใบ้มีจำนวนจำกัด</p>' +
                '<p><b>ลองกดดูสิ</b> (ใน Tutorial ไม่หักคะแนนจริง)</p>',
     ok:"ได้ค่าที่ถูกต้องมา 1 ค่า และลูกบิดนั้นถูกล็อก 🔒"},
    {id:"submit", title:"📤 ส่งให้ผู้ดูแลตรวจสอบ", wait:"submit", targets:() => [$("#submit")],
     body:() => '<p>เมื่อคิดว่าได้แล้ว กดปุ่มนี้ ส่งได้ <b>' + MAX_ATT + ' ครั้ง</b> ต่อด่าน</p><p><b>ลองกดส่งตอนนี้เลย</b> ยังไม่ถูกก็ไม่เป็นไร</p>',
     ok:"ส่งแล้ว! ขั้นต่อไปดูผลการตรวจ"},
    {id:"feedback", title:"📋 ผลการตรวจ", skip:() => state.attempts === 0,
     targets:() => [$("#status")].concat(wrongKnobs()),
     body:() => '<p>ผู้ดูแลตอบกลับในแถบนี้</p>' +
                '<p>ลูกบิดที่ปรับ <b>ถูกแล้ว</b> จะ <b>เรืองแสงวาบหนึ่ง</b> (เหมือนตอนขอคำใบ้) แล้ว <b>ล็อกทันที</b> เป็นสีเหลือง 🔒</p>' +
                '<p><span class="r">ขีดสีแดง</span> บนลูกบิดที่ไฮไลต์ = ค่าที่ <b>ยังไม่ถูก</b> (หมุนกลับมาชี้ค่าที่ผิดเดิมก็แดงอีก) ปรับค่าที่เหลือแล้วส่งใหม่ได้ จนครบ ' + MAX_ATT + ' ครั้ง ครบแล้วยังไม่ถูก = แพ้</p>'},
    {id:"score", title:"🏆 คะแนน ด่าน และระดับ", targets:() => [$(".chips")],
     body:() => '<p>📊 <b>คะแนนเต็ม</b> ขึ้นกับจำนวนกราฟ (' + N + ' กราฟ = ' + FULL + ') ถูกครั้งที่ 1 ได้เต็ม · ครั้งที่ 2 หัก ' + ATT_PEN[1] + ' · ครั้งที่ 3 หัก ' + ATT_PEN[2] + ' · คำใบ้ครั้งละ −' + HINT_COST + '</p>' +
                '<p>🎯 ชนะ → <b>ด่านถัดไป</b> กราฟผสมเพิ่มทุก ' + (info.stages_per_graph || 3) + ' ด่าน (สูงสุด ' + (info.max_graphs || 6) + ') คะแนนสะสมเป็น <b>คะแนนรวม</b> · แพ้ → คะแนนรวมรีเซ็ต กลับไปด่าน 1</p>' +
                '<p>🎚 <b>ระดับความยาก</b> (นักเรียน / นิสิต / อาจารย์) เลือกที่หน้าเกมก่อนเริ่ม</p>' +
                '<p>⭐ <b>คะแนนสูงสุด</b> ของแต่ละระดับเก็บไว้ที่แถบด้านซ้าย</p>'},
    {id:"free", title:"🎮 ลองเล่นให้จบ", targets:() => [$("#bigscreen")], last:true,
     body:() => '<p>ตอนนี้ลอง <b>จูนค่าที่เหลือ</b> ให้เส้นเขียวทับเส้นเหลือง แล้วกดส่ง ด่านลองเล่นนี้ไม่นับคะแนนและไม่จับเวลา</p>' +
                '<p>พร้อมแล้วกด <b>✖ ออกจาก Tutorial</b> ที่ด้านบนของหน้านี้ แล้วเริ่มเกมจริงได้เลย</p>'},
  ];
  const END = () => state.solved
    ? {title:"🎉 ถอดรหัสสำเร็จ!", targets:() => [$("#bigscreen")],
       body:() => '<p>เส้นเขียวทับเส้นเหลืองพอดีแล้ว ในเกมจริงทุกด่านเล่นแบบนี้ คะแนนจะบวกเข้าคะแนนรวม</p><p>กด <b>✖ ออกจาก Tutorial</b> ที่ด้านบนของหน้านี้ เมื่อพร้อมเริ่มเกมจริง</p>'}
    : {title:"📡 ไม่เป็นไร ลองใหม่ในเกมจริงได้", targets:() => [$("#bigscreen")],
       body:() => '<p>ส่งครบ ' + MAX_ATT + ' ครั้งแล้วยังไม่ถูก ผู้ดูแลเฉลยให้แล้ว ในเกมจริงแบบนี้ = แพ้ (คะแนนรวมรีเซ็ต) แต่ที่นี่ไม่นับคะแนน</p><p>กด <b>✖ ออกจาก Tutorial</b> ที่ด้านบนของหน้านี้ เมื่อพร้อม</p>'};

  function clearHl(){ hl.forEach(e => { if (e) e.classList.remove("hl"); }); hl = []; }
  function place(target){
    cur = target || null;
    const a = app.getBoundingClientRect();
    coach.style.left = "0px"; coach.style.top = "0px";
    const cw = coach.offsetWidth, ch = coach.offsetHeight;
    if (!target){ coach.style.left = Math.max(0, (a.width - cw) / 2) + "px"; coach.style.top = "60px"; coach.classList.remove("above", "below"); return; }
    const r = target.getBoundingClientRect(), tx = r.left - a.left, ty = r.top - a.top, docH = Math.max(app.scrollHeight, app.offsetHeight, window.innerHeight - 8);   // กรอบ iframe สูงกว่าเนื้อหาเล็กน้อย วางกล่องไกด์ทับพื้นที่ว่างด้านล่างได้
    const below = ty + r.height + ch + 16 <= docH || ty - ch - 16 < 0;       // ปกติวางไว้ใต้เป้าหมาย ถ้าที่ไม่พอค่อยวางไว้เหนือ
    const top = below ? ty + r.height + 12 : ty - ch - 12;
    const left = Math.max(0, Math.min(a.width - cw, tx + r.width / 2 - cw / 2));
    coach.style.left = left + "px"; coach.style.top = top + "px";
    coach.classList.toggle("below", below); coach.classList.toggle("above", !below);
    coach.style.setProperty("--ax", Math.max(20, Math.min(cw - 20, tx + r.width / 2 - left)) + "px");
    const y0 = Math.min(ty, top), y1 = Math.max(ty + r.height, top + ch);   // ให้เห็นทั้งเป้าหมายและกล่องไกด์พร้อมกัน
    span.style.top = y0 + "px"; span.style.height = (y1 - y0) + "px";
    try { span.scrollIntoView({block:"nearest", behavior:"smooth"}); } catch (e) {}
  }
  function show(){
    clearHl();
    if (closed){ coach.hidden = true; $("#tourbtn").hidden = false; return; }
    $("#tourbtn").hidden = true;
    const st = ended ? END() : STEPS[idx], isWait = !!st.wait && !ended, isDone = isWait && done.has(st.id);
    const targets = (st.targets ? st.targets() : []).filter(Boolean);
    targets.forEach(t => t.classList.add("hl")); hl = targets;
    let dots = "";
    STEPS.forEach((_, q) => { dots += '<i class="' + (ended || q <= idx ? "on" : "") + '"></i>'; });
    coach.innerHTML =
      '<div class="ctop"><span>' + (ended ? "จบแล้ว" : "ขั้นที่ " + (idx + 1) + "/" + STEPS.length) + '</span><span class="cdots">' + dots + '</span>' +
      '<button class="cx" type="button" data-act="close" aria-label="ปิดไกด์" title="ปิดไกด์ (เปิดใหม่ได้ที่ปุ่ม 🎓 ไกด์)">✖</button></div>' +
      '<h3>' + st.title + '</h3><div class="cbody">' + st.body() + '</div>' +
      (st.vis ? '<div class="cvis">' + st.vis() + '</div>' : '') +
      (isWait ? (isDone ? '<div class="cok">✅ ' + st.ok + '</div>' : '<div class="cwait">👉 ลองทำดูเลย — ส่วนที่ไฮไลต์อยู่</div>') : '') +
      '<div class="cnav">' +
        (idx > 0 && !ended ? '<button class="cbtn" type="button" data-act="prev">◀ ย้อน</button>' : '') +
        '<span class="sp"></span>' +
        (isWait && !isDone ? '<button class="cbtn" type="button" data-act="next">ข้ามขั้นนี้ ⏭</button>' : '') +
        (ended || st.last ? '<button class="cbtn primary" type="button" data-act="close">ปิดไกด์</button>'
                          : (!isWait || isDone ? '<button class="cbtn primary" type="button" data-act="next">ถัดไป ▶</button>' : '')) +
      '</div>';
    coach.hidden = false;
    place(targets[0]);
  }
  function go(n, dir){
    while (n > 0 && n < STEPS.length - 1 && STEPS[n].skip && STEPS[n].skip()) n += dir;
    idx = Math.max(0, Math.min(STEPS.length - 1, n));
    show();
  }
  coach.addEventListener("click", e => {
    const b = e.target.closest("[data-act]");
    if (!b) return;
    const act = b.getAttribute("data-act");
    if (act === "close"){ closed = true; show(); }
    else if (act === "prev") go(idx - 1, -1);
    else if (act === "next") go(idx + 1, 1);
  });
  $("#tourbtn").addEventListener("click", () => { closed = false; show(); });
  new ResizeObserver(() => { if (!coach.hidden && cur) place(cur); }).observe(app);
  return {
    start(){ setTimeout(() => go(0, 1), 80); },
    event(type, d){                                         // บอร์ดแจ้งว่าผู้เล่นทำอะไรไป: knob (d.k) / hint / submit / finish
      if (type === "finish"){ ended = true; show(); return; }
      const st = STEPS[idx];
      if (ended || !st.wait || done.has(st.id)) return;
      if ((type === "knob" && st.wait === d.k) || type === st.wait){ done.add(st.id); show(); }
    },
  };
}
if (GAME.tutorial === true){ tour = makeTour(); tour.start(); }
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
    if (a.theme && a.theme !== THEME){ applyTheme(a.theme); if (onTheme) onTheme(); }   // Streamlit ส่งธีมที่เลือกมาทุกครั้งที่วาดใหม่
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
# ส่วนเสริม: SANDBOX (HTML + JavaScript) เปิดจากปุ่ม 🧪 SANDBOX ที่หน้าแรกหรือหน้าเกม
# กราฟ sin ที่ปรับ A, f, φ ได้อิสระ ไม่มีโจทย์ ไม่จำกัดค่าเหมือนในเกม
# =====================================================================
SANDBOX_HTML = r"""<!doctype html>
<html lang="th" data-theme="__THEME__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SINALL sandbox</title>
<style>
__THEME_CSS__
:root{
  --mono:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;
  --sans:"Noto Sans Thai","Leelawadee UI",Tahoma,system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.45 var(--sans);-webkit-text-size-adjust:100%}
#app{max-width:1200px;margin:0 auto;padding:10px 12px 14px}

.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:flex;align-items:baseline;gap:8px;padding:4px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bezel)}
.chip b{font:600 18px var(--mono);color:var(--mixtxt)}
.chip.a0 b{color:var(--recvtxt)}
.chip span{font-size:12px;color:var(--dim)}

.top{position:sticky;top:0;z-index:5;padding:8px 0;background:var(--bg)}
.screen{padding:6px 8px 6px;border:1px solid var(--line);border-radius:10px;background:var(--bg)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12px;color:var(--dim)}
.sw{display:inline-block;width:16px;height:4px;margin-right:6px;border-radius:2px;vertical-align:middle}
#scope{display:block;width:100%;height:250px}
#fx{min-height:20px;margin-top:2px;font:12px/1.5 var(--mono);color:var(--ink);overflow-wrap:anywhere}
.note{margin-top:2px;padding:5px 10px;border:1px solid var(--warn);border-radius:8px;background:var(--warnbg);font-size:13px}
.note:empty{display:none}

.ctrl{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}
.a0card{flex:1 1 380px;min-width:0;padding:6px 10px 8px;border:1px solid var(--line);border-radius:10px;background:var(--panel);--c:var(--sum)}
.a0h{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 10px}
.a0h b{font:600 14px var(--mono);color:var(--recvtxt)}
.a0h span{font-size:12px;color:var(--dim)}
.tools{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:6px 10px;border:1px solid var(--line);border-radius:10px;background:var(--panel);font-size:13px}
.tools label{display:flex;align-items:center;gap:4px;cursor:pointer;white-space:nowrap}
.tools input{margin:0;accent-color:var(--mix)}
.btn{padding:6px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bezel);color:var(--ink);font:600 13px var(--sans);white-space:nowrap;cursor:pointer}
.btn:hover{border-color:var(--mix)}
:focus-visible{outline:2px solid var(--mix);outline-offset:2px}

.row{display:grid;grid-template-columns:34px minmax(0,1fr) 60px;align-items:center;gap:8px;margin-top:4px}
.row.z{grid-template-columns:34px minmax(0,1fr) 60px 44px}
.sym{padding-left:5px;border-left:3px solid var(--c);font:600 14px var(--mono);color:var(--ink);line-height:1.05}     /* สีของเส้นอยู่ที่แถบข้างตัวอักษร (ตัวอักษรใช้สีหลักเพื่อให้อ่านชัดในทั้งสองธีม) */
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
.card.off .dot{background:var(--off)}
.card.off .tg{color:var(--dim);font-weight:400}
.ok{font-size:11px;color:var(--mixtxt)}
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
        <span><i class="sw" style="background:var(--sum)"></i>f(x) = a₀ + Σ (ผลรวมทุกเทอม)</span>
        <span><i class="sw" style="background:linear-gradient(90deg,var(--p0),var(--p1),var(--p2))"></i>แต่ละเทอม aₙcos(nx) + bₙsin(nx)</span>
        <span><i class="sw" style="background:repeating-linear-gradient(90deg,var(--sum) 0 4px,transparent 4px 7px)"></i>เส้น a₀</span>
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
        <input id="a0rg" type="range" min="-10" max="10" step="0.01" aria-label="a₀ (ยกกราฟทั้งหมด)">
        <input id="a0nb" type="number" min="-10" max="10" step="0.01" aria-label="a₀ (พิมพ์ค่า)">
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
  <p class="help">จอแสดง x = 0 ถึง 4π เรเดียน และ y = −20 ถึง 20 (คงที่ ไม่ขยายตามกราฟ) · เทอม n วนครบ n รอบทุก 2π · aₙ และ bₙ กำหนดเฟสร่วมกัน: aₙcos(θ) + bₙsin(θ) = R·sin(θ + φ) โดย R = √(aₙ² + bₙ²) และ φ = มุมของจุดบนแผงวงกลม (ลากจุดเพื่อปรับ aₙ, bₙ พร้อมกัน) · a₀, aₙ และ bₙ ปรับได้ตั้งแต่ −10 ถึง 10 ทีละ 0.01 · จอเล็กของแต่ละเทอมตรึงแกน y ไว้ที่ −15.14 ถึง 15.14 (ค่าสูงสุดที่เทอมหนึ่งเป็นไปได้ R = 10√2 ≈ 14.14 บวกลบ 1)</p>
</div>

<script>
(function(){
"use strict";
__THEME_JS__
const NPTS = 1201, NT = 6, TAU = 2 * Math.PI;
const HARD = 10;                                         // a₀, aₙ, bₙ ปรับได้ −10 ถึง 10 (ทีละ 0.01)
const PADMAX = HARD, PADRING = 5;                        // แผงวงกลมครอบคลุม ±10 (วงแหวนทุก 5)
const X_MAX = 4 * Math.PI, Y_LIM = 20;                   // จอใหญ่ล็อกขอบเขตไว้: x = 0 ถึง 4π (เรเดียน), y = −20 ถึง 20
// จอเล็กของแต่ละเทอม: ตรึงแกน y ด้วยกฎเดียวกับจอใหญ่ (สูงสุด + 1 / ต่ำสุด − 1) โดยใช้ค่าสูงสุดที่เทอมหนึ่งเป็นไปได้
// R = √(aₙ² + bₙ²) มากสุดตอน aₙ = bₙ = 10 คือ 10√2 ≈ 14.14 -> y = −15.14 ถึง 15.14 (ไม่ขยายตามค่าที่ปรับ จึงเห็นขนาดคลื่นเปลี่ยนจริง)
const MINI_Y = Math.hypot(HARD, HARD) + 1, MINI_TICK = 10;
const MONO = 'ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace';
const SUB = ["₀","₁","₂","₃","₄","₅","₆"];
const STORE = "allsin.sandbox.v2";                       // ชื่อคีย์เดิมจากตอนที่เกมชื่อ ALLSIN คงไว้เพื่อให้ค่าที่ผู้เล่นเคยตั้งใน SANDBOX ยังอยู่
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
    terms.push({on:!!t.on, a:r2(clamp(t.a, HARD)), b:r2(clamp(t.b, HARD))});   // ค่าที่จำไว้จากรุ่นเก่าอาจเกิน ±10 หรือมีทศนิยมมากกว่า 2 ตำแหน่ง
  }
  return {parts:o.parts !== false, sum:o.sum !== false, base:o.base !== false, a0:r2(clamp(o.a0, HARD)), terms};
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
  const intR = Math.abs(R - Math.round(R)) < 1e-9 && Math.round(R) >= 1 && Math.round(R) <= HARD;
  return onAxis && intR ? {A:Math.round(R), phi} : null;
}
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
  const F = frame(g, w, h, {l:22, r:4, t:6, b:6}, MINI_Y, fixedTicks(MINI_TICK, MINI_TICK), null, 9);   // y = ±15.14 ตรึงไว้ ขีดที่ −10, 0, 10
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
  for (let k = PADRING; k <= PADMAX; k += PADRING){ g.beginPath(); g.arc(cx, cy, r * k / PADMAX, 0, TAU); g.stroke(); }   // วงแหวนที่ R = 5, 10
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
  $("#note").textContent = msg.join(" · ");        // (ไม่แจ้งเตือนเมื่อกราฟเกินขอบ y: ส่วนที่เกินถูกตัดจากจอเงียบ ๆ)
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
    '<input class="rg" type="range" min="' + (-HARD) + '" max="' + HARD + '" step="0.01" aria-label="' + label + '">' +
    '<input class="nb" type="number" min="' + (-HARD) + '" max="' + HARD + '" step="0.01" aria-label="' + label + ' (พิมพ์ค่า)"></div>';
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
const snapPad = v => { const h = Math.round(v * 2) / 2; return Math.abs(v - h) <= 0.12 ? h : Math.round(v * 10) / 10; };   // แผงวงกลมหยาบกว่าแถบเลื่อน: ปัดเป็น 0.1 (ใกล้ครึ่งจำนวนเต็มจะดูดเข้าหา) ค่าละเอียดกว่านี้ใช้แถบเลื่อน/ช่องตัวเลข
function buildCards(){
  const host = $("#terms");
  S.terms.forEach((_, i) => {
    const n = i + 1, root = document.createElement("article");
    root.className = "card";
    root.style.setProperty("--c", "var(--p" + i + ")");
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
      c.rg[k].addEventListener("input", () => {            // ลากแถบเลื่อน: กราฟเปลี่ยนทันที (−10 ถึง 10 ทีละ 0.01)
        S.terms[i][k] = r2(parseFloat(c.rg[k].value)); afterChange(i);
      });
      c.nb[k].addEventListener("input", () => {            // พิมพ์ตัวเลข: เกิน ±10 ถูกตัดเป็น ±10 ปัดเป็นทศนิยม 2 ตำแหน่ง
        const v = parseFloat(c.nb[k].value);
        if (!Number.isFinite(v)) return;
        S.terms[i][k] = r2(clamp(v, HARD)); afterChange(i);
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
      const step = e.shiftKey ? 1 : (e.altKey ? 0.01 : 0.1), m = {ArrowRight:["b", 1], ArrowLeft:["b", -1], ArrowUp:["a", 1], ArrowDown:["a", -1]};   // ลูกศร 0.1 / Shift 1 / Alt 0.01
      if (!(e.key in m)) return;
      e.preventDefault();
      const [k, s] = m[e.key], t = S.terms[i];
      t[k] = r2(clamp(t[k] + s * step, HARD));
      afterChange(i);
    });
    c.mini._draw = () => drawMini(i); c.pad._draw = () => drawPad(i);
    ro.observe(c.mini); ro.observe(c.pad);
  });
}

const ro = new ResizeObserver(entries => entries.forEach(e => { if (e.target._draw) e.target._draw(); }));
scope._draw = drawBig; ro.observe(scope);

$("#a0rg").addEventListener("input", () => { S.a0 = r2(parseFloat($("#a0rg").value)); afterChange(); });
$("#a0nb").addEventListener("input", () => {
  const v = parseFloat($("#a0nb").value);
  if (Number.isFinite(v)){ S.a0 = r2(clamp(v, HARD)); afterChange(); }
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


# =====================================================================
# หน้าแรก: กราฟตัวอักษร SINALL (HTML + JavaScript) + แถบเลื่อนเดียว = จำนวนเทอม N ของอนุกรมฟูเรียร์
# __LETTERS_JSON__ จะถูกแทนด้วยผลของ letters_data() (สัมประสิทธิ์คำนวณด้วย numpy ฝั่ง Python ครั้งเดียวต่อเซสชัน)
# ลากแถบเลื่อนแล้วกราฟเปลี่ยนทันทีในเบราว์เซอร์ (ไม่รีรัน Streamlit): รวมแค่ N เทอมแรกของแต่ละตัวอักษร
# =====================================================================
HOME_HTML = r"""<!doctype html>
<html lang="th" data-theme="__THEME__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SINALL home</title>
<style>
__THEME_CSS__
:root{
  --mono:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;
  --sans:"Noto Sans Thai","Leelawadee UI",Tahoma,system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.45 var(--sans);-webkit-text-size-adjust:100%}
#app{max-width:1200px;margin:0 auto;padding:2px 2px 6px}
.screen{padding:6px;border:1px solid var(--line);border-radius:10px;background:var(--bg)}
#cv{display:block;width:100%;height:220px}
.ctl{display:grid;grid-template-columns:auto minmax(0,1fr) 40px;align-items:center;gap:10px;margin-top:8px;padding:6px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.ctl label{font-weight:600;white-space:nowrap}
.ctl input[type=range]{width:100%;margin:0;accent-color:var(--mix)}
.ctl output{font:700 16px var(--mono);color:var(--mixtxt);text-align:right}
:focus-visible{outline:2px solid var(--mix);outline-offset:2px}
@media (max-width:600px){#cv{height:130px} .ctl{grid-template-columns:minmax(0,1fr) 40px} .ctl label{grid-column:1 / -1}}
</style>
</head>
<body>
<div id="app">
  <div class="screen"><canvas id="cv" role="img" aria-label="ตัวอักษร SINALL วาดด้วยอนุกรมฟูเรียร์ 6 ชุด ชุดละหนึ่งตัวอักษร"></canvas></div>
  <div class="ctl">
    <label for="n">จำนวนเทอมของอนุกรม N</label>
    <input id="n" type="range" min="1" max="30" step="1" value="30">
    <output id="nv" for="n">30</output>
  </div>
</div>

<script>
(function(){
"use strict";
__THEME_JS__
const DATA = __LETTERS_JSON__;                 // {n_max, n_start, letters:[{name, P, Q, A[], B[], C[], D[]}]}
const NMAX = DATA.n_max, T = 1000;             // T = จำนวนจุดต่อเส้นโค้ง
const $ = s => document.querySelector(s);
const cv = $("#cv"), slider = $("#n"), out = $("#nv");
slider.max = String(NMAX); slider.value = String(DATA.n_start); out.textContent = slider.value;

// ตาราง cos(2πnt), sin(2πnt) ของ n = 1..NMAX คำนวณครั้งเดียว
const COS = [], SIN = [];
for (let n = 1; n <= NMAX; n++){
  const c = new Float64Array(T), s = new Float64Array(T);
  for (let j = 0; j < T; j++){ const a = 2 * Math.PI * n * j / T; c[j] = Math.cos(a); s[j] = Math.sin(a); }
  COS.push(c); SIN.push(s);
}
function trace(L, N){                          // รวม N เทอมแรก คืน {x, y} (ปิดเส้นโค้งด้วยจุดสุดท้าย = จุดแรก)
  const x = new Float64Array(T + 1).fill(L.P), y = new Float64Array(T + 1).fill(L.Q);
  for (let n = 0; n < N; n++){
    const a = L.A[n], b = L.B[n], c = L.C[n], d = L.D[n], co = COS[n], si = SIN[n];
    for (let j = 0; j < T; j++){ x[j] += a * co[j] + b * si[j]; y[j] += c * co[j] + d * si[j]; }
  }
  x[T] = x[0]; y[T] = y[0];
  return {x, y};
}
// ขอบเขตของภาพ: ครอบคลุมเส้นโค้งของทุกค่า N (1..NMAX) เพราะอนุกรมที่ตัดไว้ไม่กี่เทอมเลยขอบตัวอักษรได้ (ปรากฏการณ์ Gibbs)
// และตรึงไว้ ภาพจึงไม่ขยับ/ไม่ล้นกรอบเมื่อเลื่อนแถบ
const B = {x0:Infinity, x1:-Infinity, y0:Infinity, y1:-Infinity};
DATA.letters.forEach(L => {
  const x = new Float64Array(T).fill(L.P), y = new Float64Array(T).fill(L.Q);
  for (let n = 0; n < NMAX; n++){                        // เพิ่มทีละเทอม แล้วเก็บขอบเขตของผลรวมที่ N = n + 1
    const a = L.A[n], b = L.B[n], c = L.C[n], d = L.D[n], co = COS[n], si = SIN[n];
    for (let j = 0; j < T; j++){
      x[j] += a * co[j] + b * si[j]; y[j] += c * co[j] + d * si[j];
      if (x[j] < B.x0) B.x0 = x[j]; if (x[j] > B.x1) B.x1 = x[j];
      if (y[j] < B.y0) B.y0 = y[j]; if (y[j] > B.y1) B.y1 = y[j];
    }
  }
});

function setup(c){
  const r = c.getBoundingClientRect(), d = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
  if (c.width !== Math.round(w * d) || c.height !== Math.round(h * d)){ c.width = Math.round(w * d); c.height = Math.round(h * d); }
  const g = c.getContext("2d");
  g.setTransform(d, 0, 0, d, 0, 0);
  return {g, w, h};
}
function draw(){
  const {g, w, h} = setup(cv), N = parseInt(slider.value, 10);
  g.fillStyle = C.bg; g.fillRect(0, 0, w, h);
  const padX = 16, padY = 14, W = B.x1 - B.x0, H = B.y1 - B.y0;
  const sc = Math.min((w - 2 * padX) / W, (h - 2 * padY) / H);
  const ox = (w - sc * W) / 2 - sc * B.x0, oy = (h + sc * H) / 2 + sc * B.y0;
  const px = x => ox + sc * x, py = y => oy - sc * y;
  g.lineWidth = 1;                              // ตารางจาง ๆ แบบจอออสซิลโลสโคป: เส้นแนวนอนทุก 0.5 หน่วย แนวตั้งทุก 1 หน่วย
  for (let y = Math.ceil(B.y0 * 2) / 2; y <= B.y1 + 1e-9; y += 0.5){
    g.strokeStyle = Math.abs(y) < 1e-9 ? C.axis : (Math.abs(y - Math.round(y)) < 1e-9 ? C.grid : C.gridMinor);
    g.beginPath(); g.moveTo(px(B.x0) - 8, py(y)); g.lineTo(px(B.x1) + 8, py(y)); g.stroke();
  }
  for (let x = Math.ceil(B.x0); x <= B.x1 + 1e-9; x += 1){
    g.strokeStyle = C.gridMinor;
    g.beginPath(); g.moveTo(px(x), py(B.y0) + 6); g.lineTo(px(x), py(B.y1) - 6); g.stroke();
  }
  g.lineJoin = "round"; g.lineCap = "round"; g.lineWidth = 3.2;
  DATA.letters.forEach((L, k) => {
    const t = trace(L, N), col = PALETTE[k % PALETTE.length];
    g.strokeStyle = col; g.shadowColor = col; g.shadowBlur = TH.blur;
    g.beginPath();
    for (let j = 0; j <= T; j++){ const X = px(t.x[j]), Y = py(t.y[j]); if (j) g.lineTo(X, Y); else g.moveTo(X, Y); }
    g.stroke();
  });
  g.shadowBlur = 0;
}
slider.addEventListener("input", () => { out.textContent = slider.value; draw(); });
new ResizeObserver(draw).observe(cv);
draw();
})();
</script>
</body>
</html>
"""


# ใส่ตัวแปรสี/ตารางสีของธีมลงในทุกหน้า HTML (ส่วนที่เลือกธีมคือแอตทริบิวต์ data-theme ซึ่ง themed() ตั้งตอนฝัง)
BOARD_HTML = fill_theme(BOARD_HTML)
SANDBOX_HTML = fill_theme(SANDBOX_HTML)
HOME_HTML = fill_theme(HOME_HTML)


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
    ซึ่งเกมยังเล่นได้ครบ เพียงแต่ปุ่มในหน้าสรุปจะไม่แสดง (ใช้ปุ่มบนแผงควบคุมของหน้าเกมแทน)
    """
    try:
        import hashlib
        import os
        import tempfile
        import streamlit.components.v1 as components

        html = themed(BOARD_HTML.replace("__GAME_JSON__", "null"), DEFAULT_THEME)   # null = รอรับโจทย์จาก Streamlit (ธีมจริงมาทางอาร์กิวเมนต์ theme)
        tag = hashlib.sha256(html.encode("utf-8")).hexdigest()[:10]
        folder = os.path.join(tempfile.gettempdir(), "sinall_board_" + tag)
        page = os.path.join(folder, "index.html")
        if not os.path.exists(page):
            os.makedirs(folder, exist_ok=True)
            tmp = page + ".%d.tmp" % os.getpid()
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(html)
            os.replace(tmp, page)
        return components.declare_component("sinall_board_" + tag, path=folder)
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
        hint_button=level["hints"],                         # False = ซ่อนปุ่มคำใบ้ (ตอนนี้ทุกระดับมีปุ่ม)
        hint_pool=game.get("hint_pool", 0),                 # คำใบ้ที่กดได้ในด่านนี้ (สะสมมาจากด่านก่อน ๆ)
        hint_per_stage=HINT_PER_STAGE,                      # ผ่านด่านนี้แล้วจะได้เพิ่มกี่ครั้ง (ไว้เขียนในหน้าสรุป)
        amp_max=level["amp_max"],                           # ช่วงลูกบิดแอมพลิจูด: จำนวนเต็ม [-amp_max, amp_max] ยกเว้น 0
        freq_max=level["freq_max"],                         # ช่วงลูกบิดความถี่: จำนวนเต็ม [-freq_max, freq_max] ยกเว้น 0
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
        return BOARD_COMPONENT(game=payload, height=BOARD_HEIGHT, theme=current_theme(), key="board_%d" % game["id"], default=None)
    embed(themed(BOARD_HTML.replace("__GAME_JSON__", json.dumps(payload)), current_theme()), BOARD_HEIGHT)
    return None


def handle_board_event(event, game):
    """รับเหตุการณ์จากบอร์ด: เก็บคะแนน (เกมละครั้ง) และทำตามปุ่มในหน้าสรุปผล

    ชนะ -> คะแนนรวมบวกคะแนนเกมนี้ อัปเดตคะแนนสูงสุดของระดับนั้นถ้าคะแนนรวมสูงกว่าเดิม และไปด่านถัดไป (ระดับความยากยังล็อกอยู่)
    แพ้ -> คะแนนรวมรีเซ็ตเป็น 0 (คะแนนสูงสุดของระดับนั้นยังอยู่) กลับไปด่าน 1 และเกมจบ: ปลดล็อกการเลือกระดับความยาก
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
        hints = max(0, min(hints, game.get("hint_pool", 0), len(game["bonus"])))   # ใช้ได้ไม่เกินคำใบ้ที่มีตอนเริ่มด่าน
        score = game_score(status, attempts, hints, len(game["components"]))
        ss["last_status"] = status
        level = game.get("difficulty", DEFAULT_LEVEL)       # คะแนนสูงสุดเก็บแยกตามระดับความยากของเกมนี้
        if status == "won":
            ss["total_score"] = ss.get("total_score", 0) + score
            record_high(level, ss["total_score"])
            ss["stage"] = game.get("stage", 1) + 1          # ผ่านด่าน -> ด่านถัดไป
            # คำใบ้สะสม: ที่ใช้ไปแล้วหมดไป ที่เหลือเก็บต่อ แล้วผ่านด่านได้เพิ่ม +1 (ด่านใหม่ไม่รีเซ็ต)
            ss["hint_pool"] = max(0, game.get("hint_pool", 0) - hints) + HINT_PER_STAGE
        else:
            record_high(level, ss.get("total_score", 0))
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
    embed(themed(SANDBOX_HTML, current_theme()), SANDBOX_HEIGHT)


def game_running():
    """True ตั้งแต่เริ่มเกมจนเกมจบ (บอร์ดรายงานว่าชนะ/แพ้/หมดเวลาแล้ว) ช่วงนี้ห้ามเข้า SANDBOX
    (ถ้าบอร์ดรายงานกลับมาไม่ได้ เช่นใช้ HTML ฝังตรง ๆ จะไม่ล็อก เพราะไม่รู้ว่าเกมจบเมื่อไร)"""
    ss = st.session_state
    game = ss.get("game")
    return BOARD_COMPONENT is not None and game is not None and ss.get("scored_gid") != game["id"]


def set_mode(mode):
    """สลับหน้าจอหลัก: "home" (หน้าแรก) / "game" (หน้าเกม) / "sandbox" / "tutorial" (ใช้เป็น callback ของปุ่ม)
    เข้า SANDBOX จะจำหน้าที่มาไว้ (sandbox_back) เพื่อให้ปุ่มกลับไปถูกที่ (หน้าแรกหรือหน้าเกม)"""
    ss = st.session_state
    if mode == "sandbox":
        if game_running():
            return                          # ระหว่างเล่นเกมเข้า SANDBOX ไม่ได้
        if ss.get("mode", "home") != "sandbox":
            ss["sandbox_back"] = ss.get("mode", "home")
    ss["mode"] = mode


def leave_sandbox():
    """ปุ่มกลับจาก SANDBOX: ไปหน้าที่เข้ามา (หน้าแรกหรือหน้าเกม)"""
    st.session_state["mode"] = st.session_state.get("sandbox_back", "home")


def box(key):
    """กล่องที่มีชื่อ (key) ไว้ให้ CSS อ้างถึง: Streamlit จะใส่ class "st-key-<key>" ให้"""
    try:
        return st.container(key=key)
    except TypeError:                     # Streamlit รุ่นเก่าไม่มี key: ยังใช้งานได้ แต่แสดงทั้งสองหน้าซ้อนกัน
        return st.container()


def wide_button(label, **kwargs):
    """ปุ่มเต็มความกว้างของคอลัมน์ที่วางอยู่"""
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


def level_summary(i):
    """คำอธิบายระดับความยากลำดับที่ i สำหรับหน้ากติกา: จับเวลาไหม + ช่วง A และ f + คำใบ้เริ่มต้น"""
    d = DIFFICULTIES[i]
    return "%s · A ปรับได้ −%d ถึง %d และ f ปรับได้ −%d ถึง %d (ไม่รวม 0) · คำใบ้เริ่มต้น %d ครั้ง" % (
        "จับเวลา" if d["timer"] else "ไม่จับเวลา", d["amp_max"], d["amp_max"], d["freq_max"], d["freq_max"], d["start_hints"])


def show_rules():
    full_table =" · ".join("%d กราฟ = %d" % (n, v) for n, v in sorted(FULL_SCORE.items()))
    time_table = " · ".join("%d กราฟ = %d นาที" % (n, time_limit(n) // 60) for n in sorted(FULL_SCORE))
    st.markdown(
        f"""
**วิธีเล่น**
1. กด **▶ เริ่มเกม** ที่หน้าแรกเพื่อไปที่หน้าเกม เลือกระดับความยาก แล้วกด **▶ เริ่มเกม** อีกครั้ง ระบบจะสุ่มสัญญาณผสมที่ประกอบด้วยกราฟ sin จำนวน *n* กราฟ ตามด่านที่เล่นอยู่
2. **ด่าน** เริ่มที่ด่าน 1 ซึ่งมีกราฟผสมแค่ {MIN_GRAPHS} กราฟ ผ่านครบทุก {STAGES_PER_GRAPH} ด่านจะเพิ่มกราฟผสม +1 กราฟ (สูงสุด {MAX_GRAPHS} กราฟ): {stage_table()} ถ้าชนะจะได้เล่นด่านถัดไป ถ้าแพ้จะกลับไปเริ่มที่ด่าน 1
3. **ระดับความยาก** เลือกด้วยแถบเลื่อนที่หน้าเกม เลือกได้ **ก่อนกดเริ่มเกมเท่านั้น** พอกดเริ่มแล้วจะล็อกตลอดทุกด่านจนกว่าเกมจะจบ (แพ้ หมดเวลา หรือกด 🏠 กลับหน้าแรก) จึงเลือกใหม่ได้:
   - **{DIFFICULTIES[0]["label"]}** {level_summary(0)}
   - **{DIFFICULTIES[1]["label"]}** {level_summary(1)}
   - **{DIFFICULTIES[2]["label"]}** {level_summary(2)}
4. จอเล็กที่ใช้งานได้จะมี *n* จอ ส่วนจอที่เหลือจะขึ้นคำว่า **NO SIGNAL**
5. แต่ละจอมีลูกบิด 3 อัน และแสดงกราฟ y = A·sin(f·x + φ)
   - **แอมพลิจูด A** เป็นจำนวนเต็มตั้งแต่ −m ถึง m **ยกเว้น 0** (m = {DIFFICULTIES[0]["amp_max"]} / {DIFFICULTIES[1]["amp_max"]} / {DIFFICULTIES[2]["amp_max"]} ตามระดับ ง่าย / ปานกลาง / ยาก)
   - **ความถี่ f** เป็นจำนวนเต็มตั้งแต่ −m ถึง m **ยกเว้น 0** (m = {DIFFICULTIES[0]["freq_max"]} / {DIFFICULTIES[1]["freq_max"]} / {DIFFICULTIES[2]["freq_max"]} ตามระดับ ง่าย / ปานกลาง / ยาก)
   - **เฟส φ** เลือกได้ 0°, 90°, 180° หรือ 270°
6. ตอนเริ่มด่าน ผู้ดูแลจะบอกค่าที่ถูกต้องให้ฟรีแบบสุ่ม (ลูกบิดสีเหลืองที่ล็อก 🔒) ไม่เกิน 2 ค่าต่อจอ (ทุกระดับ) ไม่นับรวมกับคำใบ้ในข้อ 7
7. ปุ่ม **💡 ขอคำใบ้เพิ่ม** (ทุกระดับ) ใช้ **คำใบ้สะสม** ของรอบ: เริ่มรอบด้วยคำใบ้ {DIFFICULTIES[0]["start_hints"]} / {DIFFICULTIES[1]["start_hints"]} / {DIFFICULTIES[2]["start_hints"]} ครั้ง (ง่าย / ปานกลาง / ยาก) และ **ทุกครั้งที่ผ่านด่านได้เพิ่ม +{HINT_PER_STAGE} ครั้ง** สะสมไปได้เรื่อย ๆ ไม่มีเพดาน คำใบ้ที่ **ใช้ไปแล้วจะหมดไป** ขึ้นด่านใหม่จะไม่รีเซ็ต เหลือเท่าที่สะสมไว้ แต่ละครั้งผู้ดูแลจะบอกค่าที่ถูกต้องเพิ่ม 1 ค่า (สุ่มจากค่าที่ยังไม่รู้) และ **หัก {HINT_COST} คะแนน** (ถ้าแพ้หรือกลับหน้าแรก รอบใหม่จะเริ่มนับจากคำใบ้เริ่มต้นของระดับอีกครั้ง)
8. จอใหญ่แสดงสัญญาณที่รับได้ (สีเหลือง) ซ้อนกับผลรวมของทุกจอที่คุณจูน (สีเขียว) เป้าหมายคือให้สองเส้นทับกันพอดี (x = 0 ถึง 4π เรเดียน ส่วนแกน y **ตรึงไว้ตลอดด่าน** ตามกราฟสีเหลืองของด่านนั้น คือ ค่าต่ำสุด − 1 ถึง ค่าสูงสุด + 1 ไม่ขยายตามกราฟที่คุณผสม ถ้ากราฟสีเขียวเกินขอบเขตส่วนที่เกินจะถูกตัดออกจากจอ) จอเล็กแต่ละจอก็ **ตรึงแกน y ตลอดด่าน** ด้วยกฎเดียวกัน คือ ค่าต่ำสุด − 1 ถึง ค่าสูงสุด + 1 ของกราฟเฉลยของจอนั้น (กราฟของคุณที่เกินขอบเขตจะถูกตัดออกจากจอ)
9. **⏱ จับเวลาถอยหลัง** (ระดับนิสิตและอาจารย์) เริ่มนับเมื่อกดเริ่มเกม: เวลาพื้นฐาน {TIME_BASE // 60} นาที และ +{TIME_PER_EXTRA_GRAPH // 60} นาทีต่อกราฟที่ต้องตอบเพิ่ม (สูงสุด +{TIME_MAX_EXTRA // 60} นาที): {time_table} เวลา **ไม่มีผลต่อคะแนน** แต่ถ้าเวลาหมดเกมจะ **จบทันที** (นับเป็นแพ้) ระดับนักเรียนไม่จับเวลา
   - **เวลาลดลงเมื่อเล่นไปไกล:** {shrink_text()} (จะมีแจ้งเตือนก่อนเข้าด่านที่ {TIME_SHRINK_FROM} หนึ่งครั้ง)
10. เมื่อมั่นใจแล้วกด **ส่งให้ผู้ดูแลตรวจสอบ** ส่งได้สูงสุด **{MAX_ATTEMPTS} ครั้ง** ผู้ดูแลตรวจจากรูปคลื่น ถ้าได้กราฟเดียวกันก็ถือว่าถูก เช่น A = −1, f = 1, φ = 180° ให้กราฟเดียวกับ A = 1, f = 1, φ = 0°
11. ถ้าส่งแล้วยังไม่ถูก ค่าไหนที่ตรงกับเฉลยแล้ว ลูกบิดนั้นจะ **เรืองแสงวาบหนึ่ง** (แบบเดียวกับตอนขอคำใบ้) แล้ว **ถูกล็อกทันที** (ลูกบิดสีเหลือง 🔒 เหมือนค่าที่ผู้ดูแลล็อกให้ตอนเริ่ม) ส่วนค่าที่ยังไม่ถูก **ขีดบนลูกบิดจะเป็นสีแดง** และถ้าหมุนไปมาแล้วเผลอกลับมาชี้ค่าเดิมที่ผิด ก็จะเป็นขีดแดงอีก แล้วคุณปรับค่าที่เหลือเล่นต่อได้
12. **คะแนนเต็ม** ขึ้นกับจำนวนกราฟที่ต้องตอบ: {full_table}
   - ถูกหมดตั้งแต่ครั้งที่ 1 ได้ **เต็ม − จำนวนครั้งที่กดคำใบ้**
   - ถูกหมดในครั้งที่ 2 ได้ **เต็ม − {ATTEMPT_PENALTY[1]} − จำนวนครั้งที่กดคำใบ้**
   - ถูกหมดในครั้งที่ 3 ได้ **เต็ม − {ATTEMPT_PENALTY[2]} − จำนวนครั้งที่กดคำใบ้**
13. ชนะแล้วคะแนนจะ **สะสมเป็นคะแนนรวม** และได้เล่นด่านถัดไป แต่ถ้าส่งครบ {MAX_ATTEMPTS} ครั้งแล้วยังไม่ถูก หรือเวลาหมด คุณจะแพ้: **คะแนนรวมรีเซ็ตเป็น 0 และกลับไปด่าน 1** (ระบบยังเก็บ **⭐ คะแนนสูงสุดของแต่ละระดับ** ไว้ให้ที่แถบด้านซ้าย) พร้อมสรุปผล เฉลยที่ถูกต้อง และปุ่ม **🔄 เริ่มเกมใหม่** กับ **🧪 SANDBOX**
14. **กดเริ่มเกมแล้วสุ่มโจทย์ใหม่ไม่ได้** ปุ่มเริ่มเกมบนหน้าเกมจะถูกล็อกจนกว่าเกมจะจบ ถ้าอยากเลิกกลางคันให้กด **🏠 กลับหน้าแรก** บนหน้าเกม (ต้องกดยืนยัน) ซึ่ง **นับเป็นแพ้** คือคะแนนรวมรีเซ็ตเป็น 0 และกลับไปเริ่มที่ด่าน 1 (⭐ คะแนนสูงสุดของระดับนั้นยังเก็บไว้) แล้วจะเปลี่ยนระดับความยากได้ใหม่

อยากลองเล่นกับกราฟก่อน? กดปุ่ม **🧪 SANDBOX** ที่หน้าแรก (หรือบนหน้าเกม) หน้าจอจะเปลี่ยนเป็นเครื่องสังเคราะห์อนุกรมฟูเรียร์ ปรับ a₀, aₙ, bₙ ของแต่ละ n ได้ตามใจ
ปุ่มนี้ใช้ได้ **ก่อนเริ่มเกมและหลังเกมจบเท่านั้น** ตั้งแต่เริ่มเกมจนเกมจบปุ่มจะถูกล็อก
"""
    )


SANDBOX_HELP = r"""
- **a₀** ยกกราฟทั้งหมดขึ้นหรือลง (เลื่อนในแนวตั้ง) ในเกม a₀ เท่ากับ 0 เสมอ แต่ใน SANDBOX ปรับได้ตั้งแต่ −10 ถึง 10 ทีละ 0.01
- **n** (1 ถึง 6) เป็นความถี่ของแต่ละเทอม: cos(nx) และ sin(nx) วนครบ n รอบทุก 2π
  เกมผสมกราฟได้สูงสุด 6 กราฟ จึงมีเทอม n = 1 ถึง 6 (ความถี่ f ของลูกบิดในเกมก็คือ n)
- **aₙ, bₙ** เป็นสัมประสิทธิ์ของ cos และ sin ของเทอมที่ n สองค่านี้กำหนด **เฟส** ของคลื่นร่วมกัน
  (และขนาดของคลื่นด้วย): ลากจุดบนแผงวงกลม มุมของจุดคือเฟส φ ระยะจากกลางวงคือขนาด R
  aₙ และ bₙ ปรับได้ตั้งแต่ −10 ถึง 10 ทีละ 0.01 (แถบเลื่อนหรือพิมพ์ในช่องตัวเลข แผงวงกลมปรับได้ละเอียดแค่ 0.1)
- **ขอบเขตของจอ** คงที่เสมอ: x = 0 ถึง 4π เรเดียน (2 คาบของ n = 1) จอใหญ่ y = −20 ถึง 20
  ส่วนจอเล็กของแต่ละเทอม y = −15.14 ถึง 15.14 (ค่าสูงสุดที่เทอมหนึ่งเป็นไปได้ R = 10√2 ≈ 14.14 บวกลบ 1)
- ในที่นี้ x วัดเป็นเรเดียน ถ้าวัด x เป็นจำนวนคาบ (t = x/2π) จะเขียนเทอมเดียวกันเป็น cos(2πnt) และ sin(2πnt)
  ซึ่งเป็นอนุกรมฟูเรียร์ชุดเดียวกัน
"""


# =====================================================================
# ส่วนที่ 2: หน้าเว็บ Streamlit
#   หน้าแรก (home)  : กราฟ SINALL + แถบเลื่อน N + ปุ่ม เริ่มเกม / กติกา / SANDBOX  (ข้อความกติกาโผล่เมื่อกดปุ่ม กติกา)
#   หน้าเกม (game)  : แผงควบคุม (ระดับความยาก ปุ่มเริ่ม ด่าน คำใบ้ คะแนนรวม กลับหน้าแรก SANDBOX) + บอร์ดเกม
#   SANDBOX         : เครื่องสังเคราะห์อนุกรมฟูเรียร์
#   Tutorial        : ด่านลองเล่นที่มีไกด์พาทำ (ไกด์อยู่ในบอร์ด)  ถามครั้งเดียวหลังกดเริ่มเกมครั้งแรก
#   โหมดสว่าง/มืด   : ปุ่มที่แถบบนสุดของทุกหน้า (current_theme / toggle_theme / page_css) ทุกหน้า HTML ใช้ตารางสีชุดเดียวกัน THEME_COLORS
#   แถบด้านซ้าย     : แสดงเฉพาะ ⭐ คะแนนสูงสุดของแต่ละระดับความยาก
# =====================================================================
PAGE_CSS = string.Template("""
:root{color-scheme:$scheme}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stMainBlockContainer"]{background:$bg !important;color:$ink !important}
[data-testid="stHeader"]{background:$bg !important;color:$ink !important}
[data-testid="stSidebar"],[data-testid="stSidebarContent"],[data-testid="stSidebar"] > div:first-child{background:$panel !important}
[data-testid="stSidebar"]{border-right:1px solid $line}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{color:$ink !important}
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stMarkdownContainer"] p,.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stMarkdownContainer"] strong,.stApp [data-testid="stMarkdownContainer"] em{color:$ink !important}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] *{color:$dim !important}
.stApp [data-testid="stWidgetLabel"],.stApp [data-testid="stWidgetLabel"] *,.stApp label,.stApp label p{color:$ink !important}
.stApp [data-testid="stMetricLabel"],.stApp [data-testid="stMetricLabel"] *{color:$dim !important}
.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricValue"] *{color:$mixtxt !important}
.stApp .katex,.stApp .katex *{color:$ink !important}
.stApp hr{border-color:$line !important}
.stApp a{color:$mixtxt !important}
.stApp button[data-testid="stBaseButton-secondary"],.stApp .stButton > button{background:$bezel !important;border:1px solid $line !important;color:$ink !important}
.stApp .stButton > button *{color:inherit !important}
.stApp button[data-testid="stBaseButton-secondary"]:hover:not(:disabled),.stApp .stButton > button:hover:not(:disabled){border-color:$mix !important;color:$ink !important}
.stApp button[data-testid="stBaseButton-primary"],.stApp .stButton > button[kind="primary"]{background:$pbg !important;border:1px solid $pborder !important;color:$pink !important}
.stApp button[data-testid="stBaseButton-primary"]:hover:not(:disabled),.stApp .stButton > button[kind="primary"]:hover:not(:disabled){filter:brightness(1.1);color:$pink !important}
.stApp .stButton > button:disabled{opacity:.5 !important}
.stApp [data-testid="stSliderThumbValue"],.stApp [data-testid="stSliderThumbValue"] *{color:$mixtxt !important}
.stApp [data-testid="stTickBarMin"],.stApp [data-testid="stTickBarMax"]{color:$dim !important}
.stApp [data-baseweb="slider"] [role="slider"]{background-color:$mix !important}
.stApp [data-testid="stVerticalBlockBorderWrapper"]{border-color:$line !important}
.stApp [data-testid="stExpander"],.stApp [data-testid="stExpander"] details{border-color:$line !important}
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary *{color:$ink !important}
.stApp [data-testid="stAlert"],.stApp [data-testid="stAlertContainer"]{background:$warnbg !important}
.stApp [data-testid="stAlert"] *{color:$ink !important}
""")


def page_css(theme):
    """CSS ที่ทับสีของหน้าเว็บ Streamlit เองให้เป็นโหมดมืด/สว่างตามที่เลือก (ให้กลมกลืนกับบอร์ดที่ฝังอยู่ ซึ่งใช้ตารางสีชุดเดียวกัน)
    ใช้ data-testid ของส่วนต่าง ๆ ของ Streamlit ถ้ารุ่นไหนไม่มีส่วนนั้นก็แค่ไม่มีผล"""
    c = dict(THEME_COLORS[theme if theme in THEMES else DEFAULT_THEME])
    c["scheme"] = theme if theme in THEMES else DEFAULT_THEME
    return PAGE_CSS.substitute(c)


PAGE_TITLES = {"home": "📡 SINALL", "game": "📡 SINALL", "sandbox": "🧪 SANDBOX", "tutorial": "🎓 Tutorial"}


def header_row(mode):
    """แถบบนสุดของทุกหน้า: ชื่อหน้า + ปุ่มสลับโหมดสว่าง/มืด (ปุ่มแสดงโหมดที่จะสลับไป)"""
    try:
        cols = st.columns([4, 1], vertical_alignment="center")
    except TypeError:                     # Streamlit รุ่นเก่าไม่มี vertical_alignment
        cols = st.columns([4, 1])
    with cols[0]:
        st.title(PAGE_TITLES.get(mode, PAGE_TITLES["home"]))
    with cols[1]:
        wide_button("☀️ โหมดสว่าง" if current_theme() == "dark" else "🌙 โหมดมืด", key="theme_btn", on_click=toggle_theme,
                    help="สลับระหว่างโหมดมืดและโหมดสว่าง (ใช้กับทุกหน้า)")


def panel():
    """กล่องมีกรอบสำหรับจัดกลุ่มของบนหน้าเว็บ (Streamlit รุ่นเก่าที่ไม่มี border ใช้กล่องเปล่าแทน)"""
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


def show_story():
    """เรื่องราวของเกม (ส่วนหนึ่งของหน้ากติกา)"""
    st.markdown(
        "คุณคือ **นายวิทยุ** ประจำสถานีรับสัญญาณ คืนนี้เสาอากาศจับสัญญาณปริศนาจากอวกาศได้ "
        "สัญญาณนี้เป็นคลื่นผสมของกราฟ sin หลายตัว ตามอนุกรมฟูเรียร์"
    )
    st.latex(r"f(x)=a_0+\sum_{n=1}^{\infty}\left(a_n\cos(nx)+b_n\sin(nx)\right)")
    st.markdown(
        "งานของคุณคือ **แยกสัญญาณผสมออกมาเป็นกราฟ sin ให้ครบทุกตัว** "
        "ด้วยเครื่องจูน 6 จอ แล้วส่งให้ผู้ดูแลตรวจสอบ"
    )


def show_home():
    """หน้าแรก: กราฟตัวอักษร SINALL (ปรับจำนวนเทอม N ได้ด้วยแถบเลื่อนเดียว) และปุ่มเริ่มเกม / กติกา / SANDBOX"""
    ss = st.session_state
    if "letters_data" not in ss:
        ss["letters_data"] = letters_data()              # คำนวณครั้งเดียวต่อเซสชัน
    embed(themed(HOME_HTML.replace("__LETTERS_JSON__", json.dumps(ss["letters_data"])), current_theme()), HOME_HEIGHT)
    c1, c2, c3 = st.columns(3)
    with c1:
        wide_button("▶ เริ่มเกม", key="home_start", type="primary", on_click=press_start)
    with c2:
        wide_button("📖 กติกา", key="home_rules", on_click=toggle_rules,
                    help="แสดง/ซ่อนเรื่องราวและกติกาทั้งหมด")
    with c3:
        wide_button("🧪 SANDBOX", key="home_sandbox", on_click=set_mode, args=("sandbox",),
                    help="ทดลองปรับอนุกรมฟูเรียร์อย่างอิสระ")
    if ss.get("show_rules"):
        with panel():                                    # ข้อความกติกาโผล่มาเมื่อกดปุ่ม กติกา เท่านั้น
            show_story()
            show_rules()
            d1, d2 = st.columns(2)
            with d1:
                wide_button("🎓 ดู Tutorial", key="rules_tutorial", on_click=open_tutorial, args=("home",))
            with d2:
                wide_button("✖ ปิดกติกา", key="rules_close", on_click=toggle_rules)


def show_tutorial_question():
    """คำถามหลังกดเริ่มเกมครั้งแรกของเซสชัน: ต้องการดู Tutorial ไหม (ถามครั้งเดียว ดู press_start)"""
    with panel():
        st.markdown("**🎓 อยากดู Tutorial ไหม?** เป็นด่านลองเล่นที่มีไกด์พาทำทีละขั้น ใช้เวลาไม่กี่นาที ข้ามได้ และจะถามครั้งเดียวเท่านั้น")
        c1, c2 = st.columns(2)
        with c1:
            wide_button("🎓 ดู Tutorial", key="tut_yes", type="primary", on_click=open_tutorial, args=("game",))
        with c2:
            wide_button("⏭ ข้าม ไปเล่นเลย", key="tut_no", on_click=skip_tutorial_question)


def practice_payload():
    """โจทย์ของด่านลองเล่นใน Tutorial: คงที่ทุกครั้ง (ไกด์จะได้พูดถึงลูกบิดแต่ละตัวได้ตรง ๆ) 2 กราฟ ระดับง่าย ไม่จับเวลา
        จอ 1: A = 2, f = 2, φ = 90°   (ผู้ดูแลล็อก f ให้)      จอ 2: A = −1, f = 3, φ = 180°   (ผู้ดูแลล็อก φ ให้)
    ที่เหลือต้องหมุนเอง: จอ 1 หมุน A กับ φ, จอ 2 หมุน A กับ f  ไกด์ (JavaScript ในบอร์ด) พาลองหมุนทีละลูกบิด ขอคำใบ้ และส่งตรวจ
    คำใบ้เพิ่มเรียงตามลำดับ bonus  ไม่ส่งคะแนนกลับมาที่ Streamlit (practice)"""
    cfg = DIFFICULTIES[0]
    game = {"id": 0, "components": [{"amp": 2, "freq": 2, "phase": 90}, {"amp": -1, "freq": 3, "phase": 180}],
            "hints": [["freq"], ["phase"]],
            "bonus": [[0, "amp"], [1, "amp"], [1, "freq"], [0, "phase"]],
            "hint_pool": max(1, cfg["start_hints"]), "stage": 1, "difficulty": 0, "base_total": 0, "base_high": 0}
    payload = board_payload(game)
    payload.update(practice=True, tutorial=True, difficulty="ลองเล่น (Tutorial)",
                   tour_info={"stages_per_graph": STAGES_PER_GRAPH, "max_graphs": MAX_GRAPHS})
    return payload


def show_tutorial():
    """หน้า Tutorial: ด่านลองเล่นบนบอร์ดจริง มีไกด์ลอยอยู่ติดกับส่วนที่พูดถึง (ไกด์ทำงานในบอร์ด) คะแนนไม่ถูกนับ"""
    ss = st.session_state
    left, _ = st.columns([1, 3])
    with left:
        wide_button("✖ ออกจาก Tutorial", key="tut_exit", on_click=close_tutorial)
    payload = practice_payload()
    if BOARD_COMPONENT is not None:
        BOARD_COMPONENT(game=payload, height=BOARD_HEIGHT, theme=current_theme(),
                        key="tutorial_board_%d" % ss.get("tutorial_count", 0), default=None)
    else:
        embed(themed(BOARD_HTML.replace("__GAME_JSON__", json.dumps(payload)), current_theme()), BOARD_HEIGHT)


def show_game_controls(has_game):
    """แผงควบคุมบนหน้าเกม (เดิมอยู่ที่แถบด้านซ้าย): ระดับความยาก, ด่าน, คำใบ้สะสม, คะแนนรวม, ปุ่มเริ่ม/ด่านถัดไป,
    🏠 กลับหน้าแรก, 🧪 SANDBOX  ต้องเรียกหลังวาดบอร์ดและจัดการเหตุการณ์จากบอร์ดแล้ว เพื่อให้ตัวเลขเป็นค่าล่าสุดเสมอ"""
    ss = st.session_state
    playing = game_running()               # ด่านนี้กำลังเล่นอยู่ (ยังไม่จบ) -> SANDBOX ถูกล็อก
    game_over = has_game and BOARD_COMPONENT is not None and not playing
    stage_now = ss.get("stage", 1)
    level_locked = run_locked()            # ทั้งรอบ (ทุกด่านจนกว่าจะแพ้) -> ระดับความยากถูกล็อก
    with panel():
        left, right = st.columns([3, 4])
        with left:
            # ระดับความยาก: แถบเลื่อน 3 ระดับ เลือกได้ก่อนกดเริ่มเกมเท่านั้น กดเริ่มแล้วล็อกตลอดทุกด่านจนกว่าเกมจะจบ (แพ้/หมดเวลา)
            level_labels = [d["label"] for d in DIFFICULTIES]
            st.select_slider("ระดับความยาก", options=level_labels, value=level_labels[DEFAULT_LEVEL], key="difficulty",
                             disabled=level_locked,
                             help="เลือกก่อนกดเริ่มเกม พอกดเริ่มแล้วจะเปลี่ยนไม่ได้ตลอดทุกด่านจนกว่าเกมจะจบ แล้วจึงเลือกใหม่ได้")
            level = DIFFICULTIES[current_level()]
            st.caption(("⏱ จับเวลา" if level["timer"] else "⏱ ไม่จับเวลา") +
                       " · A: −%d ถึง %d · f: −%d ถึง %d (ไม่รวม 0)" % (level["amp_max"], level["amp_max"], level["freq_max"], level["freq_max"]) +
                       " · 💡 คำใบ้เริ่มต้น %d ครั้ง (+%d ต่อด่าน)" % (level["start_hints"], HINT_PER_STAGE) +
                       (" · 🔒 ล็อกจนกว่าเกมจะจบ" if level_locked else ""))
        with right:
            if BOARD_COMPONENT is not None:
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("🎯 ด่านถัดไป" if game_over else "🎯 ด่าน", stage_now,
                              help="ผ่านครบทุก %d ด่านจะเพิ่มกราฟผสม +1 (สูงสุด %d กราฟ) ถ้าแพ้จะกลับไปด่าน 1" % (STAGES_PER_GRAPH, MAX_GRAPHS))
                with m2:
                    if level["hints"]:
                        st.metric("💡 คำใบ้สะสม", hint_pool_now(),
                                  help="คำใบ้ที่มีตอนเริ่มด่านนี้ (ปุ่ม 💡 ในเกมแสดงจำนวนที่เหลือจริง) ผ่านด่านได้เพิ่ม +%d "
                                       "คำใบ้ที่ใช้แล้วหมดไป ที่เหลือสะสมไปด่านถัดไป ถ้าแพ้จะเริ่มนับใหม่ตามระดับ" % HINT_PER_STAGE)
                with m3:
                    st.metric("🏆 คะแนนรวม", ss.get("total_score", 0),
                              help="รวมคะแนนของเกมที่ชนะต่อเนื่องกัน ถ้าแพ้ (รวมถึงกด 🏠 กลับหน้าแรกกลางเกม) จะรีเซ็ตเป็น 0")
                n_now = graphs_for_stage(stage_now)
                st.caption("ด่านนี้มีกราฟผสม %d กราฟ" % n_now + (" · ⏱ เวลา %s" % fmt_time(time_limit(n_now, stage_now)) if level["timer"] else ""))
            else:
                st.caption("(โหมดฝังบอร์ดตรง ๆ: ไม่แสดงด่าน คะแนนรวม และคำใบ้สะสมที่นี่)")
        confirming = bool(ss.get("confirm_quit")) and has_game
        b1, b2, b3 = st.columns(3)
        with b1:
            if playing:
                # กดเริ่มเกมแล้ว: ปุ่มเริ่มเกมถูกล็อกจนกว่าเกมจะจบ สุ่มโจทย์ใหม่ (รีโรล) ไม่ได้
                # ทางออกระหว่างเล่นมีทางเดียวคือปุ่ม 🏠 กลับหน้าแรก (นับเป็นแพ้)
                wide_button("🔒 กำลังเล่นอยู่", key="start_locked", disabled=True,
                            help="กดเริ่มเกมแล้วสุ่มโจทย์ใหม่ไม่ได้ ต้องเล่นให้จบ หรือกด 🏠 กลับหน้าแรก (นับเป็นแพ้)")
            else:
                if not has_game:
                    start_label = "▶ เริ่มเกม"
                elif not game_over:
                    # เหลือกรณีเดียว: ใช้ HTML ฝังตรง ๆ (ไม่มี BOARD_COMPONENT) ที่บอร์ดรายงานผลกลับมาไม่ได้ จึงไม่รู้ว่าเกมจบเมื่อไร
                    # ถ้าล็อกปุ่มนี้ไว้ ผู้เล่นจะเริ่มเกมต่อไม่ได้อีกเลย จึงต้องเปิดไว้ (ในกรณีปกติจะไม่มาถึงตรงนี้)
                    start_label = "🔄 เริ่มเกมใหม่"
                elif ss.get("last_status") == "won":
                    start_label = "➡ ด่านถัดไป"
                else:
                    start_label = "🔄 เริ่มใหม่ (กลับไปด่าน 1)"
                wide_button(start_label, key="start_game", type="primary", on_click=request_start)
        with b2:
            # ปุ่มกลับหน้าแรก: กลางเกมหรือมีคะแนนสะสมอยู่ต้องกดยืนยันก่อน เพราะเป็นการจบรอบ (กลางเกมนับเป็นแพ้)
            need_confirm = playing or ss.get("total_score", 0) > 0
            wide_button("🏠 กลับหน้าแรก", key="quit_ask", on_click=ask_quit if need_confirm else go_home, disabled=confirming,
                        help="กลับไปหน้าแรก เปลี่ยนระดับความยากได้ใหม่" + (" (กลางเกมนับเป็นแพ้)" if playing else ""))
        with b3:
            # ปุ่ม SANDBOX: ล็อกระหว่างเล่นเกม ใช้ได้ก่อนเริ่มเกมและหลังเกมจบ
            wide_button("🧪 SANDBOX", key="sandbox_open", on_click=set_mode, args=("sandbox",), disabled=playing,
                        help="ล็อกอยู่ระหว่างเล่นเกม ใช้ได้เมื่อเกมจบ" if playing else "ทดลองปรับอนุกรมฟูเรียร์บนจอใหญ่")
        if confirming:
            if playing:
                st.warning("กลับหน้าแรกตอนนี้ **เกมที่กำลังเล่นอยู่จะนับเป็นแพ้** คะแนนรวมรีเซ็ตเป็น 0 และกลับไปเริ่มที่ด่าน 1 (⭐ คะแนนสูงสุดของระดับนี้ยังเก็บไว้)")
            else:
                st.warning("กลับหน้าแรกจะจบรอบนี้ คะแนนรวมรีเซ็ตเป็น 0 และกลับไปเริ่มที่ด่าน 1 (⭐ คะแนนสูงสุดของระดับนี้ยังเก็บไว้)")
            q1, q2 = st.columns(2)
            with q1:
                wide_button("✅ ยืนยัน กลับหน้าแรก", key="quit_yes", on_click=go_home, type="primary")
            with q2:
                wide_button("↩ ยกเลิก", key="quit_no", on_click=cancel_quit)


# =====================================================================
# สคริปต์หน้าเว็บ (Streamlit รันทั้งไฟล์นี้ใหม่ทุกครั้งที่กดปุ่ม)
# =====================================================================
st.set_page_config(page_title="SINALL", page_icon="📡", layout="wide")

ss = st.session_state
mode = ss.get("mode", "home")
if mode not in ("home", "game", "sandbox", "tutorial"):
    mode = "home"
if game_running() and mode != "game":
    mode = "game"                           # กันไว้: ระหว่างเล่นเกมต้องอยู่ที่หน้าเกมเสมอ
ss["mode"] = mode
has_game = "game" in ss

# ธีม (มืด/สว่าง): ทับสีของหน้า Streamlit ก่อน แล้วค่อยวาดแถบบนสุด (ชื่อหน้า + ปุ่มสลับโหมด) ส่วนบอร์ด หน้าแรก SANDBOX รับธีมไปใช้เอง
st.markdown("<style>%s</style>" % page_css(current_theme()), unsafe_allow_html=True)
header_row(mode)

# หน้าแรก หน้าเกม และหน้า SANDBOX ถูกสร้างไว้ทั้งสามหน้า แล้วใช้ CSS ซ่อนหน้าที่ไม่ได้ดูอยู่ (ไม่ถอดออกจากหน้าเว็บ)
# เพื่อให้ลูกบิด คำใบ้ และจำนวนครั้งที่ส่งตรวจของเกมอยู่ครบเมื่อสลับกลับมา (หน้า Tutorial สร้างเฉพาะตอนที่เปิดอยู่)
hidden = [k for k in ("home", "game", "sandbox") if k != mode]
st.markdown("<style>%s{display:none}</style>" % ",".join(".st-key-%s_box" % k for k in hidden), unsafe_allow_html=True)
home_page = box("home_box")            # สร้างกล่องไว้ก่อน เติมเนื้อหาทีหลัง (ลำดับบนหน้าเว็บไม่เปลี่ยน)
game_page = box("game_box")
sandbox_page = box("sandbox_box")

with home_page:
    show_home()

# ---- หน้าเกม: ต้องวาดบอร์ดก่อนแผงควบคุม เพื่อให้ตัวเลขบนแผงเป็นค่าล่าสุดเสมอ (แผงอยู่บนบอร์ด จึงสร้างกล่องไว้ก่อน) ----
with game_page:
    tutorial_slot = st.container()
    controls_slot = st.container()
    if has_game and ss.get("shrink_notice"):
        show_shrink_notice()               # ก่อนเข้าด่าน 16: แจ้งเรื่องเวลาที่จะลดลง รอกดรับทราบ (ยังไม่เริ่มด่าน)
    elif has_game:
        board_event = show_board(ss["game"])
        handle_board_event(board_event, ss["game"])    # เก็บคะแนน / ทำตามปุ่มในหน้าสรุป
    with tutorial_slot:
        if ss.get("tutorial_ask"):
            show_tutorial_question()       # หลังกดเริ่มเกมครั้งแรก: ถามว่าอยากดู Tutorial ไหม
    with controls_slot:
        show_game_controls(has_game)

with sandbox_page:
    st.latex(r"f(x)=a_0+\sum_{n=1}^{6}\left(a_n\cos(nx)+b_n\sin(nx)\right)")
    st.button("🎮 กลับไปหน้าเกม" if ss.get("sandbox_back") == "game" else "🏠 กลับหน้าแรก",
              key="sandbox_back_btn", on_click=leave_sandbox)
    show_sandbox()
    with st.expander("📖 ความหมายของพารามิเตอร์", expanded=False):
        st.markdown(SANDBOX_HELP)

if mode == "tutorial":
    with box("tutorial_box"):
        show_tutorial()

# ---- แถบด้านซ้าย: แสดงเฉพาะคะแนนสูงสุดที่เคยทำได้ในแต่ละระดับความยาก (ที่เหลือย้ายไปอยู่บนหน้าเกมแล้ว) ----
with st.sidebar:
    st.header("⭐ คะแนนสูงสุด")
    for idx, d in enumerate(DIFFICULTIES):
        st.metric(d["label"], high_score_of(idx))
    st.caption("แยกตามระดับความยาก · เริ่มนับใหม่เมื่อรีเฟรชหน้าเว็บ")
