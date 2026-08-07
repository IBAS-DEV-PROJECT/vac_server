## 브랜치 전략 (GitHub Flow)

1인 개발이므로 PR 없이 `main` 브랜치에 직접 머지하는 것을 원칙으로 하되, 기능 단위 작업 이력을 남기기 위해 기능 브랜치는 유지합니다.

- `main` : 항상 배포 가능한 상태 유지
- `feature/*` : 신규 기능 개발 (`feature/login-api`)
- `fix/*` : 버그 수정 (`fix/upload-error`)

**작업 흐름**

1. `main`에서 브랜치 생성
2. 작업 및 커밋 (커밋 컨벤션 준수)
3. 로컬에서 테스트 통과 확인
4. `main`으로 직접 머지 (PR 생략)
5. 머지 후 기능 브랜치 삭제
6. `main`에 머지된 시점에 배포

## 커밋 컨벤션

형식: `<type>: <설명>`

| type | 설명 | 예시 |
| --- | --- | --- |
| feat | 새로운 기능 추가 | `feat: 로그인 기능 구현` |
| fix | 버그 수정 | `fix: 프로필 이미지 업로드 오류 수정` |
| docs | 문서 수정 (README 등) | `docs: API 명세서 업데이트` |
| style | 코드 포맷팅, 세미콜론 누락, 들여쓰기 등 (로직 변경 없음) | `style: Prettier 적용` |
| refactor | 리팩토링 (기능 변경 없이 코드 구조 개선) | `refactor: 중복 코드 함수로 분리` |
| test | 테스트 코드 추가 또는 수정 | `test: 회원가입 유닛 테스트 추가` |
| chore | 빌드 업무, 패키지 매니저 설정, 기타 잡동사니 작업 | `chore: lodash 패키지 추가` |
| perf | 성능 개선 | `perf: 데이터베이스 쿼리 속도 최적화` |
| ci | CI/CD 설정 파일 변경 (GitHub Actions, Docker 등) | `ci: GitHub Actions 빌드 워크플로우 수정` |