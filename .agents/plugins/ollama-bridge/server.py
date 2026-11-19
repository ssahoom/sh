import os
import sys

# 프로젝트 루트 경로 추가 (ollama_client 가져오기 위함)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ollama_client import OllamaService
from mcp.server.mcpserver import MCPServer

server = MCPServer(name="local-ollama")
service = OllamaService()

@server.tool()
def ask_local_ollama(prompt: str, model: str = "gemma4:e4b") -> str:
    """
    내 PC 로컬 Ollama 모델(gemma4:e4b 등)에 질문을 전달하고 생성된 답변을 반환합니다.
    Args:
        prompt: 로컬 모델에게 요청할 프롬프트 질문/작업 내용
        model: 사용할 모델 태그 (기본값: 'gemma4:e4b', 또는 'gemma4:12b', 'gemma4:e2b', 'gemma2:latest')
    """
    try:
        return service.chat(prompt, model=model)
    except Exception as e:
        return f"로컬 Ollama 호출 실패: {e}"

@server.tool()
def list_local_models() -> str:
    """
    현재 PC의 Ollama에 설치되어 사용 가능한 로컬 모델 목록을 조회합니다.
    """
    try:
        models = service.list_installed_models()
        local_mods = [m for m in models if not m.endswith(":cloud")]
        return f"설치된 로컬 모델 목록: {', '.join(local_mods)}"
    except Exception as e:
        return f"모델 목록 조회 실패: {e}"

if __name__ == "__main__":
    server.run(transport="stdio")

