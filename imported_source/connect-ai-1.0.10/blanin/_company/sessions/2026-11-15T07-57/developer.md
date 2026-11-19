# 💻 코다리 — QC 컨설팅 서비스의 핵심 기능(Audit Trail 및 Drift Detection) 구현을 위한 API 엔드포인트 및 데이터베이스 스키마(Schema)를 구체적으로 설계하고 문서화하십시오. MVP의 기술적 안정성을 확보하는 데 집중할 것.

### 💻 코다리 (시니어 풀스택 엔지니어) 개인 메모리

#### QC 컨설팅 서비스의 핵심 기능(Audit Trail 및 Drift Detection) 구현을 위한 API 엔드포인트 및 데이터베이스 스키마(Schema) 설계

#### 핵심 기능
1. **Audit Trail**: 시스템 내 모든 중요한 이벤트를 기록하고 추적합니다.
2. **Drift Detection**: 시스템의 현재 상태와 기준 상태 간의 차이를 감지합니다.

#### API 엔드포인트 설계

##### Audit Trail 관련 API
1. **GET /audit-trail**
   - **Description**: 전체 Audit Trail 목록을 반환합니다.
   - **Request Parameters**:
     - `page` (Optional): 페이지 번호
     - `pageSize` (Optional): 페이지 크기
   - **Response**:
     ```json
     {
       "data": [
         {
           "id": "audit-trail-1",
           "timestamp": "2026-11-15T12:00:00Z",
           "action": "ACTION_NAME",
           "user": "USER_ID",
           "details": "ACTION_DETAILS"
         }
       ],
       "pagination": {
         "total": 10,
         "page": 1,
         "pageSize": 10
       }
     }
     ```

2. **POST /audit-trail**
   - **Description**: 새로운 Audit Trail 항목을 생성합니다.
   - **Request Body**:
     ```json
     {
       "action": "ACTION_NAME",
       "user": "USER_ID",
       "details": "ACTION_DETAILS"
     }
     ```
   - **Response**:
     ```json
     {
       "id": "audit-trail-2",
       "timestamp": "2026-11-15T12:00:00Z",
       "action": "ACTION_NAME",
       "user": "USER_ID",
       "details": "ACTION_DETAILS"
     }
     ```

##### Drift Detection 관련 API
1. **GET /drift-detection**
   - **Description**: 전체 Drift Detection 결과 목록을 반환합니다.
   - **Request Parameters**:
     - `page` (Optional): 페이지 번호
     - `pageSize` (Optional): 페이지 크기
   - **Response**:
     ```json
     {
       "data": [
         {
           "id": "drift-detection-1",
           "timestamp": "2026-11-15T12:00:00Z",
           "source": "SOURCE_NAME",
           "target": "TARGET_NAME",
           "differences": [
             {
               "path": "PATH_TO_DIFFERENCE",
               "currentValue": "CURRENT_VALUE",
               "expectedValue": "EXPECTED_VALUE"
             }
           ]
         }
       ],
       "pagination": {
         "total": 10,
         "page": 1,
         "pageSize": 10
       }
     }
     ```

2. **POST /drift-detection**
   - **Description**: 새로운 Drift Detection 결과를 생성합니다.
   - **Request Body**:
     ```json
     {
       "source": "SOURCE_NAME",
       "target": "TARGET_NAME",
       "differences": [
         {
           "path": "PATH_TO_DIFFERENCE",
           "currentValue": "CURRENT_VALUE",
           "expectedValue": "EXPECTED_VALUE"
         }
       ]
     }
     ```
   - **Response**:
     ```json
     {
       "id": "drift-detection-2",
       "timestamp": "2026-11-15T12:00:00Z",
       "source": "SOURCE_NAME",
       "target": "TARGET_NAME",
       "differences": [
         {
           "path": "PATH_TO_DIFFERENCE",
           "currentValue": "CURRENT_VALUE",
           "expectedValue": "EXPECTED_VALUE"
         }
       ]
     }
     ```

#### 데이터베이스 스키마(Schema) 설계

##### Audit Trail Table
| Column Name | Data Type | Description                 |
|-------------|-----------|-----------------------------|
| id          | UUID      | Audit Trail 고유 ID           |
| timestamp   | TIMESTAMP | 이벤트 발생 시간            |
| action      | VARCHAR   | 수행한 동작                 |
| user        | VARCHAR   | 사용자 ID                   |
| details     | TEXT      | 동작에 대한 추가 세부 정보 |

##### Drift Detection Table
| Column Name | Data Type | Description                 |
|-------------|-----------|-----------------------------|
| id          | UUID      | Drift Detection 고유 ID     |
| timestamp   | TIMESTAMP | 결과 발생 시간              |
| source      | VARCHAR   | 비교 대상의 소스 이름       |
| target      | VARCHAR   | 비교 대상의 대상 이름       |
| differences | JSON      | 차이점 목록                 |

#### 문서화
위에 설계된 API 엔드포인트와 데이터베이스 스키마를 문서화하여 회사의 기술 문서에 포함시킵니다.

#### 결론
위와 같이 QC 컨설팅 서비스의 핵심 기능(Audit Trail 및 Drift Detection)을 구현하기 위한 API 엔드포인트 및 데이터베이스 스키마를 구체적으로 설계하였습니다. 이 설계는 MVP의 기술적 안정성을 확보하는 데 초점을 맞추고 있습니다.
