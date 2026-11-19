# -*- coding: utf-8 -*-
"""
AI CAD 자동화 - 독립 GUI 프로그램 (AutoCAD 2023 연동)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AutoCAD 명령창이 아닌 별도의 AI 전용 창에서
자연어를 입력하면 AutoCAD 2023에 도면을 자동 작도합니다.

공종: 금속 하지틀(각파이프), 화스너 브라켓, 외장 판넬(알루미늄/복합판넬)
      단열재 시공 제외
"""

import os
import re
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_SCR = os.path.join(BASE_DIR, "ai_draw_output.scr")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자연어 파서
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def parse_prompt(text):
    """자연어 프롬프트에서 도면 사양을 파싱"""
    text = text.strip()
    data = {
        "width": 4000.0, "height": 3000.0,
        "type": "subframe",
        "pipe_w": 50.0, "pipe_h": 50.0,
        "pitch_x": 600.0, "pitch_y": 1200.0,
        "bracket_pitch": 900.0,
        "panel_joint": 15.0,
    }

    # 크기 (W x H) — 3자리~5자리 숫자
    m = re.search(r'(\d{3,5})\s*[*xX×,]\s*(\d{3,5})', text)
    if m:
        data["width"], data["height"] = float(m.group(1)), float(m.group(2))

    # 단일 길이 "3000 자리" / "길이 3000"
    if not m:
        m_single = re.search(r'(\d{3,5})\s*(?:자리|길이|mm)?', text)
        if m_single:
            val = float(m_single.group(1))
            if val >= 500:
                data["width"] = val

    # 공종
    if any(k in text for k in ["판넬", "패널", "와리", "복합판넬", "시트"]):
        data["type"] = "panel"
    else:
        data["type"] = "subframe"

    # 파이프 규격 (50*50, 100x50 등)
    m = re.search(r'(\d{2,3})\s*[*xX×]\s*(\d{2,3})', text)
    if m:
        data["pipe_w"], data["pipe_h"] = float(m.group(1)), float(m.group(2))

    # 간격/피치
    m = re.search(r'(?:간격|피치|수직|종대)\s*[:=]?\s*(\d{3,4})', text)
    if m: data["pitch_x"] = float(m.group(1))
    m = re.search(r'(?:수평|횡대|가로대)\s*[:=]?\s*(\d{3,4})', text)
    if m: data["pitch_y"] = float(m.group(1))
    m = re.search(r'(?:화스너|브라켓|앙카)\s*[:=]?\s*(\d{3,4})', text)
    if m: data["bracket_pitch"] = float(m.group(1))

    return data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCR 생성기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_subframe_scr(d):
    w, h, pw, ph = d["width"], d["height"], d["pipe_w"], d["pipe_h"]
    px, py, bp = d["pitch_x"], d["pitch_y"], d["bracket_pitch"]

    L = ["CMDECHO 0", "OSMODE 0"]
    L.append("-LAYER M 01_외곽선 C 7 01_외곽선 ")
    L.append("-LAYER M 02_각파이프 C 4 02_각파이프 ")
    L.append("-LAYER M 03_화스너 C 1 03_화스너 ")
    L.append("-LAYER M 04_치수 C 2 04_치수 ")
    L.append("-LAYER M 05_주기 C 3 05_주기 ")

    # 외곽
    L.append("-LAYER S 01_외곽선 ")
    L.append(f"RECTANG 0,0 {w},{h}")

    # 수직 각파이프
    L.append("-LAYER S 02_각파이프 ")
    xs = [0.0]
    cx = px
    while cx < w - px * 0.4:
        xs.append(cx); cx += px
    if w not in xs: xs.append(w)

    for x in xs:
        if x == 0:    x1, x2 = 0, pw
        elif x == w:  x1, x2 = w - pw, w
        else:         x1, x2 = x - pw/2, x + pw/2
        L.append(f"RECTANG {x1:.1f},0 {x2:.1f},{h}")

    # 수평 각파이프
    ys = [0.0]
    cy = py
    while cy < h - py * 0.4:
        ys.append(cy); cy += py
    if h not in ys: ys.append(h)

    for y in ys:
        if y == 0:    y1, y2 = 0, pw
        elif y == h:  y1, y2 = h - pw, h
        else:         y1, y2 = y - pw/2, y + pw/2
        L.append(f"RECTANG 0,{y1:.1f} {w},{y2:.1f}")

    # 화스너
    L.append("-LAYER S 03_화스너 ")
    for x in xs:
        by = bp / 2
        while by < h:
            L.append(f"RECTANG {x-30:.1f},{by-40:.1f} {x+30:.1f},{by+40:.1f}")
            L.append(f"CIRCLE {x:.1f},{by:.1f} 8")
            by += bp

    # 치수
    L.append("-LAYER S 04_치수 ")
    L.append(f"DIMLINEAR 0,0 {w},0 0,-300")
    L.append(f"DIMLINEAR 0,0 0,{h} -300,0")

    # 주기
    L.append("-LAYER S 05_주기 ")
    L.append(f"-TEXT 0,{-500} 100 0 하지틀({pw:.0f}x{ph:.0f}각파이프)W{w:.0f}xH{h:.0f}")
    L.append(f"-TEXT 0,{-700} 70 0 수직@{px:.0f}|수평@{py:.0f}|화스너@{bp:.0f}")

    L += ["ZOOM E", "CMDECHO 1", ""]
    return "\n".join(L)


def build_panel_scr(d):
    w, h, joint = d["width"], d["height"], d["panel_joint"]
    nc = max(1, round(w / 1000))
    nr = max(1, round(h / 1200))
    pw = (w - joint*(nc+1)) / nc
    ph = (h - joint*(nr+1)) / nr

    L = ["CMDECHO 0", "OSMODE 0"]
    L.append("-LAYER M 01_외곽선 C 7 01_외곽선 ")
    L.append("-LAYER M 02_판넬 C 3 02_판넬 ")
    L.append("-LAYER M 03_태그 C 4 03_태그 ")
    L.append("-LAYER M 04_치수 C 2 04_치수 ")

    L.append("-LAYER S 01_외곽선 ")
    L.append(f"RECTANG 0,0 {w},{h}")

    n = 1
    for r in range(nr):
        y0 = joint + r*(ph+joint)
        for c in range(nc):
            x0 = joint + c*(pw+joint)
            L.append("-LAYER S 02_판넬 ")
            L.append(f"RECTANG {x0:.1f},{y0:.1f} {x0+pw:.1f},{y0+ph:.1f}")
            L.append("-LAYER S 03_태그 ")
            L.append(f"-TEXT J MC {x0+pw/2:.1f},{y0+ph/2+30:.1f} 50 0 P-{n:02d}")
            L.append(f"-TEXT J MC {x0+pw/2:.1f},{y0+ph/2-30:.1f} 40 0 {pw:.0f}x{ph:.0f}")
            n += 1

    L.append("-LAYER S 04_치수 ")
    L.append(f"DIMLINEAR 0,0 {w},0 0,-300")
    L.append(f"DIMLINEAR 0,0 0,{h} -300,0")
    L += ["ZOOM E", "CMDECHO 1", ""]
    return "\n".join(L)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AutoCAD 2023 COM 연결
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_autocad():
    """실행 중인 AutoCAD 2023에 COM 연결"""
    import win32com.client
    try:
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
        return acad
    except Exception:
        return None


def send_script_to_autocad(scr_path):
    """AutoCAD 2023에 스크립트 파일을 전송하여 실행"""
    acad = get_autocad()
    if acad is None:
        return False, "AutoCAD 2023이 실행되어 있지 않습니다.\nAutoCAD 2023을 먼저 실행해 주세요."
    try:
        doc = acad.ActiveDocument
        # SendCommand로 SCRIPT 명령 전송
        doc.SendCommand(f'(command "SCRIPT" "{scr_path}")\n')
        return True, "AutoCAD 2023에 도면 작도 명령을 전송하였습니다!"
    except Exception as e:
        return False, f"AutoCAD 연동 오류: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUI 메인 창
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class AICadApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏗️ AI 금속 도면 자동화 — AutoCAD 2023")
        self.root.geometry("780x680")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        self._build_ui()
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("  AI 금속 도면 자동화 시스템 (AutoCAD 2023)")
        self.log("  회사 공종: 각파이프 하지틀 / 화스너 / 외장 판넬")
        self.log("  (단열재 시공 제외)")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("")
        self.log("📌 사용 예시:")
        self.log("  • 각파이프 50*50 3000 자리 만들어줘")
        self.log("  • 4000x3000 하지틀 간격 600 화스너 900")
        self.log("  • 5000x3500 복합판넬 와리도")
        self.log("  • 100x50 각파이프 6000x4000 수직 900 수평 1200")
        self.log("")

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 상단 타이틀
        title_frame = tk.Frame(self.root, bg="#313244", pady=10)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="🏗️ AI 금속 도면 자동화", font=("맑은 고딕", 18, "bold"),
                 fg="#89b4fa", bg="#313244").pack()
        tk.Label(title_frame, text="AutoCAD 2023 연동  |  자연어 → 도면 즉시 생성",
                 font=("맑은 고딕", 10), fg="#a6adc8", bg="#313244").pack()

        # 로그 출력 영역
        log_frame = tk.Frame(self.root, bg="#1e1e2e", padx=10, pady=5)
        log_frame.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 11), bg="#181825", fg="#cdd6f4",
            insertbackground="#f5e0dc", wrap="word", relief="flat", bd=0
        )
        self.log_area.pack(fill="both", expand=True)
        self.log_area.configure(state="disabled")

        # 상태 표시줄
        self.status_var = tk.StringVar(value="대기 중")
        status_bar = tk.Frame(self.root, bg="#313244", pady=4)
        status_bar.pack(fill="x")
        self.status_dot = tk.Label(status_bar, text="●", font=("Arial", 10), fg="#a6e3a1", bg="#313244")
        self.status_dot.pack(side="left", padx=(10, 5))
        tk.Label(status_bar, textvariable=self.status_var, font=("맑은 고딕", 9),
                 fg="#a6adc8", bg="#313244").pack(side="left")

        # 하단 입력 영역
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

        # 추가 버튼 행
        btn_row = tk.Frame(input_frame, bg="#313244")
        btn_row.pack(fill="x", pady=(8, 0))

        tk.Button(btn_row, text="📂 이미지/PDF 분석", font=("맑은 고딕", 9),
                  bg="#45475a", fg="#cdd6f4", relief="flat", padx=12, pady=4,
                  cursor="hand2", command=self.on_image_analyze).pack(side="left", padx=(0, 5))

        tk.Button(btn_row, text="📋 SCR만 생성", font=("맑은 고딕", 9),
                  bg="#45475a", fg="#cdd6f4", relief="flat", padx=12, pady=4,
                  cursor="hand2", command=self.on_scr_only).pack(side="left", padx=(0, 5))

        tk.Button(btn_row, text="🔗 AutoCAD 연결 확인", font=("맑은 고딕", 9),
                  bg="#45475a", fg="#cdd6f4", relief="flat", padx=12, pady=4,
                  cursor="hand2", command=self.on_check_acad).pack(side="left")

    def log(self, msg):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def set_status(self, text, color="#a6e3a1"):
        self.status_var.set(text)
        self.status_dot.configure(fg=color)

    def on_submit(self):
        """자연어 입력 → AutoCAD 2023에 도면 전송"""
        prompt = self.input_entry.get().strip()
        if not prompt:
            return

        self.input_entry.delete(0, "end")
        self.log(f"\n👤 입력: {prompt}")
        self.set_status("도면 생성 중...", "#f9e2af")
        self.btn_submit.configure(state="disabled")

        # 별도 스레드에서 처리 (GUI 멈추지 않도록)
        threading.Thread(target=self._process_prompt, args=(prompt, True), daemon=True).start()

    def on_scr_only(self):
        """SCR 파일만 생성 (AutoCAD 전송 없이)"""
        prompt = self.input_entry.get().strip()
        if not prompt:
            messagebox.showinfo("안내", "먼저 자연어 사양을 입력해 주세요.")
            return

        self.input_entry.delete(0, "end")
        self.log(f"\n👤 입력: {prompt}")
        self.set_status("SCR 생성 중...", "#f9e2af")
        threading.Thread(target=self._process_prompt, args=(prompt, False), daemon=True).start()

    def _process_prompt(self, prompt, send_to_acad):
        """자연어 처리 → SCR 생성 → (선택) AutoCAD 전송"""
        try:
            # 1. 자연어 파싱
            data = parse_prompt(prompt)
            self.root.after(0, self.log, f"🔍 파싱 결과: {data['type']} | "
                f"규격 W{data['width']:.0f} x H{data['height']:.0f} | "
                f"파이프 {data['pipe_w']:.0f}x{data['pipe_h']:.0f}")

            # 2. SCR 생성
            if data["type"] == "panel":
                scr_text = build_panel_scr(data)
            else:
                scr_text = build_subframe_scr(data)

            with open(OUTPUT_SCR, "w", encoding="cp949", errors="replace") as f:
                f.write(scr_text)

            self.root.after(0, self.log, f"✅ SCR 스크립트 생성 완료 → {OUTPUT_SCR}")

            # 3. AutoCAD에 전송
            if send_to_acad:
                self.root.after(0, self.log, "📡 AutoCAD 2023에 전송 중...")
                ok, msg = send_script_to_autocad(OUTPUT_SCR)
                if ok:
                    self.root.after(0, self.log, f"🎉 {msg}")
                    self.root.after(0, self.set_status, "작도 완료!", "#a6e3a1")
                else:
                    self.root.after(0, self.log, f"⚠️ {msg}")
                    self.root.after(0, self.log, f"💡 대안: AutoCAD에서 SCRIPT 명령 → {OUTPUT_SCR} 선택")
                    self.root.after(0, self.set_status, "AutoCAD 연결 안 됨", "#f38ba8")
            else:
                self.root.after(0, self.log, f"💡 AutoCAD에서 SCRIPT 명령 후 아래 파일을 선택하세요:")
                self.root.after(0, self.log, f"   {OUTPUT_SCR}")
                self.root.after(0, self.set_status, "SCR 준비 완료", "#a6e3a1")

        except Exception as e:
            self.root.after(0, self.log, f"❌ 오류 발생: {e}")
            self.root.after(0, self.set_status, "오류 발생", "#f38ba8")
        finally:
            self.root.after(0, lambda: self.btn_submit.configure(state="normal"))

    def on_image_analyze(self):
        """이미지/PDF 파일을 선택하여 판넬 와리 도면 자동 생성"""
        filepath = filedialog.askopenfilename(
            title="분석할 이미지 또는 PDF 선택",
            filetypes=[("이미지/PDF 파일", "*.png *.jpg *.jpeg *.bmp *.pdf"), ("모든 파일", "*.*")],
            initialdir=BASE_DIR
        )
        if not filepath:
            return

        self.log(f"\n📂 이미지 분석 시작: {filepath}")
        self.set_status("이미지 분석 중...", "#f9e2af")

        # 치수 입력 다이얼로그
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
            # image_to_panel_engine 모듈 임포트
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
            self.root.after(0, self.log, f"🎉 판넬 와리 설계 완료!")
            self.root.after(0, self.log, f"   판넬 {len(proc.panels)}매 | 총면적 {total:.2f}㎡")
            self.root.after(0, self.log, f"   DXF/산출서/미리보기 → {BASE_DIR}")
            self.root.after(0, self.set_status, "이미지 분석 완료!", "#a6e3a1")

        except Exception as e:
            self.root.after(0, self.log, f"❌ 이미지 분석 오류: {e}")
            self.root.after(0, self.set_status, "분석 오류", "#f38ba8")

    def on_check_acad(self):
        """AutoCAD 2023 연결 상태 확인"""
        self.log("\n🔗 AutoCAD 2023 연결 확인 중...")
        acad = get_autocad()
        if acad:
            try:
                ver = acad.Version
                doc_name = acad.ActiveDocument.Name
                self.log(f"✅ AutoCAD 연결 성공! (버전: {ver})")
                self.log(f"   현재 열린 도면: {doc_name}")
                self.set_status(f"AutoCAD 연결됨 ({ver})", "#a6e3a1")
            except Exception as e:
                self.log(f"⚠️ AutoCAD 연결됨, 도면 정보 조회 오류: {e}")
        else:
            self.log("❌ AutoCAD 2023이 실행되어 있지 않습니다.")
            self.log("   AutoCAD 2023을 먼저 실행해 주세요.")
            self.set_status("AutoCAD 미연결", "#f38ba8")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AICadApp()
    app.run()
