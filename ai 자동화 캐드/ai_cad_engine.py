# -*- coding: utf-8 -*-
"""
AI CAD 자연어 도면 자동화 엔진 (AutoCAD 연동 스크립트 생성기)
공종: 금속 하지틀(각파이프/트러스), 화스너 브라켓, 외장 판넬(알루미늄/복합판넬)
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, "prompt_input.txt")
OUTPUT_SCR = os.path.join(BASE_DIR, "ai_draw_output.scr")

def parse_natural_language(text):
    text = text.strip()
    data = {
        "width": 4000.0,
        "height": 3000.0,
        "type": "subframe",
        "pipe_w": 50.0,
        "pipe_h": 50.0,
        "pipe_pitch_x": 600.0,
        "pipe_pitch_y": 1200.0,
        "bracket_pitch": 900.0,
        "panel_joint": 15.0
    }

    # 1. 크기 (W x H)
    size_match = re.search(r'(\d{3,5})\s*[*xX×,]\s*(\d{3,5})', text)
    if size_match:
        data["width"] = float(size_match.group(1))
        data["height"] = float(size_match.group(2))

    # 2. 공종 구분
    if any(k in text for k in ["판넬", "패널", "와리", "복합판넬", "시트"]):
        data["type"] = "panel"
    else:
        data["type"] = "subframe"

    # 3. 파이프 규격
    pipe_match = re.search(r'(\d{2,3})\s*[*xX×]\s*(\d{2,3})', text)
    if pipe_match:
        data["pipe_w"] = float(pipe_match.group(1))
        data["pipe_h"] = float(pipe_match.group(2))

    # 4. 간격
    pitch_x = re.search(r'(?:세로|수직|간격|피치|종대)\s*[:=]?\s*(\d{3,4})', text)
    if pitch_x: data["pipe_pitch_x"] = float(pitch_x.group(1))

    pitch_y = re.search(r'(?:가로|수평|횡대)\s*[:=]?\s*(\d{3,4})', text)
    if pitch_y: data["pipe_pitch_y"] = float(pitch_y.group(1))

    fastener = re.search(r'(?:화스너|브라켓|앙카)\s*[:=]?\s*(\d{3,4})', text)
    if fastener: data["bracket_pitch"] = float(fastener.group(1))

    return data

def generate_subframe_scr(data):
    w, h = data["width"], data["height"]
    pw = data["pipe_w"]
    px, py = data["pipe_pitch_x"], data["pipe_pitch_y"]
    bp = data["bracket_pitch"]

    lines = ["CMDECHO 0", "OSMODE 0"]
    lines.append("-LAYER M 01_STRUCTURE_OUTLINE C 7 01_STRUCTURE_OUTLINE ")
    lines.append("-LAYER M 02_SUBFRAME_PIPE C 4 02_SUBFRAME_PIPE ")
    lines.append("-LAYER M 03_FASTENER_BRACKET C 1 03_FASTENER_BRACKET ")
    lines.append("-LAYER M 04_DIMENSION C 2 04_DIMENSION ")
    lines.append("-LAYER M 05_ANNOTATION C 3 05_ANNOTATION ")

    # 외곽선
    lines.append("-LAYER S 01_STRUCTURE_OUTLINE ")
    lines.append(f"RECTANG 0,0 {w},{h}")

    # 수직 각파이프
    lines.append("-LAYER S 02_SUBFRAME_PIPE ")
    x_list = [0.0]
    cx = px
    while cx < w - (px * 0.4):
        x_list.append(cx)
        cx += px
    if w not in x_list: x_list.append(w)

    for x in x_list:
        x1 = max(0.0, x - pw / 2) if x != 0.0 else 0.0
        x2 = min(w, x + pw / 2) if x != w else w
        if x == 0.0: x2 = pw
        if x == w: x1 = w - pw
        lines.append(f"RECTANG {x1:.1f},0 {x2:.1f},{h}")

    # 수평 각파이프
    y_list = [0.0]
    cy = py
    while cy < h - (py * 0.4):
        y_list.append(cy)
        cy += py
    if h not in y_list: y_list.append(h)

    for y in y_list:
        y1 = max(0.0, y - pw / 2) if y != 0.0 else 0.0
        y2 = min(h, y + pw / 2) if y != h else h
        if y == 0.0: y2 = pw
        if y == h: y1 = h - pw
        lines.append(f"RECTANG 0,{y1:.1f} {w},{y2:.1f}")

    # 화스너 브라켓
    lines.append("-LAYER S 03_FASTENER_BRACKET ")
    for x in x_list:
        c_by = bp / 2
        while c_by < h:
            lines.append(f"RECTANG {x-30:.1f},{c_by-40:.1f} {x+30:.1f},{c_by+40:.1f}")
            lines.append(f"CIRCLE {x:.1f},{c_by:.1f} 8")
            c_by += bp

    # 치수선 & 타이틀
    lines.append("-LAYER S 04_DIMENSION ")
    lines.append(f"DIMLINEAR 0,0 {w},0 0,-300")
    lines.append(f"DIMLINEAR 0,0 0,{h} -300,0")

    lines.append("-LAYER S 05_ANNOTATION ")
    lines.append(f"-TEXT 0,{-600} 120 0 금속하지틀도면({pw:.0f}x{data['pipe_h']:.0f}각파이프)-W:{w:.0f}xH:{h:.0f}")
    lines.append(f"-TEXT 0,{-800} 80 0 수직간격:@{px:.0f}|수평간격:@{py:.0f}|화스너:@{bp:.0f}")

    lines.append("ZOOM E")
    lines.append("CMDECHO 1")
    lines.append("")
    return "\n".join(lines)

def generate_panel_scr(data):
    w, h, joint = data["width"], data["height"], data["panel_joint"]
    nx = max(1, round(w / 1000.0))
    ny = max(1, round(h / 1200.0))
    pw = (w - (joint * (nx + 1))) / nx
    ph = (h - (joint * (ny + 1))) / ny

    lines = ["CMDECHO 0", "OSMODE 0"]
    lines.append("-LAYER M 01_WALL_OUTLINE C 7 01_WALL_OUTLINE ")
    lines.append("-LAYER M 02_PANEL_SHEET C 3 02_PANEL_SHEET ")
    lines.append("-LAYER M 04_DIMENSION C 2 04_DIMENSION ")
    lines.append("-LAYER M 05_PANEL_TAG C 4 05_PANEL_TAG ")

    lines.append("-LAYER S 01_WALL_OUTLINE ")
    lines.append(f"RECTANG 0,0 {w},{h}")

    lines.append("-LAYER S 02_PANEL_SHEET ")
    tag_num = 1
    for iy in range(ny):
        py_pt = joint + iy * (ph + joint)
        for ix in range(nx):
            px_pt = joint + ix * (pw + joint)
            lines.append(f"RECTANG {px_pt:.1f},{py_pt:.1f} {px_pt+pw:.1f},{py_pt+ph:.1f}")
            lines.append("-LAYER S 05_PANEL_TAG ")
            lines.append(f"-TEXT J MC {px_pt+pw/2:.1f},{py_pt+ph/2+30:.1f} 50 0 P-{tag_num:02d}")
            lines.append(f"-TEXT J MC {px_pt+pw/2:.1f},{py_pt+ph/2-30:.1f} 40 0 {pw:.0f}x{ph:.0f}")
            lines.append("-LAYER S 02_PANEL_SHEET ")
            tag_num += 1

    lines.append("-LAYER S 04_DIMENSION ")
    lines.append(f"DIMLINEAR 0,0 {w},0 0,-300")
    lines.append(f"DIMLINEAR 0,0 0,{h} -300,0")
    lines.append("ZOOM E")
    lines.append("CMDECHO 1")
    lines.append("")
    return "\n".join(lines)

def main():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    else:
        prompt = "4000x3000 각파이프 하지틀 간격 600 화스너 900"

    data = parse_natural_language(prompt)
    scr = generate_panel_scr(data) if data["type"] == "panel" else generate_subframe_scr(data)

    with open(OUTPUT_SCR, "w", encoding="cp949", errors="replace") as f:
        f.write(scr)

if __name__ == "__main__":
    main()
