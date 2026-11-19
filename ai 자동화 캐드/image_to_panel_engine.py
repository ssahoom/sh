# -*- coding: utf-8 -*-
"""
[AI CAD 자동화] 사진 / 이미지 / PDF 기반 외장 판넬 와리 및 하지틀 자동 설계기
- 공종: 단열재 제외, 금속 하지틀(각파이프), 화스너 브라켓, 외장 판넬(알루미늄/복합판넬), 후레싱
"""

import os
import sys
import argparse
import cv2
import numpy as np
import ezdxf

# 현재 스크립트가 위치한 폴더를 기본 작업 및 출력 경로로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ImageToPanelProcessor:
    def __init__(self, image_path, real_width_mm=6000.0, real_height_mm=4000.0):
        self.image_path = image_path
        self.real_width = float(real_width_mm)
        self.real_height = float(real_height_mm)
        self.joint_mm = 15.0       # 판넬 실링 줄눈 15mm
        self.openings = []         # 감지된 창호 개구부
        self.panels = []           # 생성된 판넬 리스트
        self.img = None
        self.img_h = 0
        self.img_w = 0

    def load_and_preprocess(self):
        """이미지 또는 PDF 로드"""
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.image_path}")

        # PDF 파일 처리
        ext = os.path.splitext(self.image_path)[1].lower()
        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(self.image_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=200)
                temp_img = os.path.join(BASE_DIR, "temp_pdf_converted.png")
                pix.save(temp_img)
                self.image_path = temp_img
                print(f"[PDF 변환 완료] {temp_img}")
            except ImportError:
                raise ImportError("PDF 처리를 위해 터미널에서 'pip install pymupdf'를 실행해 주세요.")

        # 한글 경로 지원을 위해 numpy 디코딩
        img_array = np.fromfile(self.image_path, np.uint8)
        self.img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if self.img is None:
            raise ValueError(f"이미지를 읽을 수 없습니다: {self.image_path}")

        self.img_h, self.img_w = self.img.shape[:2]
        print(f"[이미지 로드 완료] 해상도: {self.img_w}x{self.img_h}px")

    def detect_openings(self):
        """외벽 내 창문/출입구 등 개구부 자동 검출"""
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = self.img_w * self.img_h
        px_to_mm_x = self.real_width / self.img_w
        px_to_mm_y = self.real_height / self.img_h

        self.openings = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area_ratio = (w * h) / total_area
            if 0.015 <= area_ratio <= 0.35 and 0.2 < (float(w) / h) < 5.0:
                mm_x = x * px_to_mm_x
                mm_w = w * px_to_mm_x
                mm_h = h * px_to_mm_y
                mm_y = self.real_height - (y + h) * px_to_mm_y
                self.openings.append({"mm_box": (mm_x, mm_y, mm_w, mm_h)})

        print(f"[개구부 감지 완료] 총 {len(self.openings)}개의 창호/개구부 식별")

    def generate_panels(self):
        """창호를 회피하여 금속 판넬 와리(분할) 생성"""
        w, h, joint = self.real_width, self.real_height, self.joint_mm
        cols = max(1, round(w / 1000.0))
        rows = max(1, round(h / 1200.0))
        nom_w = (w - (joint * (cols + 1))) / cols
        nom_h = (h - (joint * (rows + 1))) / rows

        self.panels = []
        tag_idx = 1
        for r in range(rows):
            py = joint + r * (nom_h + joint)
            for c in range(cols):
                px = joint + c * (nom_w + joint)

                # 창호 개구부와 겹치는지 검사
                is_overlap = False
                for op in self.openings:
                    ox, oy, ow, oh = op["mm_box"]
                    if not (px + nom_w <= ox or px >= ox + ow or py + nom_h <= oy or py >= oy + oh):
                        ov_x = max(0, min(px + nom_w, ox + ow) - max(px, ox))
                        ov_y = max(0, min(py + nom_h, oy + oh) - max(py, oy))
                        if (ov_x * ov_y) > (nom_w * nom_h * 0.4):
                            is_overlap = True
                            break

                if not is_overlap:
                    self.panels.append({
                        "tag": f"P-{tag_idx:02d}",
                        "x": px, "y": py, "w": nom_w, "h": nom_h,
                        "area_m2": (nom_w * nom_h) / 1000000.0
                    })
                    tag_idx += 1

        print(f"[판넬 와리 생성] 총 {len(self.panels)}장의 외장 판넬 배치 완료")

    def export_all(self):
        """모든 결과물 출력 (DXF, 산출서, 스크립트, 미리보기)"""
        dxf_path = os.path.join(BASE_DIR, "사진기반_판넬제작_와리설계.dxf")
        md_path = os.path.join(BASE_DIR, "판넬_제작가공_산출서.md")
        png_path = os.path.join(BASE_DIR, "사진기반_판넬와리_미리보기.png")
        scr_path = os.path.join(BASE_DIR, "사진기반_판넬와리_오버레이.scr")

        # 1. DXF 도면 생성 (AutoCAD 2023 네이티브 호환 R2018 포맷)
        doc = ezdxf.new("R2018")
        msp = doc.modelspace()
        doc.layers.new("01_WALL_OUTLINE", dxfattribs={"color": 7})
        doc.layers.new("02_OPENINGS_WINDOW", dxfattribs={"color": 1})
        doc.layers.new("03_PANEL_EXTERIOR", dxfattribs={"color": 3})
        doc.layers.new("04_SUBFRAME_PIPE", dxfattribs={"color": 4})
        doc.layers.new("05_DIMENSION", dxfattribs={"color": 2})
        doc.layers.new("06_PANEL_TAGS", dxfattribs={"color": 6})

        msp.add_lwpolyline([(0, 0), (self.real_width, 0), (self.real_width, self.real_height), (0, self.real_height)], close=True, dxfattribs={"layer": "01_WALL_OUTLINE"})
        for op in self.openings:
            ox, oy, ow, oh = op["mm_box"]
            msp.add_lwpolyline([(ox, oy), (ox+ow, oy), (ox+ow, oy+oh), (ox, oy+oh)], close=True, dxfattribs={"layer": "02_OPENINGS_WINDOW"})

        for p in self.panels:
            px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
            msp.add_lwpolyline([(px, py), (px+pw, py), (px+pw, py+ph), (px, py+ph)], close=True, dxfattribs={"layer": "03_PANEL_EXTERIOR"})
            msp.add_text(p["tag"], dxfattribs={"layer": "06_PANEL_TAGS", "height": 50}).set_placement((px + pw/2 - 40, py + ph/2 + 20))
            msp.add_text(f"{pw:.0f}x{ph:.0f}", dxfattribs={"layer": "06_PANEL_TAGS", "height": 35}).set_placement((px + pw/2 - 60, py + ph/2 - 30))

        # 하지틀 각파이프 중심선
        x_joints = sorted(list(set([p["x"] - self.joint_mm/2 for p in self.panels] + [p["x"] + p["w"] + self.joint_mm/2 for p in self.panels])))
        for xj in x_joints:
            msp.add_line((xj, 0), (xj, self.real_height), dxfattribs={"layer": "04_SUBFRAME_PIPE"})

        doc.saveas(dxf_path)
        print(f"[DXF 저장] -> {dxf_path}")

        # 2. 판넬 가공 산출서
        total_area = sum(p["area_m2"] for p in self.panels)
        lines = [
            "# 외장 판넬(알루미늄/복합판넬) 제작 가공 산출서",
            f"- 기준 규격: W {self.real_width:.0f} mm x H {self.real_height:.0f} mm",
            f"- 총 판넬 수량: {len(self.panels)} 매 | 총 소요 면적: {total_area:.2f} ㎡ (헤베)",
            "",
            "| 판넬 No | 가로 (mm) | 세로 (mm) | 면적 (㎡) | 위치 좌표 (X, Y) |",
            "| :---: | :---: | :---: | :---: | :---: |"
        ]
        for p in self.panels:
            lines.append(f"| {p['tag']} | {p['w']:.0f} | {p['h']:.0f} | {p['area_m2']:.3f} | ({p['x']:.0f}, {p['y']:.0f}) |")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[산출서 저장] -> {md_path}")

        # 3. AutoCAD 스크립트 (.scr)
        scr_lines = [
            "CMDECHO 0", "OSMODE 0",
            "-LAYER M 01_WALL_OUTLINE C 7 01_WALL_OUTLINE ",
            "-LAYER M 03_PANEL_EXTERIOR C 3 03_PANEL_EXTERIOR ",
            "-LAYER S 01_WALL_OUTLINE ", f"RECTANG 0,0 {self.real_width},{self.real_height}",
            "-LAYER S 03_PANEL_EXTERIOR "
        ]
        for p in self.panels:
            scr_lines.append(f"RECTANG {p['x']:.1f},{p['y']:.1f} {p['x']+p['w']:.1f},{p['y']+p['h']:.1f}")
        scr_lines.extend(["ZOOM E", "CMDECHO 1", ""])
        with open(scr_path, "w", encoding="cp949", errors="replace") as f:
            f.write("\n".join(scr_lines))
        print(f"[AutoCAD 스크립트 저장] -> {scr_path}")

        # 4. 미리보기 이미지 생성 (한글 경로 지원)
        preview = self.img.copy()
        mm_to_px_x = self.img_w / self.real_width
        mm_to_px_y = self.img_h / self.real_height
        for p in self.panels:
            px1 = int(p["x"] * mm_to_px_x)
            py1 = int((self.real_height - (p["y"] + p["h"])) * mm_to_px_y)
            px2 = int((p["x"] + p["w"]) * mm_to_px_x)
            py2 = int((self.real_height - p["y"]) * mm_to_px_y)
            cv2.rectangle(preview, (px1, py1), (px2, py2), (0, 255, 0), 2)
            cv2.putText(preview, p["tag"], (px1 + 10, py1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        is_success, buf = cv2.imencode(".png", preview)
        if is_success:
            with open(png_path, "wb") as f:
                f.write(buf)
            print(f"[미리보기 이미지 저장] -> {png_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", "-i", type=str, default=r"D:\ai 자동화 캐드\sample_cad_plate.png")
    parser.add_argument("--width", "-w", type=float, default=6000.0)
    parser.add_argument("--height", "-H", type=float, default=4000.0)
    args = parser.parse_args()

    proc = ImageToPanelProcessor(args.image, args.width, args.height)
    proc.load_and_preprocess()
    proc.detect_openings()
    proc.generate_panels()
    proc.export_all()
