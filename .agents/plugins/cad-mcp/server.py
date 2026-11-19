import os
import sys
import json
import ezdxf
from ezdxf import colors
from mcp.server.mcpserver import MCPServer

server = MCPServer(name="cad-automation-mcp")

# CAD 저장 기본 경로 (규칙 준수)
CAD_SAVE_DIR = r"D:\ai 자동화 캐드"
if not os.path.exists(CAD_SAVE_DIR):
    try:
        os.makedirs(CAD_SAVE_DIR, exist_ok=True)
    except:
        pass

@server.tool()
def create_subframe_drawing(
    width: float = 3000.0,
    height: float = 2400.0,
    pipe_spec: str = "100x50x2.3T",
    span: float = 600.0,
    bracket_spacing: float = 1200.0,
    filename: str = "금속하지틀_자동생성.dxf"
) -> str:
    """
    자연어로 요청된 치수와 간격에 맞춰 금속 하지틀(각파이프 + 화스너 브라켓) CAD DXF 도면을 자동 생성합니다.
    (단열재 제외, 순수 금속 공종 규칙 준수)
    
    Args:
        width: 전체 입면 가로 폭 (mm, 예: 3000.0)
        height: 전체 입면 세로 높이 (mm, 예: 2400.0)
        pipe_spec: 아연도 각파이프 규격 (기본: "100x50x2.3T" 또는 "50x50x2.3T")
        span: 수직 각파이프 설치 간격 (mm, 기본: 600.0)
        bracket_spacing: 슬래브/벽체 앵커 화스너 브라켓 수직 고정 간격 (mm, 기본: 1200.0)
        filename: 저장할 DXF 파일명 (기본: "금속하지틀_자동생성.dxf")
    """
    try:
        if not filename.lower().endswith(".dxf"):
            filename += ".dxf"
        output_path = os.path.join(CAD_SAVE_DIR, filename)

        doc = ezdxf.new("R2018", setup=True)
        msp = doc.modelspace()

        # 회사 표준 레이어 설정 (단열재 제외)
        doc.layers.add(name="AA-STRUCTURE", color=colors.RED, linetype="Continuous")
        doc.layers.add(name="AA-STEEL-FRAME", color=colors.CYAN, linetype="Continuous")
        doc.layers.add(name="AA-BRACKET", color=colors.YELLOW, linetype="Continuous")
        doc.layers.add(name="AA-DIMS", color=colors.WHITE, linetype="Continuous")

        # 1. 외곽 구조체 바운더리 라인
        msp.add_lwpolyline([(0, 0), (width, 0), (width, height), (0, height), (0, 0)], dxfattribs={"layer": "AA-STRUCTURE", "lineweight": 40})

        # 파이프 치수 파싱
        p_w = 100.0 if "100" in pipe_spec else 50.0
        p_d = 50.0

        # 2. 수직 각파이프 배열 (스팬 간격)
        x_positions = []
        curr_x = 0.0
        while curr_x <= width:
            x_positions.append(curr_x)
            curr_x += span
        if x_positions[-1] < width:
            x_positions.append(width)

        pipe_count = len(x_positions)
        bracket_count = 0

        for x in x_positions:
            # 수직 파이프 단면선
            pts = [(x, 0), (x + p_w, 0), (x + p_w, height), (x, height), (x, 0)]
            msp.add_lwpolyline(pts, dxfattribs={"layer": "AA-STEEL-FRAME", "lineweight": 50})

            # 수직 파이프마다 화스너 브라켓 고정점 배치
            curr_y = 150.0
            while curr_y < height:
                # L형 브라켓 형상
                b_pts = [(x - 15, curr_y - 20), (x + p_w + 15, curr_y - 20), (x + p_w + 15, curr_y + 20), (x - 15, curr_y + 20), (x - 15, curr_y - 20)]
                msp.add_lwpolyline(b_pts, dxfattribs={"layer": "AA-BRACKET", "lineweight": 35})
                # 앵커 볼트 위치
                msp.add_circle((x + (p_w / 2.0), curr_y), radius=7.0, dxfattribs={"layer": "AA-BRACKET"})
                bracket_count += 1
                curr_y += bracket_spacing

        # 치수 및 표기 텍스트
        msp.add_text(f"SUB-FRAME ELEVATION ({int(width)} x {int(height)} mm)", dxfattribs={"layer": "AA-DIMS", "height": 35.0}).set_placement((0, height + 80.0))
        msp.add_text(f"PIPE: {pipe_spec} @ {int(span)} SPAN | BRACKET: L-TYPE @ {int(bracket_spacing)}", dxfattribs={"layer": "AA-DIMS", "height": 22.0}).set_placement((0, height + 40.0))

        try:
            doc.saveas(output_path)
        except Exception as e_save:
            # 샌드박스 쓰기 권한 제한 시 워크스페이스 내 생성 후 이동 시도
            fallback_path = os.path.join(os.path.abspath(r'd:\AI 1인 기업 test'), filename)
            doc.saveas(fallback_path)
            output_path = fallback_path
        return (
            f"✅ 금속 하지틀 CAD 도면 생성 완료!\n"
            f"- 저장 위치: {output_path}\n"
            f"- 규격: {width}x{height} mm (스팬: {span}mm)\n"
            f"- 각파이프 규격: {pipe_spec} (총 {pipe_count}본 산출)\n"
            f"- 화스너 브라켓: L형 앵커 브라켓 (총 {bracket_count}개소 배치)"
        )
    except Exception as e:
        return f"❌ 도면 생성 실패: {str(e)}"

@server.tool()
def create_panel_layout_drawing(
    total_width: float = 3000.0,
    total_height: float = 2400.0,
    panel_type: str = "AL_SHEET_3T",
    joint_width: float = 15.0,
    max_panel_w: float = 1200.0,
    max_panel_h: float = 1000.0,
    filename: str = "외장판넬_와리분할.dxf"
) -> str:
    """
    건물 외벽 치수에 맞춰 알루미늄 복합판넬/시트의 와리(분할) 및 줄눈(메지 15mm) 도면을 자동 생성합니다.
    
    Args:
        total_width: 외벽 전체 가로 폭 (mm, 예: 3000.0)
        total_height: 외벽 전체 세로 높이 (mm, 예: 2400.0)
        panel_type: 판넬 자재 종류 (기본: "AL_SHEET_3T" 또는 "AL_COMPOSITE_4T")
        joint_width: 판넬 간 실리콘 줄눈(메지) 폭 (mm, 기본: 15.0)
        max_panel_w: 판넬 1장당 최대 가로 치수 (mm, 기본: 1200.0)
        max_panel_h: 판넬 1장당 최대 세로 치수 (mm, 기본: 1000.0)
        filename: 저장할 DXF 파일명 (기본: "외장판넬_와리분할.dxf")
    """
    try:
        if not filename.lower().endswith(".dxf"):
            filename += ".dxf"
        output_path = os.path.join(CAD_SAVE_DIR, filename)

        doc = ezdxf.new("R2018", setup=True)
        msp = doc.modelspace()

        doc.layers.add(name="AA-STRUCTURE", color=colors.RED, linetype="Continuous")
        doc.layers.add(name="AA-PANEL", color=colors.GREEN, linetype="Continuous")
        doc.layers.add(name="AA-JOINT", color=colors.YELLOW, linetype="Continuous")
        doc.layers.add(name="AA-DIMS", color=colors.WHITE, linetype="Continuous")

        # 분할 개수 계산
        cols = int(total_width // max_panel_w) + (1 if total_width % max_panel_w > 0 else 0)
        rows = int(total_height // max_panel_h) + (1 if total_height % max_panel_h > 0 else 0)

        # 각 판넬 순수 치수 (줄눈 차감 균등 분할)
        panel_w = (total_width - (joint_width * (cols - 1))) / cols
        panel_h = (total_height - (joint_width * (rows - 1))) / rows

        panel_count = cols * rows
        total_sqm = (total_width * total_height) / 1000000.0

        for c in range(cols):
            for r in range(rows):
                x = c * (panel_w + joint_width)
                y = r * (panel_h + joint_width)
                pts = [(x, y), (x + panel_w, y), (x + panel_w, y + panel_h), (x, y + panel_h), (x, y)]
                msp.add_lwpolyline(pts, dxfattribs={"layer": "AA-PANEL", "lineweight": 50})

                # 판넬 넘버링 및 치수
                p_no = f"P{c+1}-{r+1}"
                msp.add_text(p_no, dxfattribs={"layer": "AA-DIMS", "height": 18.0}).set_placement((x + 20, y + 20))

        # 메타 타이틀
        msp.add_text(f"EXTERIOR PANEL ELEVATION LAYOUT ({panel_type})", dxfattribs={"layer": "AA-DIMS", "height": 32.0}).set_placement((0, total_height + 70.0))
        msp.add_text(f"PANEL SIZE: {int(panel_w)} x {int(panel_h)} mm | JOINT: {int(joint_width)}mm | TOTAL: {panel_count} EA ({round(total_sqm, 2)} m2)", dxfattribs={"layer": "AA-DIMS", "height": 20.0}).set_placement((0, total_height + 35.0))

        try:
            doc.saveas(output_path)
        except Exception as e_save:
            # 샌드박스 쓰기 권한 제한 시 워크스페이스 내 생성 후 이동 시도
            fallback_path = os.path.join(os.path.abspath(r'd:\AI 1인 기업 test'), filename)
            doc.saveas(fallback_path)
            output_path = fallback_path
        return (
            f"✅ 외장 판넬 와리 도면 생성 완료!\n"
            f"- 저장 위치: {output_path}\n"
            f"- 전체 면적: {round(total_sqm, 2)} ㎡ ({total_width}x{total_height} mm)\n"
            f"- 판넬 자재: {panel_type}\n"
            f"- 와리 분할: {cols}열 x {rows}행 (총 {panel_count}장)\n"
            f"- 1장당 가공 치수: {int(panel_w)} x {int(panel_h)} mm (줄눈: {joint_width}mm)"
        )
    except Exception as e:
        return f"❌ 판넬 도면 생성 실패: {str(e)}"

@server.tool()
def read_and_analyze_dxf(filename: str) -> str:
    """
    'D:\\ai 자동화 캐드' 폴더에 있는 특정 DXF 도면을 읽어서 레이어 목록, 객체 수, 텍스트 표기 등을 분석합니다.
    
    Args:
        filename: 분석할 DXF 파일 이름 (예: "sample_cad_plate.dxf")
    """
    try:
        path = os.path.join(CAD_SAVE_DIR, filename) if not os.path.isabs(filename) else filename
        if not os.path.exists(path):
            return f"❌ 파일을 찾을 수 없습니다: {path}"

        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
        layers = [l.dxf.name for l in doc.layers]
        
        entities = {}
        texts = []
        for e in msp:
            t = e.dxftype()
            entities[t] = entities.get(t, 0) + 1
            if t in ("TEXT", "MTEXT"):
                texts.append(getattr(e.dxf, "text", "")[:30])

        return (
            f"📋 DXF 도면 분석 결과 ({os.path.basename(path)}):\n"
            f"- 등록 레이어 ({len(layers)}개): {', '.join(layers[:12])}\n"
            f"- 도면 엔티티 통계: {entities}\n"
            f"- 도면 텍스트 샘플: {texts[:8]}"
        )
    except Exception as e:
        return f"❌ DXF 분석 실패: {str(e)}"

if __name__ == "__main__":
    server.run(transport="stdio")
