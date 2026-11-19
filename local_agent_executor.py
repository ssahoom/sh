"""
Connect AI LAB의 3대 에이전트 액션을 파이썬 환경에 연동한 로컬 에이전트 실행기
- <create_file path="...">: 파일 자동 생성
- <edit_file path="..."><find>...</find><replace>...</replace></edit_file>: 파일 자동 편집
- <run_command>...</run_command>: 터미널 명령 실행
"""
import os
import re
import subprocess
from ollama_client import OllamaService

SYSTEM_AGENT_PROMPT = """You are "Connect AI LAB", a premium agentic AI coding assistant running 100% offline on the user's machine.

You have THREE powerful agent actions. Use them whenever appropriate:

━━━ ACTION 1: CREATE NEW FILES ━━━
<create_file path="relative/path/file.ext">
file content here
</create_file>

━━━ ACTION 2: EDIT EXISTING FILES ━━━
<edit_file path="relative/path/file.ext">
<find>exact text to find in the file</find>
<replace>replacement text</replace>
</edit_file>
You can have multiple <find>/<replace> pairs inside one <edit_file> block.

━━━ ACTION 3: RUN TERMINAL COMMANDS ━━━
<run_command>npm install express</run_command>

RULES:
1. ALWAYS respond in Korean unless asked otherwise.
2. Use agent actions automatically when the user's request requires creating, editing files, or running commands.
3. Outside of action blocks, briefly explain what you did.
4. For code that is just for explanation, use standard markdown code fences.
5. When editing files, the <find> text must EXACTLY match existing content in the file.
"""

class LocalAgentExecutor:
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.path.dirname(__file__)
        self.service = OllamaService()

    def execute_actions(self, ai_response: str) -> list[str]:
        """AI 응답 속의 에이전트 태그들을 분석하고 실제로 실행합니다."""
        reports = []

        # 1. 파일 생성 처리 (<create_file path="...">...</create_file>)
        create_pattern = re.compile(r'<create_file\s+path="([^"]+)">([\s\S]*?)</create_file>', re.MULTILINE)
        for match in create_pattern.finditer(ai_response):
            rel_path = match.group(1).strip()
            content = match.group(2)
            abs_path = os.path.join(self.workspace_root, rel_path)
            try:
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                reports.append(f"📁 [파일 생성] {rel_path} ({len(content)}자)")
            except Exception as e:
                reports.append(f"❌ [생성 실패] {rel_path}: {e}")

        # 2. 파일 편집 처리 (<edit_file path="...">...</edit_file>)
        edit_pattern = re.compile(r'<edit_file\s+path="([^"]+)">([\s\S]*?)</edit_file>', re.MULTILINE)
        fr_pattern = re.compile(r'<find>([\s\S]*?)</find>\s*<replace>([\s\S]*?)</replace>', re.MULTILINE)

        for match in edit_pattern.finditer(ai_response):
            rel_path = match.group(1).strip()
            body = match.group(2)
            abs_path = os.path.join(self.workspace_root, rel_path)

            if not os.path.exists(abs_path):
                reports.append(f"❌ [편집 실패] {rel_path}: 파일이 존재하지 않습니다.")
                continue

            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                edits = 0
                for fr_match in fr_pattern.finditer(body):
                    find_text = fr_match.group(1)
                    replace_text = fr_match.group(2)
                    if find_text in file_content:
                        file_content = file_content.replace(find_text, replace_text, 1)
                        edits += 1

                if edits > 0:
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    reports.append(f"✏️ [파일 편집] {rel_path} ({edits}곳 수정 완료)")
                else:
                    reports.append(f"⚠️ [편집 경고] {rel_path}: 일치하는 검색 대상을 찾지 못함")
            except Exception as e:
                reports.append(f"❌ [편집 실패] {rel_path}: {e}")

        # 3. 터미널 명령 처리 (<run_command>...</run_command>)
        cmd_pattern = re.compile(r'<run_command>([\s\S]*?)</run_command>', re.MULTILINE)
        for match in cmd_pattern.finditer(ai_response):
            cmd = match.group(1).strip()
            reports.append(f"🖥️ [명령어 감지] {cmd}")

        return reports

    def run(self, user_prompt: str, model: str = None) -> dict:
        """로컬 Ollama 모델에게 지시하고 에이전트 액션을 수행합니다."""
        print(f"🤖 로컬 에이전트 지시 중: {user_prompt}")
        ai_reply = self.service.chat(
            prompt=user_prompt,
            system_prompt=SYSTEM_AGENT_PROMPT,
            model=model
        )
        reports = self.execute_actions(ai_reply)
        return {
            "response": ai_reply,
            "reports": reports
        }

if __name__ == "__main__":
    agent = LocalAgentExecutor()
    print("=== Connect AI LAB 로컬 에이전트 테스트 ===")
    test_prompt = "hello.txt 파일을 만들고 'Hello, 1인 기업 with Ollama!'라고 적어줘."
    res = agent.run(test_prompt)
    print("\n--- AI 응답 ---")
    print(res["response"])
    print("\n--- 실행 결과 리포트 ---")
    for r in res["reports"]:
        print(r)

