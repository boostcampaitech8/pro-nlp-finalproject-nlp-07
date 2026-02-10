# Mind Gym – AI Backend (ai branch)

본 브랜치는 Mind Gym 서비스의 **AI 백엔드 전용 브랜치**이다.  
웹(frontend / backend API)과 통신하여 요청을 받아 처리하며,  
대화 상태 관리, 멀티턴 대화 실행,  
Coach / Persona / Supervisor 모델 오케스트레이션을 담당한다.

---

## Branch Role

- 브랜치명: `ai`
- 역할:
  - 웹 서버로부터 HTTP 요청 수신
  - Redis 기반 세션 상태 관리
  - 멀티턴 대화 흐름 실행
  - Coach / Judge Multi-LoRA 모델 학습 (coach_train)
  - 모델 정량 평가 및 메트릭 측정 (coach_eval)
  - Coach / Persona / Supervisor 모델 호출
  - 대화 결과 및 피드백을 JSON 형태로 반환

본 브랜치는 **UI를 포함하지 않으며**,  
웹(frontend 또는 backend)에서 API 형태로 호출되어 사용된다.

---

## Project Structure

```text
ai/
├── app/
│   ├── coach_model.py          # Coach LLM 실제 구현체 (GPU 모델 로딩 및 추론 로직)
│   ├── coach_stub.py          # Coach 모델 인터페이스
│   ├── feedback_client.py     # 세션 기반 최종 피드백 생성
│   ├── graph.py               # 대화 실행 그래프 (Coach → Persona → Supervisor)
│   ├── main.py                # FastAPI 엔트리포인트
│   ├── persona_adapter.py     # Persona LLM 어댑터
│   ├── state_store.py         # Redis 기반 세션 상태 저장/복원
│   ├── supervisor_client.py   # Supervisor 검증 로직
│   └── __init__.py
│── coach_train/                # Coach/Judge 모델 학습 파이프라인 (V10)
│   └── train.py                # Unsloth 기반 Qwen2.5 Multi-LoRA 학습 실행 스크립트
│ 
├── coach_eval/                 # 모델 성능 평가 및 메트릭 측정
│   ├── eval_base_metrics.py    # Base 모델(학습 전) 성능 측정 비교군
│   ├── eval_v10_metrics.py     # V10 모델(Judge+Coach) 최종 성능 평가
│   ├── judge_score_eval.py     # Judge Adapter(개입 판단) 정확도 전용 
평가
│ 
│   └── judge_prompt.txt        # 평가에 사용되는 Judge 프롬프트 템플릿
├── tests/
│   ├── conftest.py
│   └── test_graph_memory.py   # Redis 기반 세션 메모리 검증 테스트
│
├── persona.py                 # Persona 설정 데이터 구조
└── README.md
```

## Core Architecture

### Session-based State Management
- 모든 대화는 `session_id` 단위로 관리된다.
- Redis를 사용하여 다음 상태 정보를 저장하고 복원한다.
  - persona cfg (persona_name, role_description, difficulty, style_notes 등)
  - transcript (멀티턴 대화 로그)
  - turn index
- 서버 재시작 이후에도 동일한 `session_id`로 이전 대화 상태를 복원할 수 있다.
- 웹 서버는 매 요청마다 persona 정보를 전달하지 않아도 되며, Redis에 저장된 cfg를 기준으로 동작한다.

### Multi-Agent Execution Flow
Mind Gym의 대화 처리는 단순 1:1 응답이 아니라, 여러 에이전트가 순차적으로 실행되는 그래프 기반 흐름으로 처리된다.

- 실행 순서: `load_state → coach → persona → supervisor → save_state`
- `debug=1` 옵션을 사용하면 응답에 실행 trace가 포함되며, 노드 실행 순서 및 내부 판단 결과를 확인할 수 있다.

#### Node Responsibilities
- `load_state`: Redis에서 세션 상태(cfg, transcript, turn 등) 로드
- `coach`: 사용자 발화를 평가하여 개입 필요 여부 판단 및 코칭 생성
- `persona`: 설정된 페르소나/난이도에 따라 역할 연기 발화 생성
- `supervisor`: coach/persona 출력의 일관성 및 정책 검증, 필요 시 rerun 판단
- `save_state`: 업데이트된 transcript 및 turn 등을 Redis에 저장

### Coach Model
- Coach는 사용자 발화를 분석하여 다음 필드를 생성한다.
  - `intervene`: 개입 여부(boolean)
  - `rewrite`: 교정/대안 제안(문장 또는 가이드)
  - `signals`: 개입 근거(리스크/화행/태도 등)
- GPU 모델은 import 시점이 아닌 lazy-loading 방식으로 로드되며, `COACH_ENABLED=1`에서 활성화된다.
- 추론은 이벤트 루프 블로킹을 줄이기 위해 별도 thread에서 수행한다.

### Persona
- Persona는 다음 cfg를 기반으로 역할 연기를 수행한다.
  - `persona_name`, `role_description`, `difficulty`, `style_notes`, `opening_hint`
- Persona는 Coach 판단 이후 실행되며, Coach 결과와 독립적으로 발화를 생성한다.
- 멀티턴 상황에서는 transcript(최근 N턴)를 입력으로 사용해 맥락을 유지한다.

### Supervisor
- Supervisor는 Coach/Persona 출력 결과를 검증한다.
  - 출력 형식/정책/일관성 확인
  - 필요 시 rerun 여부 판단(현재는 MVP 단계에서 제한적으로 사용)

---

## API Endpoints

### POST `/chat/start`
세션을 생성하고 persona cfg를 저장한다.

- Request body:
  - `session_id` (string)
  - `persona_name` (string)
  - `role_description` (string)
  - `difficulty` (int)
  - `style_notes` (string)
  - `use_supervisor` (bool)
  - `opening_hint` (string, optional)

### POST `/chat/message`
멀티턴 대화를 진행한다.

- Request body:
  - `session_id` (string)
  - `user_text` (string)
  - `use_supervisor` (bool)
- Optional query:
  - `debug=1` (내부 실행 trace 및 last_coach/last_supervisor 등 포함)

### POST `/chat/feedback`
세션 transcript를 기반으로 최종 피드백을 생성한다.

- Request body:
  - `session_id` (string)
- 존재하지 않는 `session_id`에 대해서는 404를 반환한다.

---

## Environment Variables

- Redis
  - `REDIS_URL=redis://localhost:6379/0`

- Coach
  - `COACH_ENABLED=1`
  - `COACH_MODEL_PATH=shinjipark/qwen2.5_14B_coach`

- Persona (LLM)
  - `CLOVA_ENDPOINT=...`
  - `CLOVA_API_KEY=...`

---

## Runtime Notes
- GPU 모델 사용 시 `uvicorn --reload`는 권장하지 않음(캐시 파일 변경으로 reload loop 가능)
- 현재 구조는 세션 단위 직렬 요청을 전제로 하며, Redis 레벨 락은 사용하지 않음
- MVP/데모 단계 기준으로 E2E 실행 및 멀티턴 동작은 검증 완료

---

## Coach Model Architecture
### 1. Coach Model Training (coach_train/)
Mind Gym의 핵심인 Coach 모델은 Multi-LoRA 아키텍처를 사용하여 train.py를 통해 학습된다.

Base Model: unsloth/Qwen2.5-14B-Instruct-bnb-4bit


Masking Strategy: input에는 -100으로 masking을 적용하고 모델의 출력값인 intervene, reason, coach_feedback에만 Loss를 계산하여 효율적인 학습을 진행함.


Social Self-Defense: "사회적 지능(Social Intelligence)"과 "품격 있는 호신술"을 가르치는 페르소나 적용.


### 2. Model Evaluation (coach_eval/)
학습된 모델의 성능을 정량적으로 검증하기 위한 모듈이다.

eval_v10_metrics.py: 학습된 V10 모델이 개입 여부(Intervene True/False)를 얼마나 정확하게 맞추는지(Accuracy/F1-score) 별도 측정.

judge_score_eval.py: gpt-4.1-mini 모델을 LLM-Judge로 사용한 루드릭 채점을 시행함. (루드릭 채점의 기준은 judge_prompt.txt 참고)

eval_base_metrics.py: 학습되지 않은 Base 모델과의 Intervene 성능 비교를 위한 기준점 마련.


## Status
- Coach 모델 연동 및 E2E 실행 검증 완료
- Multi-Agent 대화 흐름 정상 동작 확인
- 피드백 품질/평가 기준 고도화는 별도 이슈로 관리 예정
