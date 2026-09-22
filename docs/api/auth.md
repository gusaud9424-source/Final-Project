# 인증 API 명세 (`/api/v1/auth`, `/api/v1/dashboard`, `/api/v1/admin/students`)

> 모든 예시 값은 가상의 더미 값이며, 실제 계정·비밀번호·이메일·전화번호가 아니다.
> CSRF 토큰은 `GET /api/v1/auth/csrf` 로 발급받아 이후 모든 상태 변경 요청(POST)의 `X-CSRFToken` 헤더에 담아 보낸다.
> 세션 쿠키(`withCredentials`)가 항상 함께 전송되어야 한다.

## 공통 응답

| 상태 코드 | 의미 | 비고 |
|---|---|---|
| 400 | 요청 값 오류 / 인증코드 불일치·만료 / CSRF 토큰 만료 | CSRF 오류 시 `{"error": "csrf", "message": "..."}` |
| 401 | 로그인 필요 / 아이디·비밀번호 불일치 / 역할 불일치 | |
| 403 | 권한 없음 (관리자 전용 API에 일반 사용자 접근) | |
| 429 | 요청 제한 초과 (rate limit) | Flask-Limiter 기본 응답 |

## 엔드포인트 목록

| 엔드포인트 | 메서드 | 인증 필요 | CSRF | Rate limit | 요청 JSON | 응답 JSON (200) | 그 외 상태코드 |
|---|---|---|---|---|---|---|---|
| `/api/v1/auth/csrf` | GET | 아니오 | 불필요(토큰 발급) | 없음 | - | `{"csrf_token": "..."}` | - |
| `/api/v1/auth/login` | POST | 아니오 | 필요 | 10/min | `{"username": "user01", "password": "********", "role": "student"}` | `{"id": 1, "username": "user01", "name": "홍길동", "role": "student", "email": "user01@example.com"}` | 401(자격 불일치·역할 불일치) |
| `/api/v1/auth/logout` | POST | 예(세션) | 필요 | 없음 | - | `{"message": "로그아웃되었습니다."}` | - |
| `/api/v1/auth/me` | GET | 예(세션) | 불필요 | 없음 | - | `{"id": 1, "username": "user01", "name": "홍길동", "role": "student", "email": "user01@example.com"}` | 401(미로그인) |
| `/api/v1/auth/find-id/send-code` | POST | 아니오 | 필요 | 5/min | `{"email": "user01@example.com"}` | `{"message": "입력하신 정보가 유효하면 인증코드를 발송했습니다."}` (계정 존재 여부와 무관하게 동일 응답) | - |
| `/api/v1/auth/find-id/verify` | POST | 아니오 | 필요 | 10/min | `{"email": "user01@example.com", "code": "000000"}` | `{"username": "user01"}` | 400(코드 불일치·만료·5회 초과) |
| `/api/v1/auth/reset-password/send-email-code` | POST | 아니오 | 필요 | 5/min | `{"username": "user01", "email": "user01@example.com"}` | `{"message": "입력하신 정보가 유효하면 인증코드를 발송했습니다."}` | - |
| `/api/v1/auth/reset-password/send-sms-code` | POST | 아니오 | 필요 | 5/min | `{"username": "user01", "phone": "01000000000"}` | `{"message": "입력하신 정보가 유효하면 인증코드를 발송했습니다."}` | - |
| `/api/v1/auth/reset-password/verify-codes` | POST | 아니오 | 필요 | 10/min | `{"username": "user01", "email_code": "000000", "sms_code": "111111"}` | `{"message": "인증이 완료되었습니다. 새 비밀번호를 설정하세요."}` | 400(코드 불일치·만료·5회 초과 — 둘 중 하나라도 실패 시) |
| `/api/v1/auth/reset-password/confirm` | POST | 아니오(단, 직전 `verify-codes` 성공 세션 필요) | 필요 | 10/min | `{"username": "user01", "new_password": "********"}` | `{"message": "비밀번호가 변경되었습니다."}` | 400(비밀번호 8자 미만 / 인증 미완료) |
| `/api/v1/dashboard` | GET | 예(세션) | 불필요 | 없음 | - | student: `{"role": "student", "summary": {...}, "courses": [...]}` / admin: `{"role": "admin", "students": [...]}` | 401(미로그인) |
| `/api/v1/admin/students` | GET | 예(세션, admin) | 불필요 | 없음 | - | `{"students": [{"id": 1, "name": "...", "email": "...", "courses": [...]}]}` | 401(미로그인) / 403(관리자 아님) |

## 보안 정책 메모

- 로그인 성공 시 세션을 `clear()` 후 재발급(`session_interface.regenerate`)하여 세션 고정(session fixation)을 방지한다.
- 로그인 시 요청한 `role`이 계정의 실제 역할과 다르면 비밀번호가 맞아도 401을 반환한다.
- `find-id`/`reset-password`의 코드 발송 엔드포인트는 계정 존재 여부와 무관하게 항상 동일한 메시지를 반환해 계정 존재 여부 노출을 막는다.
- 인증코드는 5분 후 만료되며, 코드 1개당 5회 오답 시 무효화된다(`verification_codes.attempts`).
- `reset-password/confirm`은 `verify-codes`에서 세션에 저장한 `reset_user_id`가 요청한 `username`의 사용자 ID와 일치할 때만 허용되고, 사용된 인증코드는 삭제된다.
