# 07. 보물상자 보상 수령 · 과목 상세 탭 라벨 변경

실습/미션 성공 시 XP·포인트를 즉시 원장에 넣던 자동 지급을 **미수령(pending) → 보물상자 클릭 수령** 방식으로 바꿨다.
보상 액수 계산(`XP_RANGES`/`POINT_RANGES` 범위 랜덤)은 그대로 유지했다.

## 7-1. 데이터 구조

- 새 테이블 `rewards` (마이그레이션 `752399d75810_add_rewards.py`, `down_revision = f07d2a4eadc5`)
  - `user_id`, `type`(xp/point), `amount`, `source`(practice/mission), `ref`(`practice:<slug>` / `mission:<slug>`),
    `reason`(목록 표시 문구), `created_at`, `claimed_at`(NULL=미수령)
  - `UNIQUE(user_id, source, ref, type)`, 인덱스 `(user_id, claimed_at)`
- 수령 시 원장(`xp_ledger`/`point_ledger`)에 같은 `source`·`ref`로 기록 → 원장 `UNIQUE(user_id, source, ref)`가 이중 반영의 2차 방어선

## 7-2. 흐름

1. 실습 성공 → `roll_pending(..., "practice")` → XP·포인트 2행 생성
2. 미션(방어 퀴즈) 정답 → `roll_pending(..., "mission")` → `MISSION_REWARD_TYPE[slug]` 1행 생성
   - 규칙: 초급 과목=경험치, 중급·고급 과목=포인트. 미등록 과목은 생성하지 않고 경고 로그
3. 중복 방지: 사용자 행 `SELECT … FOR UPDATE` 후 `rewards` 또는 기존 원장에 같은 `(source, ref)`가 있으면 생성하지 않음
   - 이미 자동 지급을 받은 과목은 새 방식에서 pending이 생기지 않는다
4. 수령: `POST /api/v1/rewards/<id>/claim`, `POST /api/v1/rewards/claim-all`, 목록 `GET /api/v1/rewards/pending`
   - 로그인 필수, 전역 CSRFProtect, limiter(claim 30/min, claim-all 5/min), 요청 본문 없음(금액은 DB 값만)

`reward_box.py`를 따로 두지 않고 `rewards.py`에 blueprint까지 합쳤다. 분리할 필수 이유가 없었기 때문이다.

## 7-3. 프론트엔드

- `components/layout/RewardChest.vue`: 헤더 프로필 왼쪽 버튼(`bi-gift-fill`) + 미수령 개수 배지, Teleport 모달
  - 항목 아이콘: 경험치 `bi-stars`, 포인트 `bi-coin`. 항목 클릭 수령, "모두 받기"
- `stores/reward.js`: `items`/`count`/`fetchPending`/`claim`/`claimAll`. 수령 응답의 보유치로 `profile` 스토어 즉시 갱신
- 실습·미션 성공 문구: "보상 대기 중: … — 상단 보물상자에서 받으세요"

## 7-4. 과목 상세 탭 라벨

- "강의" → "실습", "과제" → "미션" (탭 라벨 · 패널 제목 · 진행률/대시보드의 "과제 완료" 표기)
- 탭 key(`lecture`/`tasks`/`info`)는 그대로 유지해 참조를 깨지 않음
- "내 강의실", "강의별 진도"는 과목(강좌) 자체를 뜻하므로 변경하지 않음

## 7-5. 시연용 초기화

```bash
docker compose exec backend flask reset-rewards --email <이메일> --course command-injection        # 미리보기
docker compose exec backend flask reset-rewards --email <이메일> --course command-injection --yes  # 실제 삭제
```

해당 사용자·과목의 `practice:<slug>`/`mission:<slug>` 원장·`rewards` 행과 `task_progress(defense)`만 삭제한다.

## 7-6. 검증 상태

- 백엔드 `py_compile`, 변경된 Vue SFC 컴파일 통과
- `flask db upgrade` → `752399d75810 (head)`, `DESCRIBE rewards`로 컬럼·UNIQUE·인덱스 확인
- Flask test client(세션 주입, 실제 CSRF 토큰) 임시 스크립트로 14개 항목 PASS 후 스크립트·임시 사용자 삭제
  - 실습/미션 pending 생성, pending 단계 원장 미반영, 목록, claim → 원장 반영, 재claim 409, 없는 id 404,
    재성공 중복 생성 없음, 모두 받기, CSRF 없는 POST 400
  - student1의 기존 자동 지급 command-injection 실습은 재성공해도 pending 생성 안 됨
- 브라우저 최종 확인은 **확인 필요**
