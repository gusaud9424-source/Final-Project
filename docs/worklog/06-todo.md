# 06. 남은 작업

현재 코드 상태를 기준으로, 다음에 해야 할 작업과 그 이유를 정리한다.

## 보상 UI 수정 (포인트/경험치 분리, 수령 버튼, Bootstrap Icons)

`frontend/src/components/layout/AppHeader.vue`의 프로필 드롭다운은 레벨·XP 진행바·포인트를 한 패널 안에
텍스트 줄로만 보여준다([04장](./04-phase3-5.md) 참고). 현재 `roll_and_grant`는 조건 충족 시 서버가 즉시
지급하는 구조라 "수령" 절차 자체가 없는데, 사용자 경험상 보상을 받는 순간을 명확히 보여주는 액션/애니메이션이
필요하다면 이 UI를 다듬어야 한다. Bootstrap Icons는 `EnrollView.vue`(`<i class="bi bi-...">`)에는 이미
쓰이고 있지만 `AppHeader.vue` 프로필 패널에는 아직 쓰이지 않았다(아바타는 이니셜 텍스트).

## 나머지 5개 취약점 모듈 구현

`backend/app/practice_builders/__init__.py`의 `PRACTICE_BUILDERS`에는 현재 `"command-injection"` 하나만
등록되어 있다. 프런트의 `ChapterDetailView.vue`도 `PRACTICE_SUPPORTED_SLUGS = ["command-injection"]`로
제한돼 있어, 나머지 과목은 "실습 준비 중" 메시지만 뜬다. [05장](./05-command-injection.md)에서 만든
`PracticeBuilder` 인터페이스(`validate_input`/`run`/`hints`)를 그대로 재사용해 다음 5개를 추가해야 한다:

- XSS (Reflected / DOM / Stored) 3종
- SQL Injection
- SQL Injection (Blind)
- File Upload

XSS·SQLi는 Command Injection처럼 sandbox 셸 실행이 아니라 각각 다른 판정 방식(응답 HTML 반영 여부, DB 쿼리
결과, 파일 저장/실행 여부)이 필요하므로, `run()` 내부 구현을 모듈별로 새로 설계해야 한다.

## 출석·포인트

`AttendanceSession` 모델은 존재하지만([03장](./03-phase3.md)) 대시보드 진도 계산에서 이미 제외됐고
실제로 출석을 기록하는 라우트가 있는지는 이 기록 시점 기준 확인되지 않았다 — 출석 체크 기능과, 그에 연동된
포인트 지급(`rewards.py`의 `"mission"` source 활용 후보)을 구현해야 한다.

## 힌트 시스템 확장

Command Injection에만 있는 `hints()` 구현([05장](./05-command-injection.md))을 나머지 5개 모듈에도
같은 3단계 원칙(개념 → 구체적 힌트 → 예시)으로 채워야 한다.

## 자료실 PDF

헤더 메뉴에 "자료실"(`/resources`) 링크와 `ResourcesView.vue`가 이미 존재하고, nginx도 `/pdf/` 경로를
backend로 프록시하도록 설정돼 있다([00장](./00-개요.md)). 하지만 실제로 PDF를 만들어 내려주는 백엔드 라우트가
구현돼 있는지는 확인되지 않았다 — `docs/architecture/architecture.md`에도 "PDF 모듈 역할(다운로드/리포트
생성 등) 구체화"가 "확정 필요" 항목으로 남아 있다.

## Sandbox 격리 최종 점검

Command Injection 모듈이 sandbox 실행 채널의 첫 실사용 사례였다([05장](./05-command-injection.md)). 지금은
`listen(1)`(동시 1개 연결만 처리)인 단일 공유 컨테이너 구조인데, 다른 5개 모듈까지 추가돼 트래픽이 늘어날 경우
이 구조가 충분한지, 또는 `docs/architecture/architecture.md`가 언급한 "요청마다 격리 컨테이너 동적 생성"
방식으로 바꿔야 하는지 재검토가 필요하다.
