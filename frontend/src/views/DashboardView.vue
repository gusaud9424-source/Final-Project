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
              {{ summary.completedTasks }}/{{ summary.totalTasks }} 과제 완료 ({{ summary.percent }}%)
            </span>
          </div>

          <div class="sq-summary-card__stats">
            <div class="sq-summary-stat">
              <span class="sq-summary-stat__label">수강 챕터</span>
              <span class="sq-summary-stat__value">{{ summary.courseCount }}개</span>
            </div>
            <div class="sq-summary-stat">
              <span class="sq-summary-stat__label">완료 과제</span>
              <span class="sq-summary-stat__value">{{ summary.completedTasks }}개</span>
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

        <div v-if="!courses.length" class="sq-empty-state">
          <p class="sq-empty-state__text">아직 수강 중인 과목이 없습니다.</p>
          <router-link to="/enroll" class="sq-dashboard__cta">수강신청하러 가기</router-link>
        </div>

        <div v-else class="row g-3 sq-course-grid">
          <div class="col-6 col-lg-3" v-for="course in courses" :key="course.id">
            <article
              class="sq-course-card"
              role="link"
              tabindex="0"
              :aria-label="`${course.title} 과목 상세로 이동`"
              @click="goToCourse(course)"
              @keydown.enter="goToCourse(course)"
              @keydown.space.prevent="goToCourse(course)"
            >
              <div class="sq-course-card__head">
                <i class="bi sq-course-card__icon" :class="course.icon" aria-hidden="true"></i>
              </div>

              <h3 class="sq-course-card__title">{{ course.title }}</h3>
              <p class="sq-course-card__desc">{{ course.description }}</p>

              <div
                class="sq-progress-bar"
                role="progressbar"
                :aria-valuenow="course.percent"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <div class="sq-progress-bar__fill" :style="{ width: course.percent + '%' }"></div>
              </div>
              <p class="sq-course-card__progress-label">
                {{ course.completed }}/{{ course.total }} 완료 · {{ course.percent }}%
              </p>
            </article>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useAuthStore } from "@/stores/auth";
import StudentsOverview from "@/components/dashboard/StudentsOverview.vue";

const authStore = useAuthStore();
const router = useRouter();

const loading = ref(true);
const errorMessage = ref("");
const summary = ref({ courseCount: 0, completedTasks: 0, totalTasks: 0, percent: 0 });
const courses = ref([]);

function goToCourse(course) {
  router.push(`/dashboard/courses/${course.slug}`);
}

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
  border-radius: var(--sq-radius-none);
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

.sq-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 48px var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  text-align: center;
}

.sq-empty-state__text {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-summary-card {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
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
  border-radius: var(--sq-radius-none);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.sq-badge--round {
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
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

.sq-course-grid {
  overflow: visible;
}

.sq-course-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
  cursor: pointer;
  transition: transform 200ms ease, border-color 200ms ease, background-color 200ms ease,
    box-shadow 200ms ease;
}

.sq-course-card:hover,
.sq-course-card:focus-visible {
  transform: scale(1.03);
  border-color: var(--sq-color-accent);
  background-image: linear-gradient(var(--sq-color-accent-subtle), var(--sq-color-accent-subtle));
  box-shadow: var(--sq-card-shadow-hover);
}

.sq-course-card:focus-visible {
  outline: none;
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

.sq-course-card__progress-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
  margin: 0;
}

@media (prefers-reduced-motion: reduce) {
  .sq-course-card {
    transition: border-color 200ms ease, background-color 200ms ease, box-shadow 200ms ease;
  }

  .sq-course-card:hover,
  .sq-course-card:focus-visible {
    transform: none;
  }
}
</style>
