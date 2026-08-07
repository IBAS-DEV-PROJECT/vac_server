## 공통 사항

### Base URL

```
https://{host}/api/v1
```

### 공통 응답 포맷

```json
// 성공
{
  "success": true,
  "data": { }
}

// 실패
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "아이디 또는 비밀번호를 다시 확인해주세요."
  }
}
```

### 인증 방식 — JWT (Access + Refresh, 회전 방식)

로그인 성공 시 Access Token, Refresh Token을 함께 발급합니다.

| 토큰 | 저장 위치(권장) | 만료 | 비고 |
| --- | --- | --- | --- |
| Access Token | 클라이언트 메모리 / SecureStore | 15~30분 | 매 요청 헤더에 포함 (회원가입, 로그인 제외) |
| Refresh Token | HttpOnly Secure Cookie (웹) / SecureStore (앱) | 14~30일 | 재발급 시 회전(rotate) |

```
Authorization: Bearer {access_token}
```

**Refresh Token 회전(Rotation) 방식**

- Access Token 만료 시 `/auth/refresh` 호출 → 새 Access Token + 새 Refresh Token 발급, 기존 Refresh Token은 즉시 폐기
- 탈취된 토큰 재사용 탐지: 이미 폐기된 Refresh Token으로 재요청이 들어오면 해당 사용자의 전체 세션을 강제 로그아웃 처리
- 서버는 Refresh Token을 해시로 저장(원문 저장 금지)

### 에러 코드

| 코드 | 발생 화면 | 메시지 |
| --- | --- | --- |
| `INVALID_CREDENTIALS` | 로그인 | 아이디 또는 비밀번호를 다시 확인해주세요. |
| `DUPLICATE_ID` | 회원가입 | 이미 사용 중인 아이디예요. 다시 입력해주세요. |
| `TOKEN_EXPIRED` | 인증 필요 API 전반 | 로그인이 만료되었습니다. 다시 로그인해주세요. |
| `REFRESH_TOKEN_REUSED` | 토큰 재발급 | 비정상적인 접근이 감지되어 로그아웃되었습니다. |

### 카테고리

topics: 일 / 관계 / 돈 / 건강 / 나 (+기타)

values: 성장 / 안정 / 자율 / 연결 / 인정 / 재미 / 효율 / 의미 / 책임 (+기타)

## API 문서

### 인증(Auth)

#### 아이디 중복 확인

- `GET /auth/id/check?id={id}`

**Response**

```json
{ 
	"success": true,
	"data": { 
		"available": true|false
	}
}
```

#### 회원가입

- `POST /auth/signup`

**Request**

```json
{
  "id": "layer2026",
  "nickname": "string",
  "password": "string",
  "passwordConfirm": "string"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "userId": "uuid"
  }
}
```

#### 로그인

- `POST /auth/login`

**Request**

```json
{
	"id": "layer2026",
	"password": "string"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "user": {
      "id": "uuid",
      "loginId": "layer2026",
      "nickname": "string"
    },
    "activateOnboarding": true|false // 첫 로그인 시 true
  }
}
```

#### 로그아웃

- `POST /auth/logout`
- 전달받은 Refresh Token을 즉시 폐기한다.

**Request**

```json
{ "refreshToken": "string" }
```

**Response**

```json
{
  "success": true,
  "data": null
}
```

#### 회원 탈퇴

- `DELETE /auth/delete`
- 계정 정보, 고민, 기록, 인사이트 데이터를 모두 삭제하고 해당 사용자의 전체 세션(Refresh Token)을 폐기한다.

**Response**

```json
{
  "success": true,
  "data": null
}
```

#### 토큰 재발급

- `POST /auth/refresh`

**Request**

```json
{ "refreshToken": "string" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "accessToken": "string",
    "refreshToken": "string"
  }
}
```

---

### 홈(Home)

#### 홈 화면 조회

- `GET /home`
- `ongoingConcerns`: 진행 중(`PENDING`) 상태의 고민을 **마지막 기록일 오래된 순**으로 정렬하여 **최대 3건** 반환한다.
- `ongoingConcernCount`: 진행 중인 고민의 전체 개수 (배열 길이와 별개)
- `recentRecords`: 작성일 **최신순**으로 **최대 3건** 반환한다.

**Response**

```json
{
  "success": true,
  "data": {
    "nickname": "닉네임",
    "ongoingConcernCount": 5,
    "ongoingConcerns": [
      {
        "concernId": "uuid",
        "title": "A사 vs B사",
        "topic": "일",
        "lastRecordDate": "2026-07-24"
      }
    ],
    "monthlyValueHighlight": {
      "topValue": "성장",
      "changeRateVsLastMonth": 12
    },
    "recentRecords": [
      {
        "recordId": "uuid",
        "decision": "A로 마음이 기움",
        "date": "2026-07-27",
        "value": "성장"
      }
    ]
  }
}
```

---

### 고민(Concerns)

#### 새 고민 작성

- `POST /concerns`

**Request**

```json
{
    "concern": "A사 vs B사",
	"topic": "일",
    "decision": "아직 못 정함 / A로 마음이 기움",
    "reason": "한 줄이면 충분해요",
    "value": "성장",
    "concernStatus": "PENDING|RESOLVED"
}
```

#### 이어쓸 고민 조회

- `GET /concerns/pending`
- 진행 중(`PENDING`) 상태의 고민만 조회한다. 정리된(`RESOLVED`) 고민은 포함하지 않는다.
- **마지막 기록일 오래된 순**으로 정렬한다.

**Response**

```json
{
	"success": true,
	"data": {
		"ongoingConcerns": [
			{
				"concernId": "uuid",
				"concern": "A사 vs B사",
				"topic": "일",
                "lastRecordDate": "2026-07-24",
                "recordCount": 4
            }
        ]
    }
}
```

#### 이어쓸 지난 기록 조회

- `GET /concerns/pending/{concernId}`
- 해당 고민의 지난 기록을 **최신순**으로 정렬한다.

**Response**

```json
{
	"success": true,
	"data": {
		"concern": "A사 vs B사",
		"records": [
			{
				"recordId": "uuid",
				"decision": "A사가 조금 더 마음에 남",
				"createdAt": "2026-07-20"
			}
		]
	}
}
```

#### 이어쓰기 기록 작성

- `POST /concerns/pending/{concernId}`

**Request**

```json
{
	"decision": "아직 못 정함 / A로 마음이 기움",
	"reason": "한 줄이면 충분해요",
	"value": "성장",
	"concernStatus": "PENDING|RESOLVED"
}
```

---

### 인사이트(Insights)

#### 인사이트 메인 조회

- `GET /insights?startDate=2025-07-01&endDate=2026-08-01&topics=일-진로&values=성장`
- `valueByTopic`: **기록 수가 많은 순**으로 정렬한다.
- `trend`: 조회 기간을 **항상 4개 구간**으로 균등 분할하므로 배열 길이는 4로 고정된다. 구간별 `startDate`/`endDate`는 서버가 계산한다.
- `largestIncrease` / `largestDecrease`: 증감폭이 가장 큰 가치를 반환하며, 동률인 경우에만 복수 항목을 포함한다.

**Response**

```json
{
  "success": true,
  "data": {
	  "valueByTopic" : [
			{
			  "topic": "일",
			  "valueDistribution": [
				  { "value": "성장", "percentage": 62 }
		        ],
			  "count": 12
            }
	  ],
	  "trend": [
		  {
			  "startDate": "2026-06-30",
			  "endDate": "2026-07-06",
			  "valueDistribution": [
					{ "value": "성장", "percentage": 47 }
				]
			}
	  ],
	  "largestIncrease": [
			{ "value": "성장", "increaseRate": 16 }
		],
		"largestDecrease": [
			{ "value": "안정", "decreaseRate": -4 }
		],
	  "insight": {
		  "mostTopic": ["일"],
		  "mostValue": ["성장"]
	  },
	  "totalCount": 48
	}
}
```

#### 기록 목록 조회

- `GET /insights/{topic}/records?startDate=2025-07-01&endDate=2026-08-01`
- `{topic}`은 주제명 문자열이며 URL 인코딩하여 전달한다.
- 기록은 **최신순**으로 정렬한다.

**Response**

```json
{
	"success": true,
	"data": {
		"topic": "건강",
		"records": [
			{
				"recordId": "uuid",
				"decision": "헬스 다시 시작",
				"value": "안정",
				"concernId": "uuid",
				"concern": "헬스 다시 시작할까",
                "recordDate": "2026-07-18"
		  }
		],
		"recordCount": 8
  }
}
```

#### 고민 타임라인 조회

- `GET /concerns/{concernId}/timeline`
- 기록은 **오래된 순**으로 정렬한다.

**Response**

```json
{
	"success": true,
	"data": {
		"concern": "헬스 다시 시작할까",
		"topic": "건강",
		"records": [
			{
				"recordId": "uuid",
				"decision": "오늘은 쉬어가기",
				"value": "안정",
				"createdAt": "2026-07-12"
			}
		],
		"recordCount": 2
	}
}
```