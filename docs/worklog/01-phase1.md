# 01. Phase 1 — 모듈=과목 구조 전환

커밋: `2d9c8e2` `feat(phase1): module-as-course structure, course slug migration, enroll catalog`
(2026-09-25, 17개 파일 변경, +782/-141줄)

## 무엇을

6개 취약점(세부 유형 포함 8개)을 각각 독립된 **과목(Course)** 으로 다루도록 데이터 모델과 화면 구조를 전환했다.
`Course` 모델에 URL 친화적인 식별자 `slug`와 난이도 `difficulty`를 추가하고, 프론트엔드에는 8개 과목의 상세 정보를
담은 카탈로그(`enroll.js`)와 그 카탈로그를 보여주는 수강신청 화면(`EnrollView.vue`)을 새로 만들었다.

## 왜

과목마다 고유한 URL(`/chapters/command-injection` 등)로 접근할 수 있어야 실습 페이지·과목 상세 페이지를 독립적으로
라우팅할 수 있다. 정수 PK만으로는 사람이 읽을 수 있는 URL을 만들 수 없고, 난이도(초급/중급/고급) 값도 화면에 배지로
표시해야 하므로 스키마 확장이 필요했다.

## 어떻게

### DB 마이그레이션 — `338ece05201e_add_course_slug_and_difficulty.py`

```python
# revision = '338ece05201e', down_revision = 'b1a9b6c8c456'
with op.batch_alter_table('courses', schema=None) as batch_op:
    batch_op.add_column(sa.Column('slug', sa.String(length=60), nullable=True))
    batch_op.add_column(sa.Column('difficulty', sa.Enum('초급', '중급', '고급', name='course_difficulty'), nullable=True))
    batch_op.create_unique_constraint('uq_courses_slug', ['slug'])
```

`courses` 테이블에 `slug`(고유 제약)와 `difficulty` enum 컬럼을 추가하는 Alembic 마이그레이션이다.

> **Alembic 마이그레이션이란?** DB 스키마(테이블 구조)도 코드처럼 버전 관리가 필요하다. Alembic은 각 변경을
> `revision`(이 파일의 ID)과 `down_revision`(바로 이전 버전의 ID)으로 체인처럼 연결해서, `flask db upgrade`로
> "지금 DB 상태 → 최신 스키마"까지 순서대로 변경을 적용할 수 있게 해준다. 이 체인이 두 갈래로 갈라지는 문제와
> 그 해결 과정은 [05장](./05-command-injection.md)에서 자세히 다룬다.

### 시드 데이터 — `backend/seed.py`

8개 과목(Course) 레코드를 슬러그·난이도와 함께 생성하는 `CATALOG` 리스트가 이 커밋에서 추가됐다
(`command-injection`, `xss-reflected`, `xss-dom`, `xss-stored`, `sql-injection`, `csrf`, `file-upload`, `sql-injection-blind`).

### 프론트엔드 카탈로그 — `frontend/src/stores/enroll.js`

Pinia 스토어에 8개 과목의 `id`(=slug), `difficulty`, `title`, `desc`, 그리고 `detail.{summary, exploit, defense}`
(설명·공격 예시·방어 방법 텍스트)를 정적으로 담은 `items` 배열이 이 커밋에서 만들어졌다. 이 `detail` 텍스트는
이후 [05장](./05-command-injection.md)의 실습 페이지 "설명" 슬롯에서도 그대로 재사용된다.

### 수강신청 화면 — `frontend/src/views/EnrollView.vue` (신규, 415줄)

난이도별로 그룹핑된 과목 목록을 보여주고, 각 행을 펼치면 요약·공격 예시·방어 방법을 볼 수 있는 아코디언 UI다.

### 대시보드 카드 → 과목 상세 이동

`DashboardView.vue`가 이 커밋에서 대폭 수정되며(171줄), 수강 중인 과목을 카드 그리드로 보여주고 카드를 클릭하면
`/dashboard/courses/{slug}`(과목 상세)로 이동하는 흐름이 만들어졌다.

```js
// frontend/src/views/DashboardView.vue
function goToCourse(course) {
  router.push(`/dashboard/courses/${course.slug}`);
}
```

## 디자인 규칙 반영

이 커밋에서 `bootstrap-overrides.scss`, `design-tokens.css`가 함께 수정되며 "카드 radius를 0으로 강제한다"는
프로젝트 전역 라운드 제거 방침이 반영됐다(`CLAUDE.md` 4절의 "확정된 디자인 값"과 일치. `--sq-card-radius: 0` 주석에
"원 추출값 14px, 전역 라운드 미사용 방침으로 0 고정"이라고 명시되어 있다 — `frontend/src/assets/design-tokens.css`).

## 검증 방법과 결과

이 시점의 수동 검증 절차나 결과는 커밋 이력만으로는 확인할 수 없다 — **확인 필요**.
