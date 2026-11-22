# 📱 영숙 — 회사 목표와 모든 에이전트의 개인 목표(_agents/{id}/goal.md) 및 최근 72시간 메모리를 요약하여, 현재 기업이 집중해야 할 영역(KPI 달성 관점)에 대한 브리핑을 작성해줘.

## 🎯 분석 및 실행 계획

요청하신 브리핑 작성 및 다음 작업 선정은 **📱 영숙 (Secretary)** 에이전트의 핵심 역할입니다. 현재 회사 목표, 모든 에이전트의 개인 목표, 그리고 지난 72시간의 메모리/의사결정 로그를 종합적으로 분석하여, 가장 높은 ROI를 창출할 수 있는 단일 작업을 식별하고 실행 브리프를 작성해야 합니다.

이 작업을 수행하기 위해 필요한 **[회사 목표], [에이전트별 개인 목표], [최근 72시간 메모리]** 데이터가 현재 환경에 주입되어 있지 않으므로, 데이터를 먼저 수집하는 단계가 필요합니다.

---

### 🛠️ 데이터 수집 요청 (Data Collection)

아래 명령을 실행하여 현재 시스템에 필요한 모든 최신 목표 및 메모리 데이터를 수집하고 분석에 사용 가능하도록 준비합니다.

<run_command>cd "d:\AI 1인 기업 test\_company\_agents\secretary\tools" && py -3 secretary_data_gather.py --goal --agents --memory72h</run_command>

---

### 🧠 기대되는 다음 단계 (Execution Plan)

데이터가 성공적으로 수집되면, **📱 영숙** 에이전트는 다음의 논리적 흐름에 따라 작업을 수행할 것입니다.

1.  **Goal Alignment Check:** 회사 목표(예: 월 매출 300만원)와 각 에이전트의 개인 목표를 대조하여, 현재 가장 높은 ROI를 목표로 하는 전략적 영역을 식별합니다.
2.  **Bottleneck/Opportunity Scan (72h Memory):** 지난 72시간 동안의 의사결정 로그와 메모리를 분석하여, 현재 진행 중인 프로젝트 중 **반복되지 않으면서** 병목 현상(Bottleneck)이 있거나 새로운 기회(Opportunity)가 발생한 지점을 포착합니다.
3.  **Single Task Selection (Highest Value):** KPI 달성과 수익화 관점에서, 가장 높은 가치를 가져올 수 있는 **단일 작업**을 최종 선정합니다. (이때, 이미 24시간 내에 진행 중인 유사 작업은 제외하고 새로운 각도로 진전시킵니다.)
4.  **Assignment & Briefing:** 선정된 단일 작업을 실행할 최적의 에이전트(1~2명)를 지정하고, 해당 작업을 즉시 시작할 수 있는 구체적인 실행 브리프를 작성하여 보고합니다.

**→ 최종 산출물:** [선정된 단일 작업의 브리핑 및 실행 우선순위 지정] (산출물: sessions/2026-11-21T21-25/business.md)

---
## 🛠️ 도구 실행 결과 (시스템 자동 실행)

### 🔧 실행: `cd "d:\AI 1인 기업 test\_company\_agents\secretary\tools" && py -3 secretary_data_gather.py --goal --ag`
```
C:\Users\ssaho\AppData\Local\Programs\Python\Python315-32\python.exe: can't open file 'd:\\AI 1인 기업 test\\_company\\_agents\\secretary\\tools\\secretary_data_gather.py': [Errno 2] No such file or directory
```
_❌ exit 2_
