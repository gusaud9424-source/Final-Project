# 02. Phase 2 — 수강신청 영속화 · 보안 수정

커밋: `8332216` `chore(security): bind nginx to 127.0.0.1` (2026-09-25 22:51),
`ade715c` `feat(phase2): persist enrollments via API` (2026-09-25 22:52)

## 무엇을

Phase 1까지는 "수강 중" 상태가 프론트엔드 Pinia 스토어의 로컬 값(`enrolled: false`)으로만 존재했다.
새로고침하면 사라지는 상태였다는 뜻이다. Phase 2에서는 이 상태를 실제 DB(`enrollments` 테이블)에 저장하고
API로 조회·생성하도록 바꿨다. 같은 날 저녁, nginx 포트 바인딩을 외부에 노출되지 않도록 좁히는 보안 수정도 함께 커밋됐다.

## 왜

로컬 상태만으로는 다른 기기·다른 세션에서 수강 여부가 일치하지 않고, [03장](./03-phase3.md)에서 만들 "수강한 과목만
과목 상세·실습에 접근 가능"이라는 규칙(`_load_enrolled_course` 가드)의 전제 조건이기도 하다. 서버가 진실의 원천이어야 한다.

## 어떻게

### API — `backend/app/enrollments.py` (신규)

```python
@bp.get("/enrollments")
def list_enrollments():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    slugs = (
        db.session.query(Course.slug)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == user.id, Course.slug.isnot(None))
        .all()
    )
    return jsonify(enrollments=[slug for (slug,) in slugs])
```

`GET /api/v1/enrollments`는 현재 로그인한 사용자가 수강 중인 과목의 slug 목록을 반환한다.
`POST /api/v1/enrollments`는 `course_slug`를 받아 새 수강 레코드를 만드는데, 동시에 같은 과목을 두 번 신청하는
경쟁 조건에 대비해 `UniqueConstraint(user_id, course_id)` 위반 시 `IntegrityError`를 잡아 "이미 수강 중"(409)으로
처리한다. 이 "사전 조회 + DB 유니크 제약 + `IntegrityError` catch" 패턴은 이후 과제 완료(`mark_task_complete`)와
보상 지급(`roll_and_grant`)에서도 반복되는, 이 프로젝트의 표준 멱등성 처리 방식이다
([03장](./03-phase3.md), [05장](./05-command-injection.md) 참고).

> **REST 엔드포인트란?** "자원(resource)을 URL로 표현하고, HTTP 메서드로 행위를 표현하는" API 설계 방식이다.
> 여기서는 `/enrollments`가 "수강 목록"이라는 자원이고, `GET`은 조회, `POST`는 새로 생성을 뜻한다.

### 프론트엔드 동기화 — `frontend/src/stores/enroll.js`, `frontend/src/views/EnrollView.vue`

`fetchEnrollments()`가 서버의 slug 목록으로 로컬 `items` 배열의 `enrolled` 플래그를 동기화하고,
`enroll(id)`는 `POST /enrollments` 호출 후 성공(또는 409 중복)일 때만 로컬 상태를 `true`로 바꾼다.

### 보안 수정 — `docker-compose.yml`

```diff
   nginx:
     ports:
-      - "8090:80"
+      - "127.0.0.1:8090:80"
```

기존에는 `8090:80`으로 모든 네트워크 인터페이스(`0.0.0.0`)에 바인딩되어 있어, 같은 네트워크의 다른 기기에서도
접근 가능한 상태였다. `127.0.0.1:8090:80`으로 바꿔 로컬호스트에서만 접근 가능하도록 좁혔다.
이 변경을 정확히 이 시점에 하게 된 배경(예: 스캔 시도 발견 등)은 커밋 메시지 외에 근거가 없어 **확인 필요**.

## 검증 방법과 결과

이 시점의 수동 검증 절차나 결과는 커밋 이력만으로는 확인할 수 없다 — **확인 필요**.
