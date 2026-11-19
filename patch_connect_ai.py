import os

TEMP_JS = os.path.join(os.path.dirname(__file__), "imported_source", "connect-ai-1.0.10", "temp.js")
OUT_JS = os.path.join(os.path.dirname(__file__), "imported_source", "connect-ai-1.0.10", "out", "extension.js")
SRC_TS = os.path.join(os.path.dirname(__file__), "imported_source", "connect-ai-1.0.10", "src", "extension.ts")

# 적용할 기본 언어 모델 목록 HTML
DEFAULT_OPTIONS_HTML = (
    '<select id="modelSel" style="background:#27272b;color:#fafafa;border:1px solid rgba(255,255,255,.2);'
    'padding:4px 8px;border-radius:6px;font-size:11px;min-width:115px;cursor:pointer;">'
    '<option value="gemma4:e4b" selected>gemma4:e4b</option>'
    '<option value="gemma4:e2b">gemma4:e2b</option>'
    '<option value="gemma4:12b">gemma4:12b</option>'
    '<option value="gemma2:latest">gemma2:latest</option>'
    '</select>'
)

def patch_file(filepath):
    print(f"Patching {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. <select id="modelSel"></select> 교체
    if '<select id="modelSel"></select>' in code:
        code = code.replace('<select id="modelSel"></select>', DEFAULT_OPTIONS_HTML)
        print("  ✅ <select id='modelSel'> 기본 모델 옵션 주입 완료!")
    else:
        print("  ℹ️ 이미 select 옵션이 교체되었거나 대상이 다릅니다.")

    # 2. ready 이벤트 시 모델 목록 전송 누락 수정
    old_ready = 'case "ready":\n          this._restoreDisplayMessages();\n          break;'
    new_ready = 'case "ready":\n          await this._sendModels();\n          this._restoreDisplayMessages();\n          break;'
    if old_ready in code:
        code = code.replace(old_ready, new_ready)
        print("  ✅ ready 이벤트 시 _sendModels() 호출 추가 완료!")

    # 3. 모델 전송 실패 시 기본 모델 4개 모두 전송하도록 개선
    old_fallback = 'this._view.webview.postMessage({ type: "modelsList", value: [defaultModel] });'
    new_fallback = 'this._view.webview.postMessage({ type: "modelsList", value: ["gemma4:e4b", "gemma4:e2b", "gemma4:12b", "gemma2:latest"] });'
    if old_fallback in code:
        code = code.replace(old_fallback, new_fallback)
        print("  ✅ fallback 모델 목록 확장 완료!")

    # 4. 웹뷰 시작 시 타이머 재전송
    old_timer = 'setTimeout(()=>vscode.postMessage({type:"ready"}),300);'
    new_timer = 'setTimeout(()=>vscode.postMessage({type:"ready"}),300);setTimeout(()=>vscode.postMessage({type:"getModels"}),600);setTimeout(()=>vscode.postMessage({type:"getModels"}),1500);'
    if old_timer in code:
        code = code.replace(old_timer, new_timer)
        print("  ✅ 웹뷰 모델 재요청 타이머 추가 완료!")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)

def main():
    if os.path.exists(TEMP_JS):
        patch_file(TEMP_JS)
    if os.path.exists(OUT_JS):
        patch_file(OUT_JS)

    print("\n🎉 모든 파일 패치 완료!")

if __name__ == "__main__":
    main()

