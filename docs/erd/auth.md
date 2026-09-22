# 인증/학습 데이터 ERD

## Mermaid ER Diagram

```mermaid
erDiagram
    users ||--o{ enrollments : "enrolls"
    courses ||--o{ enrollments : "has"
    enrollments ||--o{ attendance_sessions : "has"
    users |o--o{ verification_codes : "requests"

    users {
        int id PK
        string username UK
        string password_hash
        enum role "admin | student"
        string name
        string email UK
        string phone
        datetime created_at
    }

    courses {
        int id PK
        string title
        string description
        string icon
        string instructor
        string schedule
        datetime created_at
    }

    enrollments {
        int id PK
        int user_id FK
        int course_id FK
        int percent
        string badge_type
        string badge_label
        datetime created_at
    }

    attendance_sessions {
        int id PK
        int enrollment_id FK
        int session_no
        enum status "submitted | absent"
    }

    verification_codes {
        int id PK
        int user_id FK "nullable"
        string target
        enum purpose "find_id | reset_password_email | reset_password_sms"
        string code_hash
        int attempts
        boolean verified
        datetime expires_at
        datetime created_at
    }
```

## 유니크 제약 · 인덱스

Mermaid erDiagram 표기로는 복합 제약을 직접 표현할 수 없어 별도로 정리한다.

| 테이블 | 제약/인덱스 | 대상 컬럼 | 목적 |
|---|---|---|---|
| `users` | UNIQUE | `username` | 로그인 아이디 중복 방지 |
| `users` | UNIQUE | `email` | 아이디/비밀번호 찾기 시 계정 식별 |
| `enrollments` | UNIQUE (복합) | `user_id, course_id` | 동일 강의 중복 수강 방지 |
| `attendance_sessions` | UNIQUE (복합) | `enrollment_id, session_no` | 동일 회차 중복 출석 기록 방지 |
| `verification_codes` | INDEX (복합) | `target, purpose` | 인증코드 조회 성능 |

## 관계 요약

- `users` 1 : N `enrollments` — 사용자는 여러 강의를 수강할 수 있다.
- `courses` 1 : N `enrollments` — 강의는 여러 사용자에게 수강될 수 있다.
- `enrollments` 1 : N `attendance_sessions` — 수강 건마다 회차별 출석 기록을 가진다.
- `users` 1 : N `verification_codes` — 아이디/비밀번호 찾기 인증코드는 사용자에 연결되며(`user_id` nullable), 이메일 인증코드와 SMS 인증코드가 같은 `user_id`로 검증됐는지 `reset-password/confirm` 단계에서 확인한다.
