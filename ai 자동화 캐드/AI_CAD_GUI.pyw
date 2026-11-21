# -*- coding: utf-8 -*-
"""
AI CAD 자동화 - 독립 GUI 프로그램 (AutoCAD 2023 전용 연동)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AutoCAD 명령창이 아닌 별도의 AI 전용 창에서
자연어를 입력하면 AutoCAD 2023에 도면을 자동 작도합니다.

공종: 금속 하지틀(각파이프/트러스), 화스너 브라켓, 외장 판넬(알루미늄/복합판넬), 후레싱
      (단열재 시공 제외)
"""

import ctypes
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_SCR = os.path.join(BASE_DIR, "ai_draw_output.scr")
AUTOCAD_2023_EXE = r"C:\Program Files\Autodesk\AutoCAD 2023\acad.exe"

# ⚠️ AutoCAD 2023의 실제 COM ProgID는 AutoCAD.Application.24.2 이다.
#    (이 PC의 기본 AutoCAD.Application CurVer는 .24를 가리켜 2023 연결이 실패했음)
ACAD_PROGIDS = [
    ("AutoCAD 2023 (24.2)", "AutoCAD.Application.24.2"),
    ("AutoCAD 2022 (24.1)", "AutoCAD.Application.24.1"),
    ("AutoCAD 2021 (24)", "AutoCAD.Application.24"),
    ("AutoCAD 기본", "AutoCAD.Application"),
    ("AutoCAD 2016 (20.1)", "AutoCAD.Application.20.1"),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자연어 파서
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def parse_prompt(text):
    """자연어 프롬프트에서 도면 사양을 파싱"""
    text = text.strip()
    data = {
        "width": 4000.0,
        "height": 3000.0,
        "type": "subframe",   # single_pipe | subframe | panel
        "pipe_w": 50.0,
        "pipe_h": 50.0,
        "pitch_x": 600.0,
        "pitch_y": 1200.0,
        "bracket_pitch": 900.0,
        "panel_joint": 15.0,
    }

    # 1) 파이프 단면 규격 (예: 50*50, 100x50, 75x45 — 두 변 모두 300 이하인 경우)
    pipe_span = None
    for m in re.finditer(r'(\d{2,3})\s*[*xX×]\s*(\d{2,3})', text):
        a, b = float(m.group(1)), float(m.group(2))
        if a <= 300 and b <= 300:
            data["pipe_w"], data["pipe_h"] = a, b
            pipe_span = m.span()
            break

    # 2) 전체 입면 크기 (W x H — 한 변 이상 400 이상)
    found_wh = False
    for m in re.finditer(r'(\d{3,5})\s*[*xX×,]\s*(\d{3,5})', text):
        if pipe_span and m.span() == pipe_span:
            continue
        a, b = float(m.group(1)), float(m.group(2))
        if a >= 400 or b >= 400:
            data["width"], data["height"] = a, b
            found_wh = True
            break

    # 3) 공종 판별
    if any(k in text for k in ["판넬", "패널", "와리", "복합판넬", "시트"]):
        data["type"] = "panel"
    elif not found_wh and any(k in text for k in ["각파이프", "각 파이프", "각관", "파이프"]) and not any(
        k in text for k in ["하지틀", "하지", "프레임", "간격", "피치", "화스너", "브라켓"]
    ):
        # 예: "각 파이프 50*50 3000 자리 만들어줘" -> 단일 각파이프 부재
        data["type"] = "single_pipe"
        cleaned = text[:pipe_span[0]] + " " + text[pipe_span[1]:] if pipe_span else text
        m_len = re.search(r'(\d{3,5})\s*(?:짜리|자리|길이|mm)?', cleaned)
        if m_len:
            data["width"] = float(m_len.group(1))
        else:
            data["width"] = 3000.0
        data["height"] = data["pipe_h"]
    else:
        data["type"] = "subframe"
        if not found_wh:
            cleaned = text[:pipe_span[0]] + " " + text[pipe_span[1]:] if pipe_span else text
            m_single = re.search(r'(\d{3,5})', cleaned)
            if m_single and float(m_single.group(1)) >= 500:
                data["width"] = float(m_single.group(1))

    # 4) 간격/피치
    m = re.search(r'(?:간격|피치|수직|종대)\s*[:=]?\s*(\d{3,4})', text)
    if m:
        data["pitch_x"] = float(m.group(1))
    m = re.search(r'(?:수평|횡대|가로대)\s*[:=]?\s*(\d{3,4})', text)
    if m:
        data["pitch_y"] = float(m.group(1))
    m = re.search(r'(?:화스너|브라켓|앙카|앵커)\s*[:=]?\s*(\d{3,4})', text)
    if m:
        data["bracket_pitch"] = float(m.group(1))

    return data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 도면 요소(지오메트리) 생성 — COM 직접 작도와 SCR 출력 공용
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_drawing_spec(d):
    """레이어, 사각형, 원, 치수선, 텍스트 목록을 표준 딕셔너리로 만든다."""
    layers = {}
    rects = []    # (layer, x1, y1, x2, y2)
    circles = []  # (layer, cx, cy, r)
    dims = []     # (layer, x1, y1, x2, y2, tx, ty)
    texts = []    # (layer, text, x, y, height, center)

    if d["type"] == "single_pipe":
        length = d["width"]
        pw, ph = d["pipe_w"], d["pipe_h"]
        t = 2.3  # 표준 각파이프 두께 (mm)
        layers = {
            "01_각파이프": 4,
            "02_중심선": 1,
            "03_치수": 2,
            "04_주기": 3,
        }
        # 정면도 (길이 x 폭)
        rects.append(("01_각파이프", 0, 0, length, ph))
        rects.append(("01_각파이프", 0, t, length, ph - t))
        # 우측 단면도 (pw x ph)
        sx = length + 300.0
        rects.append(("01_각파이프", sx, 0, sx + pw, ph))
        rects.append(("01_각파이프", sx + t, t, sx + pw - t, ph - t))
        # 치수
        dims.append(("03_치수", 0, 0, length, 0, length / 2, -180))
        dims.append(("03_치수", 0, 0, 0, ph, -180, ph / 2))
        dims.append(("03_치수", sx, 0, sx + pw, 0, sx + pw / 2, -180))
        # 주기
        texts.append(("04_주기", f"각파이프 {pw:.0f}x{ph:.0f}x{t}T  L={length:.0f}mm", 0, -350, 70, False))
        texts.append(("04_주기", f"단면 {pw:.0f}x{ph:.0f}", sx, ph + 50, 40, False))

    elif d["type"] == "panel":
        w, h, joint = d["width"], d["height"], d["panel_joint"]
        nc = max(1, round(w / 1000))
        nr = max(1, round(h / 1200))
        pw = (w - joint * (nc + 1)) / nc
        ph = (h - joint * (nr + 1)) / nr
        layers = {
            "01_외곽선": 7,
            "02_판넬": 3,
            "03_태그": 4,
            "04_치수": 2,
        }
        rects.append(("01_외곽선", 0, 0, w, h))
        n = 1
        for r in range(nr):
            y0 = joint + r * (ph + joint)
            for c in range(nc):
                x0 = joint + c * (pw + joint)
                rects.append(("02_판넬", x0, y0, x0 + pw, y0 + ph))
                texts.append(("03_태그", f"P-{n:02d}", x0 + pw / 2, y0 + ph / 2 + 30, 50, True))
                texts.append(("03_태그", f"{pw:.0f}x{ph:.0f}", x0 + pw / 2, y0 + ph / 2 - 30, 40, True))
                n += 1
        dims.append(("04_치수", 0, 0, w, 0, w / 2, -300))
        dims.append(("04_치수", 0, 0, 0, h, -300, h / 2))
        texts.append(("03_태그", f"외장 판넬 와리도 W{w:.0f}xH{h:.0f} ({nc}x{nr}={nc*nr}매, 줄눈 {joint:.0f}mm)", 0, -550, 90, False))

    else:  # subframe
        w, h, pw, ph = d["width"], d["height"], d["pipe_w"], d["pipe_h"]
        px, py, bp = d["pitch_x"], d["pitch_y"], d["bracket_pitch"]
        layers = {
            "01_외곽선": 7,
            "02_각파이프": 4,
            "03_화스너": 1,
            "04_치수": 2,
            "05_주기": 3,
        }
        rects.append(("01_외곽선", 0, 0, w, h))

        xs = [0.0]
        cx = px
        while cx < w - px * 0.4:
            xs.append(cx)
            cx += px
        if w not in xs:
            xs.append(w)

        for x in xs:
            if x == 0:
                x1, x2 = 0, pw
            elif x == w:
                x1, x2 = w - pw, w
            else:
                x1, x2 = x - pw / 2, x + pw / 2
            rects.append(("02_각파이프", x1, 0, x2, h))

        ys = [0.0]
        cy = py
        while cy < h - py * 0.4:
            ys.append(cy)
            cy += py
        if h not in ys:
            ys.append(h)

        for y in ys:
            if y == 0:
                y1, y2 = 0, pw
            elif y == h:
                y1, y2 = h - pw, h
            else:
                y1, y2 = y - pw / 2, y + pw / 2
            rects.append(("02_각파이프", 0, y1, w, y2))

        for x in xs:
            by = bp / 2
            while by < h:
                rects.append(("03_화스너", x - 30, by - 40, x + 30, by + 40))
                circles.append(("03_화스너", x, by, 8.0))
                by += bp

        dims.append(("04_치수", 0, 0, w, 0, w / 2, -300))
        dims.append(("04_치수", 0, 0, 0, h, -300, h / 2))
        texts.append(("05_주기", f"하지틀({pw:.0f}x{ph:.0f}각파이프) W{w:.0f}xH{h:.0f}", 0, -500, 100, False))
        texts.append(("05_주기", f"수직@{px:.0f} | 수평@{py:.0f} | 화스너@{bp:.0f}", 0, -700, 70, False))

    return {
        "layers": layers,
        "rects": rects,
        "circles": circles,
        "dims": dims,
        "texts": texts,
    }


def build_scr_from_spec(spec):
    L = ["CMDECHO 0", "OSMODE 0"]
    for lname, color in spec["layers"].items():
        L.append(f"-LAYER M {lname} C {color} {lname} ")

    cur_layer = None
    for lname, x1, y1, x2, y2 in spec["rects"]:
        if lname != cur_layer:
            L.append(f"-LAYER S {lname} ")
            cur_layer = lname
        L.append(f"RECTANG {x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f}")

    for lname, cx, cy, r in spec["circles"]:
        if lname != cur_layer:
            L.append(f"-LAYER S {lname} ")
            cur_layer = lname
        L.append(f"CIRCLE {cx:.1f},{cy:.1f} {r:.1f}")

    for lname, x1, y1, x2, y2, tx, ty in spec["dims"]:
        if lname != cur_layer:
            L.append(f"-LAYER S {lname} ")
            cur_layer = lname
        L.append(f"DIMLINEAR {x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} {tx:.1f},{ty:.1f}")

    for lname, txt, x, y, h, center in spec["texts"]:
        if lname != cur_layer:
            L.append(f"-LAYER S {lname} ")
            cur_layer = lname
        if center:
            L.append(f"-TEXT J MC {x:.1f},{y:.1f} {h:.1f} 0 {txt}")
        else:
            L.append(f"-TEXT {x:.1f},{y:.1f} {h:.1f} 0 {txt}")

    L += ["ZOOM E", "CMDECHO 1", ""]
    return "\n".join(L)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AutoCAD 2023 COM 연결 & 직접 작도
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def is_acad_process_running():
    """Windows에 acad.exe 프로세스가 떠 있는지 확인"""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq acad.exe", "/NH"],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            text=True,
            errors="ignore",
        )
        return "acad.exe" in out.lower()
    except Exception:
        return False


def get_autocad():
    """실행 중인 AutoCAD 2023(또는 호환 버전)에 COM 연결.

    Returns: (acad_obj_or_None, connected_progid_or_None, error_detail_str)
    """
    import pythoncom
    import win32com.client

    # ⚠️ 스레드 내 COM 호출 시 CoInitialize 필수!
    pythoncom.CoInitialize()

    errors = []
    for label, progid in ACAD_PROGIDS:
        try:
            acad = win32com.client.GetActiveObject(progid)
            return acad, f"{label} [{progid}]", ""
        except Exception as e:
            errors.append(f"{progid}: {e}")

    running = is_acad_process_running()
    if running:
        admin_txt = "관리자 권한" if is_admin() else "일반 권한"
        detail = (
            f"AutoCAD(acad.exe)는 실행 중이지만 COM 연결이 차단되었습니다 (현재 AI창={admin_txt}).\n"
            f"→ 원인의 99%는 AutoCAD와 AI 창의 권한(관리자/일반)이 서로 다르기 때문입니다.\n"
            f"→ 아래 [🛡️ 관리자 권한으로 재실행] 버튼을 누르거나, AutoCAD를 일반 권한으로 실행해 주세요."
        )
    else:
        detail = (
            "AutoCAD 2023이 실행되어 있지 않습니다.\n"
            "→ 아래 [🚀 AutoCAD 2023 실행] 버튼으로 캐드를 먼저 켜고, 도면 창이 열린 뒤 다시 시도해 주세요."
        )
    return None, None, detail


def draw_spec_to_autocad(spec, scr_path):
    """AutoCAD 2023에 COM으로 직접 작도 (실패 시 정식 SCRIPT SendCommand로 폴백)."""
    import pythoncom
    import win32com.client

    acad, prog_label, err = get_autocad()
    if acad is None:
        return False, err

    try:
        try:
            doc = acad.ActiveDocument
        except Exception:
            doc = acad.Documents.Add()
        msp = doc.ModelSpace

        # 1) 레이어 생성
        for lname, color in spec["layers"].items():
            try:
                lyr = doc.Layers.Add(lname)
                lyr.color = int(color)
            except Exception:
                pass

        # 2) 사각형(LightweightPolyline) 작도
        for lname, x1, y1, x2, y2 in spec["rects"]:
            pts = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [float(x1), float(y1), float(x2), float(y1),
                 float(x2), float(y2), float(x1), float(y2)],
            )
            pl = msp.AddLightWeightPolyline(pts)
            pl.Closed = True
            pl.Layer = lname

        # 3) 원(화스너 앵커) 작도
        for lname, cx, cy, r in spec["circles"]:
            center = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8,
                [float(cx), float(cy), 0.0],
            )
            c = msp.AddCircle(center, float(r))
            c.Layer = lname

        # 4) 치수선 작도
        for lname, x1, y1, x2, y2, tx, ty in spec["dims"]:
            p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x1), float(y1), 0.0])
            p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x2), float(y2), 0.0])
            pt = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(tx), float(ty), 0.0])
            dim = msp.AddDimAligned(p1, p2, pt)
            dim.Layer = lname

        # 5) 텍스트 주기
        for lname, txt, x, y, h, _center in spec["texts"]:
            pt = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), 0.0])
            t = msp.AddText(str(txt), pt, float(h))
            t.Layer = lname

        try:
            acad.ZoomExtents()
        except Exception:
            pass
        return True, f"AutoCAD 직접 작도 완료! ({prog_label} / 도면: {doc.Name})"

    except Exception as com_err:
        # COM 직접 작도가 도면 상태(예: 명령 실행 중) 때문에 실패하면 정식 SCRIPT 명령 폴백
        try:
            doc = acad.ActiveDocument
            scr_posix = scr_path.replace("\\", "/")
            doc.SendCommand(f'\x1b\x1b_FILEDIA 0\n_.SCRIPT\n"{scr_posix}"\n_FILEDIA 1\n')
            return True, f"SCRIPT 전송 완료! ({prog_label}, COM 폴백: {com_err})"
        except Exception as e2:
            return False, f"AutoCAD 작도 오류: {com_err} / SCRIPT 폴백 오류: {e2}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUI 메인 창
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class AICadApp:
    def __init__(self):
        self.root = tk.Tk()
        admin_badge = " [관리자]" if is_admin() else ""
        self.root.title(f"🏗️ AI 금속 도면 자동화 — AutoCAD 2023{admin_badge}")
        self.root.geometry("820x700")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        self._build_ui()
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log(f"  AI 금속 도면 자동화 시스템 (AutoCAD 2023{admin_badge})")
        self.log("  회사 공종: 각파이프 하지틀 / 화스너 / 외장 판넬")
        self.log("  (단열재 시공 제외)")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("")
        self.log("📌 사용 예시:")
        self.log("  • 각 파이프 50*50 3000 자리 만들어줘")
        self.log("  • 4000x3000 하지틀 간격 600 화스너 900")
        self.log("  • 5000x3500 복합판넬 와리도")
        self.log("  • 100x50 각파이프 6000x4000 수직 900 수평 1200")
        self.log("")
        # 실행 직후 AutoCAD 2023 연결 상태 자동 확인
        self.root.after(400, self.on_check_acad)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        title_frame = tk.Frame(self.root, bg="#313244", pady=10)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="🏗️ AI 금속 도면 자동화", font=("맑은 고딕", 18, "bold"),
                 fg="#89b4fa", bg="#313244").pack()
        tk.Label(title_frame, text="AutoCAD 2023 (24.2) 직접 연동  |  자연어 → 도면 즉시 생성",
                 font=("맑은 고딕", 10), fg="#a6adc8", bg="#313244").pack()

        log_frame = tk.Frame(self.root, bg="#1e1e2e", padx=10, pady=5)
        log_frame.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 11), bg="#181825", fg="#cdd6f4",
            insertbackground="#f5e0dc", wrap="word", relief="flat", bd=0
        )
        self.log_area.pack(fill="both", expand=True)
        self.log_area.configure(state="disabled")

        self.status_var = tk.StringVar(value="대기 중")
        status_bar = tk.Frame(self.root, bg="#313244", pady=4)
        status_bar.pack(fill="x")
        self.status_dot = tk.Label(status_bar, text="●", font=("Arial", 10), fg="#a6e3a1", bg="#313244")
        self.status_dot.pack(side="left", padx=(10, 5))
        tk.Label(status_bar, textvariable=self.status_var, font=("맑은 고딕", 9),
                 fg="#a6adc8", bg="#313244").pack(side="left")

        input_frame = tk.Frame(self.root, bg="#313244", padx=10, pady=10)
        input_frame.pack(fill="x")

        tk.Label(input_frame, text="자연어 입력:", font=("맑은 고딕", 10, "bold"),
                 fg="#cba6f7", bg="#313244").pack(anchor="w")

        entry_row = tk.Frame(input_frame, bg="#313244")
        entry_row.pack(fill="x", pady=(5, 0))

        self.input_entry = tk.Entry(
            entry_row, font=("맑은 고딕", 13), bg="#45475a", fg="#cdd6f4",
            insertbackground="#f5e0dc", relief="flat", bd=0
        )
        self.input_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda e: self.on_submit())

        self.btn_submit = tk.Button(
            entry_row, text="⚡ 작도 실행", font=("맑은 고딕", 11, "bold"),
            bg="#89b4fa", fg="#1e1e2e", activebackground="#74c7ec",
            relief="flat", padx=20, pady=6, cursor="hand2",
            command=self.on_submit
        )
        self.btn_submit.pack(side="left")

        btn_row = tk.Frame(input_frame, bg="#313244")
        btn_row.pack(fill="x", pady=(8, 0))

        tk.Button(btn_row, text="🚀 AutoCAD 2023 실행", font=("맑은 고딕", 9, "bold"),
                  bg="#a6e3a1", fg="#1e1e2e", relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.on_launch_acad).pack(side="left", padx=(0, 5))

        tk.Button(btn_row, text="🔗 연결 확인", font=("맑은 고딕", 9),
                  bg="#45475a", fg="#cdd6f4", relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.on_check_acad).pack(side="left", padx=(0, 5))

        tk.Button(btn_row, text="🛡️ 관리자 권한 재실행", font=("맑은 고딕", 9),
                  bg="#f9e2af", fg="#1e1e2e", relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.on_relaunch_admin).pack(side="left", padx=(0, 5))

        tk.Button(btn_row, text="📂 이미지/PDF 분석", font=("맑은 고딕", 9),
                  bg="#45475a", fg="#cdd6f4", relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.on_image_analyze).pack(side="left", padx=(0, 5))

        tk.Button(btn_row, text="📋 SCR만 생성", font=("맑은 고딕", 9),
                  bg="#45475a", fg="#cdd6f4", relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.on_scr_only).pack(side="left")

    def log(self, msg):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def set_status(self, text, color="#a6e3a1"):
        self.status_var.set(text)
        self.status_dot.configure(fg=color)

    def on_launch_acad(self):
        if os.path.exists(AUTOCAD_2023_EXE):
            subprocess.Popen([AUTOCAD_2023_EXE])
            self.log("\n🚀 AutoCAD 2023을 실행했습니다. 도면 화면이 완전히 열린 뒤 [🔗 연결 확인]을 눌러주세요.")
            self.set_status("AutoCAD 2023 실행 중...", "#f9e2af")
        else:
            messagebox.showwarning("경로 없음", f"AutoCAD 2023 실행 파일을 찾을 수 없습니다:\n{AUTOCAD_2023_EXE}")

    def on_relaunch_admin(self):
        if is_admin():
            self.log("\n🛡️ 이미 관리자 권한으로 실행 중입니다.")
            return
        try:
            script = os.path.abspath(__file__)
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}"', BASE_DIR, 1
            )
            self.root.destroy()
        except Exception as e:
            self.log(f"❌ 관리자 권한 재실행 실패: {e}")

    def on_submit(self):
        prompt = self.input_entry.get().strip()
        if not prompt:
            return

        self.input_entry.delete(0, "end")
        self.log(f"\n👤 입력: {prompt}")
        self.set_status("도면 생성 중...", "#f9e2af")
        self.btn_submit.configure(state="disabled")
        threading.Thread(target=self._process_prompt, args=(prompt, True), daemon=True).start()

    def on_scr_only(self):
        prompt = self.input_entry.get().strip()
        if not prompt:
            messagebox.showinfo("안내", "먼저 자연어 사양을 입력해 주세요.")
            return

        self.input_entry.delete(0, "end")
        self.log(f"\n👤 입력: {prompt}")
        self.set_status("SCR 생성 중...", "#f9e2af")
        threading.Thread(target=self._process_prompt, args=(prompt, False), daemon=True).start()

    def _process_prompt(self, prompt, send_to_acad):
        try:
            data = parse_prompt(prompt)
            spec = build_drawing_spec(data)
            type_kor = {"single_pipe": "단일 각파이프", "panel": "외장 판넬 와리", "subframe": "금속 하지틀"}.get(data["type"], data["type"])
            self.root.after(
                0, self.log,
                f"🔍 파싱 결과: {type_kor} | 크기 {data['width']:.0f}x{data['height']:.0f}mm | 파이프 {data['pipe_w']:.0f}x{data['pipe_h']:.0f}"
            )

            scr_text = build_scr_from_spec(spec)
            with open(OUTPUT_SCR, "w", encoding="cp949", errors="replace") as f:
                f.write(scr_text)
            self.root.after(0, self.log, f"✅ SCR 저장 완료 → {OUTPUT_SCR}")

            if send_to_acad:
                self.root.after(0, self.log, "📡 AutoCAD 2023에 직접 작도 중...")
                ok, msg = draw_spec_to_autocad(spec, OUTPUT_SCR)
                if ok:
                    self.root.after(0, self.log, f"🎉 {msg}")
                    self.root.after(0, self.set_status, "작도 완료!", "#a6e3a1")
                else:
                    self.root.after(0, self.log, f"⚠️ {msg}")
                    self.root.after(0, self.log, f"💡 바로 쓰기: AutoCAD 도면 화면에 아래 .scr 파일을 마우스로 드래그 앤 드롭해도 즉시 그려집니다:\n   {OUTPUT_SCR}")
                    self.root.after(0, self.set_status, "AutoCAD 연결 안 됨", "#f38ba8")
            else:
                self.root.after(0, self.log, f"💡 AutoCAD 화면에 아래 파일을 드래그 앤 드롭하세요:\n   {OUTPUT_SCR}")
                self.root.after(0, self.set_status, "SCR 준비 완료", "#a6e3a1")

        except Exception as e:
            self.root.after(0, self.log, f"❌ 오류 발생: {e}")
            self.root.after(0, self.set_status, "오류 발생", "#f38ba8")
        finally:
            self.root.after(0, lambda: self.btn_submit.configure(state="normal"))

    def on_image_analyze(self):
        filepath = filedialog.askopenfilename(
            title="분석할 이미지 또는 PDF 선택",
            filetypes=[("이미지/PDF 파일", "*.png *.jpg *.jpeg *.bmp *.pdf"), ("모든 파일", "*.*")],
            initialdir=BASE_DIR
        )
        if not filepath:
            return

        self.log(f"\n📂 이미지 분석 시작: {filepath}")
        self.set_status("이미지 분석 중...", "#f9e2af")

        dim_win = tk.Toplevel(self.root)
        dim_win.title("실제 치수 입력")
        dim_win.geometry("350x200")
        dim_win.configure(bg="#313244")
        dim_win.transient(self.root)
        dim_win.grab_set()

        tk.Label(dim_win, text="현장 실제 치수를 입력하세요", font=("맑은 고딕", 11, "bold"),
                 fg="#89b4fa", bg="#313244").pack(pady=(15, 10))

        f1 = tk.Frame(dim_win, bg="#313244")
        f1.pack(pady=5)
        tk.Label(f1, text="가로 (mm):", fg="#cdd6f4", bg="#313244", font=("맑은 고딕", 10)).pack(side="left")
        w_entry = tk.Entry(f1, width=10, font=("맑은 고딕", 11), bg="#45475a", fg="#cdd6f4", relief="flat")
        w_entry.insert(0, "6000")
        w_entry.pack(side="left", padx=5)

        f2 = tk.Frame(dim_win, bg="#313244")
        f2.pack(pady=5)
        tk.Label(f2, text="세로 (mm):", fg="#cdd6f4", bg="#313244", font=("맑은 고딕", 10)).pack(side="left")
        h_entry = tk.Entry(f2, width=10, font=("맑은 고딕", 11), bg="#45475a", fg="#cdd6f4", relief="flat")
        h_entry.insert(0, "4000")
        h_entry.pack(side="left", padx=5)

        def do_analyze():
            rw = float(w_entry.get())
            rh = float(h_entry.get())
            dim_win.destroy()
            threading.Thread(target=self._run_image_analysis, args=(filepath, rw, rh), daemon=True).start()

        tk.Button(dim_win, text="분석 시작", font=("맑은 고딕", 10, "bold"),
                  bg="#89b4fa", fg="#1e1e2e", relief="flat", padx=20, pady=5,
                  command=do_analyze).pack(pady=15)

    def _run_image_analysis(self, filepath, rw, rh):
        try:
            engine_path = os.path.join(BASE_DIR, "image_to_panel_engine.py")
            if not os.path.exists(engine_path):
                self.root.after(0, self.log, f"❌ 엔진 파일을 찾을 수 없습니다: {engine_path}")
                return

            import importlib.util
            spec = importlib.util.spec_from_file_location("image_to_panel_engine", engine_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            proc = mod.ImageToPanelProcessor(filepath, rw, rh)
            proc.load_and_preprocess()
            self.root.after(0, self.log, f"  이미지 로드 완료: {proc.img_w}x{proc.img_h}px")

            proc.detect_openings()
            self.root.after(0, self.log, f"  개구부 {len(proc.openings)}개 감지")

            proc.generate_panels()
            self.root.after(0, self.log, f"  판넬 {len(proc.panels)}장 배치 완료")

            proc.export_all()

            total = sum(p["area_m2"] for p in proc.panels)
            self.root.after(0, self.log, "🎉 판넬 와리 설계 완료!")
            self.root.after(0, self.log, f"   판넬 {len(proc.panels)}매 | 총면적 {total:.2f}㎡")
            self.root.after(0, self.log, f"   DXF/산출서/미리보기 → {BASE_DIR}")
            self.root.after(0, self.set_status, "이미지 분석 완료!", "#a6e3a1")

        except Exception as e:
            self.root.after(0, self.log, f"❌ 이미지 분석 오류: {e}")
            self.root.after(0, self.set_status, "분석 오류", "#f38ba8")

    def on_check_acad(self):
        """AutoCAD 2023 연결 상태 확인"""
        self.log("\n🔗 AutoCAD 2023 연결 확인 중...")
        acad, prog_label, err = get_autocad()
        if acad:
            try:
                ver = acad.Version
                doc_name = acad.ActiveDocument.Name
                self.log(f"✅ AutoCAD 연결 성공! ({prog_label}, 버전: {ver})")
                self.log(f"   현재 열린 도면: {doc_name}")
                self.set_status(f"AutoCAD 연결됨 ({ver})", "#a6e3a1")
            except Exception as e:
                self.log(f"⚠️ AutoCAD 연결됨({prog_label}), 열린 도면이 없거나 준비 중입니다: {e}")
                self.set_status("AutoCAD 연결됨 (도면 대기)", "#f9e2af")
        else:
            self.log(f"❌ {err}")
            self.set_status("AutoCAD 미연결", "#f38ba8")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AICadApp()
    app.run()
