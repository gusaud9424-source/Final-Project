<!--
  SecuQuest — 과목 상세 (실습 · 미션 · 과목 정보)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-course">
    <router-link to="/dashboard" class="sq-course__back">← 대시보드로 돌아가기</router-link>

    <p v-if="loading" class="sq-course__status">불러오는 중...</p>

    <div v-else-if="errorMessage" class="sq-course__panel">
      <p class="sq-course__error">{{ errorMessage }}</p>
      <router-link v-if="errorStatus === 403" to="/enroll" class="sq-btn">수강신청하러 가기</router-link>
    </div>

    <template v-else>
      <!-- 과목 헤더 -->
      <section class="sq-course__header">
        <div class="sq-course__header-main">
          <i class="bi sq-course__icon" :class="course.icon" aria-hidden="true"></i>
          <div>
            <span v-if="course.difficulty" class="sq-badge" :class="`sq-badge--${difficultyTone}`">
              {{ course.difficulty }}
            </span>
            <h1 class="sq-course__title">{{ course.title }}</h1>
            <p class="sq-course__desc">{{ course.description }}</p>
          </div>
        </div>

        <div class="sq-course__progress">
          <span class="sq-course__progress-label">
            {{ progress.completed }}/{{ progress.total }} 미션 완료 · {{ progress.percent }}%
          </span>
          <div
            class="sq-progress-bar"
            role="progressbar"
            :aria-valuenow="progress.percent"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div class="sq-progress-bar__fill" :style="{ width: progress.percent + '%' }"></div>
          </div>
        </div>
      </section>

      <!-- 탭 -->
      <nav class="sq-course__tabs" role="tablist">
        <button
          v-for="tab in TABS"
          :key="tab.key"
          type="button"
          role="tab"
          class="sq-course__tab"
          :class="{ 'sq-course__tab--active': activeTab === tab.key }"
          :aria-selected="activeTab === tab.key"
          @click="selectTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </nav>

      <!-- 실습 -->
      <section v-if="activeTab === 'lecture'" class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">실습</h2>
        <p class="sq-course__text">{{ course.description }}</p>
        <p v-if="detail" class="sq-course__text">
          <template v-for="(part, i) in splitCode(detail.summary)" :key="i">
            <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
          </template>
        </p>
        <router-link :to="`/chapters/${course.slug}`" class="sq-btn">실습 시작</router-link>
      </section>

      <!-- 미션 -->
      <section v-else-if="activeTab === 'tasks'" class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">미션</h2>

        <ul class="sq-mission-list">
          <li v-for="(task, index) in tasks" :key="task.key" class="sq-mission-card">
            <div class="sq-mission-card__head">
              <span class="sq-mission-card__title">{{ task.title }}</span>
              <button
                v-if="!task.completed && TASK_ACTION[task.key]"
                type="button"
                class="sq-mission-card__action"
                @click="TASK_ACTION[task.key].handler()"
              >
                {{ TASK_ACTION[task.key].label }}
              </button>
            </div>

            <div class="sq-mission-card__badges">
              <span class="sq-badge sq-badge--round">{{ index + 1 }}회차</span>
              <span class="sq-badge" :class="task.completed ? 'sq-badge--success' : 'sq-badge--round'">
                {{ task.completed ? "완료" : "미완료" }}
              </span>
            </div>

            <p class="sq-mission-card__desc">{{ TASK_HINTS[task.key] }}</p>

            <div class="sq-mission-card__submission">
              <span class="sq-mission-card__submission-label">내 제출물</span>
              <p class="sq-mission-card__submission-content">
                {{ task.completed ? SUBMISSION_TEXT[task.key] : "-" }}
              </p>
              <span class="sq-chip">{{ task.completed ? formatDate(task.completedAt) : "-" }}</span>
            </div>
          </li>
        </ul>

        <button
          type="button"
          class="sq-btn sq-mission-quiz-btn"
          :disabled="!course.quizSetAvailable"
          @click="quizModalOpen = true"
        >
          {{ course.quizSetAvailable ? "퀴즈 풀기" : "준비 중" }}
        </button>

        <QuizSetModal
          v-if="quizModalOpen"
          :slug="slug"
          @close="quizModalOpen = false"
          @finished="onQuizFinished"
        />
      </section>

      <!-- 과목 정보 -->
      <section v-else class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">과목 정보</h2>
        <p v-if="conceptError" class="sq-course__error">{{ conceptError }}</p>
        <dl v-if="detail" class="sq-info">
          <template v-for="field in INFO_FIELDS" :key="field.key">
            <dt>{{ field.label }}</dt>
            <dd>
              <template v-for="(part, i) in splitCode(detail[field.key])" :key="i">
                <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
              </template>
            </dd>
          </template>
        </dl>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useEnrollStore } from "@/stores/enroll";
import { useRewardStore } from "@/stores/reward";
import QuizSetModal from "@/components/practice/QuizSetModal.vue";

const TABS = [
  { key: "lecture", label: "실습" },
  { key: "tasks", label: "미션" },
  { key: "info", label: "과목 정보" },
];
const TASK_HINTS = {
  concept: "과목 정보 탭 열람",
  practice: "실습 페이지에서 공격 성공",
  defense: "방어 퀴즈 70% 이상 통과",
};
const SUBMISSION_TEXT = {
  concept: "과목 정보 열람 완료",
  practice: "실습 성공 판정 완료",
  defense: "퀴즈 통과",
};
const INFO_FIELDS = [
  { key: "summary", label: "설명" },
  { key: "exploit", label: "공격 예시" },
  { key: "defense", label: "방어 방법" },
];
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };

const route = useRoute();
const router = useRouter();
const enrollStore = useEnrollStore();
const rewardStore = useRewardStore();
const slug = route.params.slug;

const loading = ref(true);
const errorMessage = ref("");
const errorStatus = ref(null);
const course = ref({});
const tasks = ref([]);
const progress = ref({ completed: 0, total: 0, percent: 0 });
const activeTab = ref("lecture");

const quizModalOpen = ref(false);
const conceptError = ref("");
let conceptRequested = false;

const TASK_ACTION = {
  concept: { label: "이동", handler: () => selectTab("info") },
  practice: { label: "이동", handler: () => router.push(`/chapters/${slug}`) },
};

const detail = computed(() => enrollStore.items.find((i) => i.id === slug)?.detail || null);
const difficultyTone = computed(() => DIFFICULTY_TONE[course.value.difficulty] || "success");

// 백틱(`)으로 감싼 구간을 code 조각으로 분리 (v-html 미사용)
function splitCode(text) {
  return (text || "").split("`").map((part, index) => ({ text: part, code: index % 2 === 1 }));
}

function formatDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" });
}

async function loadCourse() {
  const { data } = await client.get(`/courses/${slug}`);
  course.value = data.course;
  tasks.value = data.tasks;
  progress.value = data.progress;
}

// 과목 정보 탭 최초 열람 시 concept 완료 처리(서버 멱등)
async function completeConcept() {
  const concept = tasks.value.find((t) => t.key === "concept");
  if (conceptRequested || concept?.completed) return;
  conceptRequested = true;
  conceptError.value = "";
  try {
    await client.post(`/courses/${slug}/tasks/concept`);
    await loadCourse();
  } catch (error) {
    conceptRequested = false;
    conceptError.value = getErrorMessage(error, "학습 기록을 저장하지 못했습니다.");
  }
}

function selectTab(key) {
  activeTab.value = key;
  if (key === "info") completeConcept();
}

async function onQuizFinished(result) {
  if (result.passed) {
    await loadCourse();
    // 미션 보상은 미수령 상태로 쌓이므로 보물상자 배지만 갱신
    if (result.rewarded) await rewardStore.fetchPending();
  }
}

onMounted(async () => {
  try {
    await loadCourse();
  } catch (error) {
    errorStatus.value = error.response?.status ?? null;
    errorMessage.value = getErrorMessage(error, "과목 정보를 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.sq-course {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
  color: var(--sq-text-body);
}

.sq-course__back {
  align-self: flex-start;
  font-size: 14px;
  font-weight: 600;
  color: var(--sq-text-link);
  text-decoration: none;
}

.sq-course__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-course__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

/* 과목 헤더 */
.sq-course__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-course__header-main {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 0;
}

.sq-course__icon {
  font-size: 32px;
  color: var(--sq-color-accent);
}

.sq-course__title {
  margin: 8px 0 4px;
  font-size: 28px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-course__desc {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-course__progress {
  flex: 0 1 280px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sq-course__progress-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

/* 진행 바: 999px 라운드는 대시보드와 동일하게 예외 유지 */
.sq-progress-bar {
  height: 8px;
  border-radius: 999px;
  background: var(--sq-card-border);
  overflow: hidden;
}

.sq-progress-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: var(--sq-color-accent);
}

/* 탭 */
.sq-course__tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--sq-header-border);
}

.sq-course__tab {
  padding: 12px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: var(--sq-radius-none);
  margin-bottom: -1px;
  background: transparent;
  font-size: 15px;
  font-weight: 600;
  color: var(--sq-text-header-tab-inactive);
  cursor: pointer;
}

.sq-course__tab--active {
  border-bottom-color: var(--sq-color-accent);
  color: var(--sq-color-accent);
}

/* 패널 */
.sq-course__panel {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-course__section-title {
  margin: 0;
  font-size: 18px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-course__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

.sq-course code {
  padding: 1px 6px;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent-subtle);
  color: var(--sq-text-main);
  font-size: 13px;
}

.sq-btn {
  display: inline-block;
  padding: 10px 20px;
  border: none;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}

.sq-btn:hover:not(:disabled) {
  background: var(--sq-color-accent-hover);
}

.sq-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 미션 카드 목록 */
.sq-mission-list {
  width: 100%;
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sq-mission-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
}

.sq-mission-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.sq-mission-card__title {
  font-size: 15px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-mission-card__action {
  padding: 6px 14px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: transparent;
  color: var(--sq-color-accent);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.sq-mission-card__action:hover {
  background: var(--sq-color-accent-subtle);
}

.sq-mission-card__badges {
  display: flex;
  gap: 6px;
}

.sq-mission-card__desc {
  margin: 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-mission-card__submission {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
}

.sq-mission-card__submission-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--sq-text-sub);
}

.sq-mission-card__submission-content {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-main);
}

.sq-chip {
  align-self: flex-start;
  padding: 4px 10px;
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  border: 1px solid var(--sq-card-border);
  font-size: 12px;
  color: var(--sq-text-sub);
}

.sq-mission-quiz-btn {
  width: 100%;
  text-align: center;
}

/* 과목 정보 */
.sq-info {
  margin: 0;
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
}

.sq-info dt {
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-info dd {
  margin: 0;
}

/* 배지 */
.sq-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--sq-radius-none);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.sq-badge--round {
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
}

.sq-badge--success {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-badge--warning {
  background: var(--sq-badge-dday-bg);
  color: var(--sq-badge-dday-text);
}

.sq-badge--danger {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

@media (max-width: 768px) {
  .sq-info {
    grid-template-columns: 1fr;
  }
}
</style>
