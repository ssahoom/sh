import os
import zipfile

SOURCE_DIR = os.path.join(os.path.dirname(__file__), "imported_source", "connect-ai-1.0.10")
OUTPUT_VSIX = os.path.join(os.path.dirname(__file__), "connect-ai-lab-1.0.10.vsix")

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
  <Default Extension="md" ContentType="text/markdown"/>
  <Default Extension="txt" ContentType="text/plain"/>
  <Default Extension="js" ContentType="application/javascript"/>
</Types>"""

VSIX_MANIFEST_XML = """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="connect-ai-lab" Version="1.0.10" Publisher="connectailab"/>
    <DisplayName>Connect AI LAB</DisplayName>
    <Description xml:space="preserve">100% 로컬 AI 코딩 에이전트 — 파일 생성, 코드 편집, 터미널 실행을 오프라인으로. Ollama + Gemma/Llama/DeepSeek 지원.</Description>
    <Tags>ai,local,ollama,gemma,llama,deepseek,offline,agent,code-generation,connect-ai-lab,copilot</Tags>
    <Categories>Machine Learning,Programming Languages,Chat</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Icon>extension/assets/icon.png</Icon>
    <License>extension/LICENSE</License>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Icons.Default" Path="extension/assets/icon.png" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE" Addressable="true"/>
  </Assets>
</PackageManifest>"""

def build_vsix():
    print(f"📦 Packaging VSIX from {SOURCE_DIR}...")
    
    # Required files to include
    files_to_pack = [
        ("package.json", "extension/package.json"),
        ("README.md", "extension/README.md"),
        ("LICENSE", "extension/LICENSE"),
        ("assets/icon.png", "extension/assets/icon.png"),
        ("assets/icon.svg", "extension/assets/icon.svg"),
        ("out/extension.js", "extension/out/extension.js"),
    ]
    
    with zipfile.ZipFile(OUTPUT_VSIX, "w", zipfile.ZIP_DEFLATED) as z:
        # 1. Package metadata
        z.writestr("[Content_Types].xml", CONTENT_TYPES_XML.strip())
        z.writestr("extension.vsixmanifest", VSIX_MANIFEST_XML.strip())
        
        # 2. Extension files
        for src_rel, dst_path in files_to_pack:
            full_src = os.path.join(SOURCE_DIR, src_rel)
            if os.path.exists(full_src):
                z.write(full_src, dst_path)
                print(f"  + Added: {src_rel} -> {dst_path}")
            else:
                print(f"  ⚠️ Warning: {src_rel} not found!")

    print(f"🎉 Successfully built: {OUTPUT_VSIX} ({os.path.getsize(OUTPUT_VSIX):,} bytes)")

if __name__ == "__main__":
    build_vsix()

