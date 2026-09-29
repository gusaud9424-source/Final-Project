# SecuQuest 작업 기록 (Worklog)

SecuQuest는 웹 보안 6대 핵심 취약점(Command Injection, XSS 3종, SQL Injection, SQL Injection Blind, File Upload, CSRF)을
직접 실습하며 배우는 부트캠프 캡스톤 학습 플랫폼이다. Vue 3 + Flask + MariaDB + Redis + Nginx를 Docker Compose로 묶고,
실습 코드는 네트워크가 차단된 격리 sandbox 컨테이너 안에서만 실행된다.

이 문서는 프로젝트가 어떤 순서로, 왜 그런 설계를 거쳐 지금 상태에 이르렀는지를 커밋 이력과 실제 코드를 근거로 기록한다.
추측이나 창작 없이, 확인 가능한 사실만 적었고 불확실한 부분은 "확인 필요"로 표시했다.

## 목차

| 챕터 | 내용 |
|---|---|
| [00-개요](./00-개요.md) | 프로젝트 목적, 기술 스택, 아키텍처, 개발 환경·협업 방식 |
| [01-phase1](./01-phase1.md) | 모듈=과목 구조 전환, slug·difficulty 마이그레이션, 수강신청 카탈로그화 |
| [02-phase2](./02-phase2.md) | 수강신청 저장 API, nginx 포트 바인딩 보안 수정 |
| [03-phase3](./03-phase3.md) | 과목 상세 화면, task_progress 테이블, 방어 퀴즈 |
| [04-phase3.5](./04-phase3-5.md) | 레벨/XP/포인트 시스템, 격리 sandbox 실행 채널 |
| [05-command-injection](./05-command-injection.md) | 마이그레이션 정리, Command Injection 실습 모듈 설계·구현·검증 |
| [06-todo](./06-todo.md) | 남은 작업 목록 |
| [07-reward-box](./07-reward-box.md) | 보물상자 보상 수령(pending → claim), 과목 상세 탭 라벨 변경 |

각 챕터는 "무엇을 했는가 → 왜 그렇게 했는가 → 어떻게 구현했는가" 순서로 서술했으며,
코드는 핵심만 인용하고 전체는 파일 경로로 안내한다.
