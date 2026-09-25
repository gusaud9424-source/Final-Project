<!--
  SecuQuest — 과목 상세 (강의 · 과제 · 과목 정보)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-course">
    <router-link to="/dashboard" class="sq-course__back">← 내 강의실로 돌아가기</router-link>

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
            {{ progress.completed }}/{{ progress.total }} 과제 완료 · {{ progress.percent }}%
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

      <!-- 강의 -->
      <section v-if="activeTab === 'lecture'" class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">강의</h2>
        <p class="sq-course__text">{{ course.description }}</p>
        <p v-if="detail" class="sq-course__text">
          <template v-for="(part, i) in splitCode(detail.summary)" :key="i">
            <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
          </template>
        </p>
        <router-link :to="`/chapters/${course.slug}`" class="sq-btn">실습 시작</router-link>
      </section>

      <!-- 과제 -->
      <section v-else-if="activeTab === 'tasks'" class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">과제</h2>
        <ul class="sq-task-list">
          <li v-for="task in tasks" :key="task.key" class="sq-task">
            <span class="sq-task__title">{{ task.title }}</span>
            <span class="sq-task__hint">{{ TASK_HINTS[task.key] }}</span>
            <span class="sq-badge" :class="task.completed ? 'sq-badge--success' : 'sq-badge--round'">
              {{ task.completed ? "완료" : "미완료" }}
            </span>
            <span class="sq-task__date">{{ task.completed ? formatDate(task.completedAt) : "-" }}</span>
          </li>
        </ul>

        <div v-if="quiz" class="sq-quiz">
          <h3 class="sq-quiz__title">방어 퀴즈</h3>
          <p class="sq-quiz__question">
            <template v-for="(part, i) in splitCode(quiz.question)" :key="i">
              <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
            </template>
          </p>

          <p v-if="defenseCompleted" class="sq-quiz__result sq-quiz__result--correct">
            정답입니다. 방어 퀴즈 과제를 완료했습니다.
          </p>

          <form v-else class="sq-quiz__form" @submit.prevent="submitQuiz">
            <label v-for="(option, index) in quiz.options" :key="index" class="sq-quiz__option">
              <input v-model="selectedAnswer" type="radio" name="quiz" :value="index" />
              <span>
                <template v-for="(part, i) in splitCode(option)" :key="i">
                  <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
                </template>
              </span>
            </label>

            <p v-if="quizResult && !quizResult.correct" class="sq-quiz__result sq-quiz__result--wrong">
              오답입니다. {{ quizResult.explanation }}
            </p>
            <p v-if="quizError" class="sq-course__error">{{ quizError }}</p>

            <button type="submit" class="sq-btn" :disabled="selectedAnswer === null || quizSubmitting">
              {{ quizSubmitting ? "채점 중..." : "제출" }}
            </button>
          </form>
        </div>
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
import { useRoute } from "vue-router";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useEnrollStore } from "@/stores/enroll";

const TABS = [
  { key: "lecture", label: "강의" },
  { key: "tasks", label: "과제" },
  { key: "info", label: "과목 정보" },
];
const TASK_HINTS = {
  concept: "과목 정보 탭 열람",
  practice: "실습 페이지에서 공격 성공",
  defense: "방어 퀴즈 정답",
};
const INFO_FIELDS = [
  { key: "summary", label: "설명" },
  { key: "exploit", label: "공격 예시" },
  { key: "defense", label: "방어 방법" },
];
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };

const route = useRoute();
const enrollStore = useEnrollStore();
const slug = route.params.slug;

const loading = ref(true);
const errorMessage = ref("");
const errorStatus = ref(null);
const course = ref({});
const tasks = ref([]);
const progress = ref({ completed: 0, total: 0, percent: 0 });
const quiz = ref(null);
const activeTab = ref("lecture");

const selectedAnswer = ref(null);
const quizSubmitting = ref(false);
const quizResult = ref(null);
const quizError = ref("");
const conceptError = ref("");
let conceptRequested = false;

const detail = computed(() => enrollStore.items.find((i) => i.id === slug)?.detail || null);
const difficultyTone = computed(() => DIFFICULTY_TONE[course.value.difficulty] || "success");
const defenseCompleted = computed(() => tasks.value.some((t) => t.key === "defense" && t.completed));

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
  quiz.value = data.quiz;
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

async function submitQuiz() {
  if (selectedAnswer.value === null || quizSubmitting.value) return;
  quizSubmitting.value = true;
  quizError.value = "";
  quizResult.value = null;
  try {
    const { data } = await client.post(`/courses/${slug}/quiz`, { answer: selectedAnswer.value });
    quizResult.value = data;
    if (data.correct) await loadCourse();
  } catch (error) {
    quizError.value = getErrorMessage(error, "채점에 실패했습니다.");
  } finally {
    quizSubmitting.value = false;
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

/* 과제 목록 */
.sq-task-list {
  width: 100%;
  margin: 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--sq-card-border);
}

.sq-task {
  display: grid;
  grid-template-columns: 120px 1fr auto 100px;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 14px;
}

.sq-task__title {
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-task__hint,
.sq-task__date {
  color: var(--sq-text-sub);
}

.sq-task__date {
  text-align: right;
}

/* 퀴즈 */
.sq-quiz {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.sq-quiz__title {
  margin: 0;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-quiz__question {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--sq-text-main);
}

.sq-quiz__form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.sq-quiz__option {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  font-size: 14px;
  cursor: pointer;
}

.sq-quiz__option:has(input:checked) {
  border-color: var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
}

.sq-quiz__result {
  margin: 0;
  padding: 10px 12px;
  font-size: 14px;
}

.sq-quiz__result--correct {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-text-main);
}

.sq-quiz__result--wrong {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
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
  .sq-task {
    grid-template-columns: 1fr auto;
  }

  .sq-task__hint,
  .sq-task__date {
    grid-column: 1 / -1;
    text-align: left;
  }

  .sq-info {
    grid-template-columns: 1fr;
  }
}
</style>
