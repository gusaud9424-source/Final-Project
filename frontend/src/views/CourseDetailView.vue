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

      <!-- 실습 탭 -->
      <section v-if="activeTab === 'lecture'" class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">실습</h2>

        <template v-if="guide">
          <div class="sq-guide-grid">
            <article class="sq-guide-card">
              <span class="sq-guide-card__label"><i class="bi bi-bullseye" aria-hidden="true"></i> 실습 목적</span>
              <p class="sq-guide-card__text">{{ guide.practice.goal }}</p>
            </article>
            <article class="sq-guide-card">
              <span class="sq-guide-card__label"><i class="bi bi-question-circle" aria-hidden="true"></i> 왜 배우나</span>
              <p class="sq-guide-card__text">{{ guide.practice.why }}</p>
            </article>
          </div>

          <article class="sq-guide-card sq-guide-card--wide">
            <span class="sq-guide-card__label"><i class="bi bi-window" aria-hidden="true"></i> 실습 화면</span>
            <p class="sq-guide-card__text">
              <template v-for="(part, i) in splitCode(guide.practice.scenario)" :key="i">
                <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
              </template>
            </p>
          </article>

          <article class="sq-guide-card sq-guide-card--wide">
            <span class="sq-guide-card__label"><i class="bi bi-list-ol" aria-hidden="true"></i> 진행 방법</span>
            <ol class="sq-guide-steps">
              <li v-for="(step, i) in guide.practice.steps" :key="i">
                <template v-for="(part, j) in splitCode(step)" :key="j">
                  <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
                </template>
              </li>
            </ol>
            <p class="sq-guide-tip"><i class="bi bi-lightbulb" aria-hidden="true"></i> {{ guide.practice.tip }}</p>
          </article>
        </template>
        <p v-else class="sq-course__text">{{ course.description }}</p>

        <router-link :to="`/chapters/${course.slug}`" class="sq-btn">실습 시작</router-link>
      </section>

      <!-- 미션 탭 -->
      <section v-else-if="activeTab === 'tasks'" class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">미션</h2>
        <p class="sq-course__hint">미션을 완수하면 오른쪽 칸에 받을 보상이 표시됩니다. 클릭해서 받으세요.</p>
        <p v-if="claimableCount" class="sq-course__notice">
          <i class="bi bi-gift-fill" aria-hidden="true"></i>
          받을 수 있는 보상이 {{ claimableCount }}개 있어요! 오른쪽 "보상 받기"를 눌러 받으세요.
        </p>

        <ul class="sq-mission-list">
          <li v-for="(task, index) in tasks" :key="task.key" class="sq-mission-card">
            <div class="sq-mission-card__head">
              <span class="sq-badge sq-badge--round">{{ index + 1 }}회차</span>
              <span class="sq-mission-card__title">{{ missionInfo(task.key).title }}</span>
              <span class="sq-badge" :class="task.completed ? 'sq-badge--success' : 'sq-badge--round'">
                {{ task.completed ? "완료" : "미완료" }}
              </span>
            </div>

            <!-- 미션 설명(왼쪽) + 보상(오른쪽), 높이·간격 맞춤 -->
            <div class="sq-mission-card__row">
              <p class="sq-mission-card__desc">{{ missionInfo(task.key).desc }}</p>
              <div class="sq-mission-reward">
                <RewardSlot
                  :state="rewardState(task.key)"
                  :busy="rewardStore.claiming"
                  @claim="claimReward(task.key)"
                />
              </div>
            </div>
          </li>
        </ul>

        <p v-if="rewardMessage" class="sq-course__error">{{ rewardMessage }}</p>

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
          :title="course.title"
          @close="quizModalOpen = false"
          @finished="onQuizFinished"
        />
      </section>

      <!-- 과목 정보 탭 -->
      <section v-else class="sq-course__panel" role="tabpanel">
        <h2 class="sq-course__section-title">과목 정보</h2>

        <template v-if="guide">
          <article class="sq-guide-card sq-guide-card--wide">
            <span class="sq-guide-card__label"><i class="bi bi-info-circle" aria-hidden="true"></i> 어떤 취약점인가</span>
            <p class="sq-guide-card__text">{{ guide.info.summary }}</p>
          </article>

          <article class="sq-guide-card sq-guide-card--wide sq-guide-card--soft">
            <span class="sq-guide-card__label"><i class="bi bi-chat-quote" aria-hidden="true"></i> 쉽게 말하면</span>
            <p class="sq-guide-card__text">{{ guide.info.analogy }}</p>
          </article>

          <div class="sq-guide-grid">
            <article class="sq-guide-card sq-guide-card--danger">
              <span class="sq-guide-card__label"><i class="bi bi-exclamation-triangle" aria-hidden="true"></i> 막지 못하면</span>
              <p class="sq-guide-card__text">{{ guide.info.impact }}</p>
            </article>
            <article class="sq-guide-card sq-guide-card--safe">
              <span class="sq-guide-card__label"><i class="bi bi-shield-check" aria-hidden="true"></i> 방어 방법</span>
              <p class="sq-guide-card__text">{{ guide.info.defense }}</p>
            </article>
          </div>

          <article v-if="detail" class="sq-guide-card sq-guide-card--wide">
            <span class="sq-guide-card__label"><i class="bi bi-code-slash" aria-hidden="true"></i> 공격 예시 (참고)</span>
            <p class="sq-guide-card__text">
              <template v-for="(part, i) in splitCode(detail.exploit)" :key="i">
                <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
              </template>
            </p>
          </article>
        </template>

        <dl v-else-if="detail" class="sq-info">
          <template v-for="field in INFO_FIELDS" :key="field.key">
            <dt>{{ field.label }}</dt>
            <dd>
              <template v-for="(part, i) in splitCode(detail[field.key])" :key="i">
                <code v-if="part.code">{{ part.text }}</code><template v-else>{{ part.text }}</template>
              </template>
            </dd>
          </template>
        </dl>

        <!-- 1회차 개념 학습 확인 문제: 3/5 이상 정답 시 완료 -->
        <ConceptCheck :slug="slug" :completed="conceptDone" @passed="onConceptPassed" />
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
import { useRewardStore } from "@/stores/reward";
import QuizSetModal from "@/components/practice/QuizSetModal.vue";
import RewardSlot from "@/components/practice/RewardSlot.vue";
import ConceptCheck from "@/components/practice/ConceptCheck.vue";
import { COURSE_GUIDES, MISSION_GUIDE } from "@/content/courseGuides";

const TABS = [
  { key: "lecture", label: "실습" },
  { key: "tasks", label: "미션" },
  { key: "info", label: "과목 정보" },
];
const INFO_FIELDS = [
  { key: "summary", label: "설명" },
  { key: "exploit", label: "공격 예시" },
  { key: "defense", label: "방어 방법" },
];
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };

const route = useRoute();
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
const rewardMessage = ref("");
// task_key → { status, items } (서버 /courses/<slug>/rewards)
const rewards = ref({});

const guide = computed(() => COURSE_GUIDES[slug] || null);
const detail = computed(() => enrollStore.items.find((i) => i.id === slug)?.detail || null);
const difficultyTone = computed(() => DIFFICULTY_TONE[course.value.difficulty] || "success");

function missionInfo(key) {
  return MISSION_GUIDE[key] || { title: key, desc: "" };
}

function rewardState(key) {
  return rewards.value[key] || { status: "none", items: [] };
}

// 수령 대기 중인 보상 개수 (미션 탭에서 받을 수 있는 보상)
const claimableCount = computed(() =>
  Object.values(rewards.value).filter((r) => r.status === "pending" && r.claimAt !== "chest").length
);

// 백틱(`)으로 감싼 구간을 code 조각으로 분리 (v-html 미사용)
function splitCode(text) {
  return (text || "").split("`").map((part, index) => ({ text: part, code: index % 2 === 1 }));
}

async function loadCourse() {
  const { data } = await client.get(`/courses/${slug}`);
  course.value = data.course;
  tasks.value = data.tasks;
  progress.value = data.progress;
}

async function loadRewards() {
  try {
    rewards.value = await rewardStore.fetchCourseRewards(slug);
  } catch {
    // 보상 상태 조회 실패는 과목 화면 로딩을 막지 않는다
  }
}

// 1회차 완료 여부 (확인 문제 통과 시 true)
const conceptDone = computed(() => !!tasks.value.find((t) => t.key === "concept")?.completed);

// 확인 문제 통과 → 진도·미션 보상 상태 갱신 (보상은 미션 탭에서 클릭해 수령)
async function onConceptPassed() {
  await loadCourse();
  await loadRewards();
}

function selectTab(key) {
  activeTab.value = key;
}

async function claimReward(taskKey) {
  rewardMessage.value = "";
  try {
    await rewardStore.claimTask(slug, taskKey);
    await loadRewards();
  } catch (error) {
    rewardMessage.value = getErrorMessage(error, "보상을 받지 못했습니다.");
  }
}

async function onQuizFinished(result) {
  if (result.passed) {
    await loadCourse();
    await loadRewards();
  }
}

onMounted(async () => {
  try {
    await loadCourse();
    await loadRewards();
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

.sq-course__hint {
  margin: 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-course__notice {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 10px 14px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent-subtle);
  font-size: 14px;
  font-weight: 600;
  color: var(--sq-color-accent);
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
  gap: 14px;
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

/* 학습 안내 카드 (실습 · 과목 정보 공용) */
.sq-guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.sq-guide-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 16px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
}

.sq-guide-card--wide {
  flex: 0 0 auto;
}

.sq-guide-card--soft {
  background: var(--sq-color-accent-subtle);
}

.sq-guide-card--danger {
  border-color: var(--sq-badge-absent-text);
}

.sq-guide-card--safe {
  border-color: var(--sq-badge-submitted-text);
}

.sq-guide-card__label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-guide-card--danger .sq-guide-card__label {
  color: var(--sq-badge-absent-text);
}

.sq-guide-card--safe .sq-guide-card__label {
  color: var(--sq-badge-submitted-text);
}

.sq-guide-card__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--sq-text-body);
}

.sq-guide-steps {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.sq-guide-tip {
  margin: 4px 0 0;
  padding: 10px 12px;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent-subtle);
  font-size: 13px;
  line-height: 1.6;
  color: var(--sq-text-main);
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
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
}

.sq-mission-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sq-mission-card__title {
  font-size: 15px;
  font-weight: 700;
  color: var(--sq-text-main);
}

/* 설명(왼쪽) + 보상(오른쪽): 같은 높이로 정렬 */
.sq-mission-card__row {
  display: flex;
  align-items: stretch;
  gap: 16px;
}

.sq-mission-card__desc {
  flex: 1;
  min-width: 0;
  margin: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent-subtle);
  font-size: 15px;
  line-height: 1.6;
  color: var(--sq-text-body);
}

.sq-mission-reward {
  flex: 0 0 200px;
  display: flex;
}

.sq-mission-quiz-btn {
  width: 100%;
  text-align: center;
}

/* 과목 정보 (fallback) */
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
  .sq-info,
  .sq-guide-grid {
    grid-template-columns: 1fr;
  }

  .sq-mission-card__row {
    flex-direction: column;
  }

  .sq-mission-reward {
    flex-basis: auto;
  }
}
</style>
