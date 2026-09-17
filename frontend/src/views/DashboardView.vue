<!--
  SecuQuest — 학습 대시보드 (내 강의실)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-dashboard">
    <div class="sq-dashboard__head">
      <div>
        <h1 class="sq-dashboard__title">내 강의실</h1>
        <p class="sq-dashboard__subtitle">
          챕터별 진도와 학습 현황을 한눈에 확인하세요.
        </p>
      </div>
      <router-link to="/chapters" class="sq-dashboard__cta">
        챕터 선택하러 가기
      </router-link>
    </div>

    <section class="sq-summary-card">
      <div class="sq-summary-card__head">
        <span class="sq-summary-card__title">학습 요약</span>
        <span class="sq-badge sq-badge--round">
          {{ summary.completedRounds }}/{{ summary.totalRounds }} 회차 완료 ({{ summary.percent }}%)
        </span>
      </div>

      <div class="sq-summary-card__stats">
        <div class="sq-summary-stat">
          <span class="sq-summary-stat__label">수강 챕터</span>
          <span class="sq-summary-stat__value">{{ summary.courseCount }}개</span>
        </div>
        <div class="sq-summary-stat">
          <span class="sq-summary-stat__label">완료 회차</span>
          <span class="sq-summary-stat__value">{{ summary.completedRounds }}회</span>
        </div>
        <div class="sq-summary-stat">
          <span class="sq-summary-stat__label">전체 진도율</span>
          <span class="sq-summary-stat__value">{{ summary.percent }}%</span>
        </div>
      </div>

      <div
        class="sq-progress-bar sq-progress-bar--lg"
        role="progressbar"
        :aria-valuenow="summary.percent"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div class="sq-progress-bar__fill" :style="{ width: summary.percent + '%' }"></div>
      </div>
    </section>

    <div class="row g-3 sq-course-grid">
      <div class="col-6 col-lg-3" v-for="course in courses" :key="course.id">
        <article class="sq-course-card">
          <div class="sq-course-card__head">
            <i class="bi sq-course-card__icon" :class="course.icon" aria-hidden="true"></i>
            <span class="sq-badge" :class="`sq-badge--${course.badge.type}`">
              {{ course.badge.label }}
            </span>
          </div>

          <h3 class="sq-course-card__title">{{ course.title }}</h3>
          <p class="sq-course-card__desc">{{ course.description }}</p>

          <div class="sq-course-card__meta">
            <span class="sq-pill">
              <i class="bi bi-person-circle" aria-hidden="true"></i>
              {{ course.instructor }}
            </span>
            <span class="sq-pill">
              <i class="bi bi-calendar3" aria-hidden="true"></i>
              {{ course.schedule }}
            </span>
          </div>

          <div
            class="sq-progress-bar"
            role="progressbar"
            :aria-valuenow="course.percent"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div class="sq-progress-bar__fill" :style="{ width: course.percent + '%' }"></div>
          </div>
          <p class="sq-course-card__percent">{{ course.percent }}% 진행 중</p>

          <template v-if="course.attendance.sessions.length">
            <hr class="sq-course-card__divider" />
            <p class="sq-course-card__attendance-label">
              <i class="bi bi-calendar-check" aria-hidden="true"></i>
              출석 현황 ({{ course.attendance.done }}/{{ course.attendance.total }})
            </p>
            <div class="sq-course-card__sessions">
              <span
                v-for="session in course.attendance.sessions"
                :key="session.n"
                class="sq-badge"
                :class="session.status === 'submitted' ? 'sq-badge--submitted' : 'sq-badge--absent'"
              >
                {{ session.n }}회차 {{ session.status === "submitted" ? "출석" : "결석" }}
              </span>
            </div>
          </template>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
const summary = {
  courseCount: 6,
  completedRounds: 7,
  totalRounds: 24,
  percent: 29,
};

const courses = [
  {
    id: 1,
    icon: "bi-terminal",
    badge: { type: "round", label: "2/4 완료" },
    title: "Command Injection",
    description: "입력값 검증 우회로 시스템 명령을 실행하는 취약점 실습",
    instructor: "김보안",
    schedule: "월·10:00",
    percent: 50,
    attendance: {
      done: 2,
      total: 2,
      sessions: [
        { n: 1, status: "submitted" },
        { n: 2, status: "submitted" },
      ],
    },
  },
  {
    id: 2,
    icon: "bi-code-slash",
    badge: { type: "round", label: "0/4 완료" },
    title: "XSS",
    description: "DOM·반사·저장형 스크립트 삽입 공격 실습",
    instructor: "이지은",
    schedule: "목·15:00",
    percent: 0,
    attendance: {
      done: 0,
      total: 1,
      sessions: [{ n: 1, status: "absent" }],
    },
  },
  {
    id: 3,
    icon: "bi-database",
    badge: { type: "round", label: "2/4 완료" },
    title: "SQL Injection",
    description: "Union 기반 쿼리 조작으로 데이터를 추출하는 실습",
    instructor: "박준혁",
    schedule: "화·15:00",
    percent: 50,
    attendance: {
      done: 3,
      total: 3,
      sessions: [
        { n: 1, status: "submitted" },
        { n: 2, status: "submitted" },
        { n: 3, status: "submitted" },
      ],
    },
  },
  {
    id: 4,
    icon: "bi-search",
    badge: { type: "round", label: "0/4 완료" },
    title: "SQL Injection (Blind)",
    description: "응답 시간·참/거짓 반응으로 데이터를 추론하는 실습",
    instructor: "최유나",
    schedule: "금·13:00",
    percent: 0,
    attendance: { done: 0, total: 0, sessions: [] },
  },
  {
    id: 5,
    icon: "bi-cloud-upload",
    badge: { type: "round", label: "0/4 완료" },
    title: "File Upload",
    description: "확장자·MIME 우회로 악성 파일을 업로드하는 실습",
    instructor: "정하늘",
    schedule: "수·13:00",
    percent: 0,
    attendance: { done: 0, total: 0, sessions: [] },
  },
  {
    id: 6,
    icon: "bi-shield-exclamation",
    badge: { type: "dday", label: "대기 (예비 3번)" },
    title: "CSRF",
    description: "위조 요청으로 사용자 권한을 도용하는 공격 실습",
    instructor: "한서준",
    schedule: "금·10:00",
    percent: 0,
    attendance: { done: 0, total: 0, sessions: [] },
  },
];
</script>

<style scoped>
.sq-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-dashboard__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.sq-dashboard__title {
  font-size: 32px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
  margin: 0;
}

.sq-dashboard__subtitle {
  font-size: 14px;
  color: var(--sq-text-sub);
  margin: 6px 0 0;
}

.sq-dashboard__cta {
  flex-shrink: 0;
  padding: 12px 20px;
  border-radius: var(--sq-card-radius);
  background: var(--sq-color-accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.sq-summary-card {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-card-radius);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-summary-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.sq-summary-card__title {
  font-size: 18px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-summary-card__stats {
  display: flex;
  margin-bottom: 20px;
}

.sq-summary-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 20px;
  border-right: 1px solid var(--sq-card-border);
}

.sq-summary-stat:first-child {
  padding-left: 0;
}

.sq-summary-stat:last-child {
  border-right: none;
}

.sq-summary-stat__label {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-summary-stat__value {
  font-size: 24px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.sq-badge--round {
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
}

.sq-badge--submitted {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-badge--dday {
  background: var(--sq-badge-dday-bg);
  color: var(--sq-badge-dday-text);
}

.sq-badge--absent {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

.sq-progress-bar {
  height: 6px;
  border-radius: 999px;
  background: var(--sq-card-border);
  overflow: hidden;
}

.sq-progress-bar--lg {
  height: 10px;
}

.sq-progress-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: var(--sq-color-accent);
}

.sq-course-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-card-radius);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-course-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sq-course-card__icon {
  font-size: 22px;
  color: var(--sq-color-accent);
}

.sq-course-card__title {
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
  margin: 0;
}

.sq-course-card__desc {
  font-size: 13px;
  line-height: 1.4;
  color: var(--sq-text-sub);
  margin: 0;
}

.sq-course-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sq-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--sq-card-border);
  color: var(--sq-text-sub);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.sq-course-card__percent {
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
  margin: 0;
}

.sq-course-card__divider {
  margin: 0;
  border: none;
  border-top: 1px solid var(--sq-card-border);
}

.sq-course-card__attendance-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--sq-text-sub);
  margin: 0;
}

.sq-course-card__sessions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sq-course-card__sessions .sq-badge {
  padding: 4px 10px;
  font-size: 12px;
}
</style>
