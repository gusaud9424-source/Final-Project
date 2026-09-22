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
        <h1 class="sq-dashboard__title">
          {{ authStore.isAdmin ? "전체 학생 현황" : "내 강의실" }}
        </h1>
        <p class="sq-dashboard__subtitle">
          {{
            authStore.isAdmin
              ? "전체 학생의 챕터별 진도를 확인하세요."
              : "챕터별 진도와 학습 현황을 한눈에 확인하세요."
          }}
        </p>
      </div>
      <router-link v-if="!authStore.isAdmin" to="/chapters" class="sq-dashboard__cta">
        챕터 선택하러 가기
      </router-link>
    </div>

    <StudentsOverview v-if="authStore.isAdmin" />

    <template v-else>
      <p v-if="loading" class="sq-dashboard__status">불러오는 중...</p>
      <p v-else-if="errorMessage" class="sq-dashboard__error">{{ errorMessage }}</p>

      <template v-else>
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
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useAuthStore } from "@/stores/auth";
import StudentsOverview from "@/components/dashboard/StudentsOverview.vue";

const authStore = useAuthStore();

const loading = ref(true);
const errorMessage = ref("");
const summary = ref({ courseCount: 0, completedRounds: 0, totalRounds: 0, percent: 0 });
const courses = ref([]);

onMounted(async () => {
  if (authStore.isAdmin) {
    loading.value = false;
    return;
  }
  try {
    const { data } = await client.get("/dashboard");
    summary.value = data.summary;
    courses.value = data.courses;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "대시보드 정보를 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
});
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
  color: var(--sq-color-on-accent);
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.sq-dashboard__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-dashboard__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
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
