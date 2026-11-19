# 💻 코다리 — QC 컨설팅 서비스의 핵심 기능(Audit Trail 및 Drift Detection)을 구현하기 위한 기술 스택(언어, 프레임워크)을 확정하고, MVP 초기 버전에 포함되어야 할 핵심 API 엔드포인트 및 데이터베이스 스키마(Schema)를 구체적으로 설계하십시오.

### 👤 현빈 (Developer)
CEO의 지시에 따라 QC 컨설팅 서비스의 핵심 기능(Audit Trail 및 Drift Detection)을 구현하기 위한 기술 스택(언어, 프레임워크)을 확정하고, MVP 초기 버전에 포함되어야 할 핵심 API 엔드포인트 및 데이터베이스 스키마(Schema)를 구체적으로 설계하겠습니다.

#### 기술 스택
1. **언어**: Python
2. **프레임워크**: Django, FastAPI (비동기 API 서버)
3. **데이터베이스**: PostgreSQL (관계형 데이터베이스)
4. **기타 도구**: Docker, Git, GitHub Actions (CI/CD)

#### 핵심 API 엔드포인트
1. **Audit Trail**
   - `/api/audit-trail/create`: 새로운 Audit Trail 생성
   - `/api/audit-trail/list`: 모든 Audit Trail 조회
   - `/api/audit-trail/detail/{id}`: 특정 Audit Trail 조회
   - `/api/audit-trail/update/{id}`: 특정 Audit Trail 수정
   - `/api/audit-trail/delete/{id}`: 특정 Audit Trail 삭제

2. **Drift Detection**
   - `/api/drift-detection/create`: 새로운 Drift Detection 생성
   - `/api/drift-detection/list`: 모든 Drift Detection 조회
   - `/api/drift-detection/detail/{id}`: 특정 Drift Detection 조회
   - `/api/drift-detection/update/{id}`: 특정 Drift Detection 수정
   - `/api/drift-detection/delete/{id}`: 특정 Drift Detection 삭제

3. **공통**
   - `/api/auth/login`: 사용자 로그인
   - `/api/auth/register`: 사용자 등록
   - `/api/auth/token/refresh`: 액세스 토큰 갱신

#### 데이터베이스 스키마 (Schema)
1. **Audit Trail**
   ```sql
   CREATE TABLE audit_trail (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       system_name VARCHAR(255) NOT NULL,
       operation_type VARCHAR(255) NOT NULL,
       operation_time TIMESTAMP NOT NULL,
       data JSONB,
       FOREIGN KEY (user_id) REFERENCES users(id)
   );
   ```

2. **Drift Detection**
   ```sql
   CREATE TABLE drift_detection (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       model_name VARCHAR(255) NOT NULL,
       detection_time TIMESTAMP NOT NULL,
       metrics JSONB,
       FOREIGN KEY (user_id) REFERENCES users(id)
   );
   ```

3. **Users**
   ```sql
   CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       username VARCHAR(255) UNIQUE NOT NULL,
       email VARCHAR(255) UNIQUE NOT NULL,
       password VARCHAR(255) NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

이제 QC 컨설팅 서비스의 MVP 초기 버전을 개발해보겠습니다. Developer 에이전트에게 위의 설계를 전달하고, 필요한 코드 및 설정 파일을 작성하라는 명령을 내립니다.

---

### 👤 현빈 (Developer)
Developer 에이전트에게 QC 컨설팅 서비스의 MVP 초기 버전을 개발해보겠습니다.

1. **프로젝트 설정**
   - Django 프로젝트 생성
   - FastAPI 프로젝트 생성
   - PostgreSQL 데이터베이스 설정

2. **모델 설정**
   - `audit_trail.py`와 `drift_detection.py` 모델 생성
   - `users.py` 모델 생성

3. **API 엔드포인트 생성**
   - `audit_trail.py`와 `drift_detection.py` 엔드포인트 생성
   - `auth.py` 엔드포인트 생성

4. **Dockerfile 및 docker-compose.yml 생성**

5. **CI/CD 설정 (GitHub Actions)**

이러한 작업을 시작해보세요. Developer 에이전트에게 위의 설계를 전달하고, 필요한 코드 및 설정 파일을 작성하라는 명령을 내립니다.
