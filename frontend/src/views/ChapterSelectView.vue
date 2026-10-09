<!--
  SecuQuest — 학습 진도 (난이도별 과목 목록 + 과목별 진도율)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-chapters">
    <!-- 상단 요약 카드 -->
    <section class="sq-chapters__header">
      <div class="sq-chapters__header-text">
        <h1 class="sq-chapters__title">학습 진도</h1>
        <p class="sq-chapters__subtitle">
          초급 → 중급 → 고급 순서로 학습하세요. 진도율은 실습 레벨(하 · 중 · 상 · 안전)을 통과할 때마다 올라갑니다. 8개 과목을 모두 수강하고 각 과목의 4레벨을 전부 통과하면 전체 100%입니다.
        </p>
      </div>

      <div v-if="!authStore.isAdmin" class="sq-chapters__overall">
        <div class="sq-chapters__overall-head">
          <span class="sq-chapters__overall-label">전체 진도율</span>
          <span class="sq-chapters__overall-value">{{ overall.percent }}%</span>
        </div>
        <div
          class="sq-progress-bar sq-progress-bar--lg"
          role="progressbar"
          :aria-valuenow="overall.percent"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label="전체 진도율"
        >
          <div class="sq-progress-bar__fill" :style="{ width: overall.percent + '%' }"></div>
        </div>
        <span class="sq-chapters__overall-meta">
          수강 중 {{ overall.enrolled }}/{{ enrollStore.items.length }}과목 · 실습 레벨 {{ overall.completed }}/{{ overall.total }} 통과
        </span>
      </div>
    </section>

    <p v-if="loading" class="sq-chapters__status">불러오는 중...</p>
    <p v-else-if="errorMessage" class="sq-chapters__error" role="alert">{{ errorMessage }}</p>

    <template v-else>
      <p v-if="authStore.isAdmin" class="sq-chapters__status">
        관리자 계정은 진도가 집계되지 않습니다. 학생 진도는 학습 대시보드에서 확인하세요.
      </p>

      <section v-for="group in groups" :key="group.difficulty" class="sq-diff-group">
        <h2 class="sq-diff-group__title">
          <span class="sq-badge" :class="`sq-badge--${difficultyTone(group.difficulty)}`">
            {{ group.difficulty }}
          </span>
          <span class="sq-diff-group__meta">{{ group.items.length }}과목</span>
        </h2>

        <div class="row g-3">
          <div v-for="course in group.items" :key="course.id" class="col-12 col-md-6 col-xl-4">
            <article
              class="sq-chapter-card"
              :class="{ 'sq-chapter-card--locked': !course.enrolled }"
            >
              <div class="sq-chapter-card__head">
                <i class="bi sq-chapter-card__icon" :class="course.icon" aria-hidden="true"></i>
                <span
                  class="sq-chapter-card__state"
                  :class="`sq-chapter-card__state--${course.state.tone}`"
                >
                  {{ course.state.label }}
                </span>
              </div>

              <h3 class="sq-chapter-card__title">{{ course.title }}</h3>
              <p class="sq-chapter-card__desc">{{ course.desc }}</p>

              <template v-if="course.enrolled">
                <div
                  class="sq-progress-bar"
                  role="progressbar"
                  :aria-valuenow="course.percent"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`${course.title} 진도율`"
                >
                  <div class="sq-progress-bar__fill" :style="{ width: course.percent + '%' }"></div>
                </div>
                <p class="sq-chapter-card__progress-label">
                  실습 레벨 {{ course.completed }}/{{ course.total }} 통과 · {{ course.percent }}%
                </p>

                <ul class="sq-step-list" aria-label="실습 레벨별 통과 상태">
                  <li
                    v-for="step in STEPS"
                    :key="step.key"
                    class="sq-step"
                    :class="{ 'sq-step--done': course.doneKeys.includes(step.key) }"
                  >
                    <i
                      class="bi"
                      :class="course.doneKeys.includes(step.key) ? 'bi-check-circle-fill' : 'bi-circle'"
                      aria-hidden="true"
                    ></i>
                    {{ step.label }}
                  </li>
                </ul>
              </template>
              <p v-else class="sq-chapter-card__hint">수강신청 후 학습할 수 있습니다.</p>

              <button
                type="button"
                class="sq-chapter-card__btn"
                :class="{ 'sq-chapter-card__btn--outline': !course.enrolled }"
                @click="handleSelect(course)"
              >
                {{ course.state.action }}
              </button>
            </article>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useAuthStore } from "@/stores/auth";
import { useEnrollStore } from "@/stores/enroll";

const router = useRouter();
const authStore = useAuthStore();
const enrollStore = useEnrollStore();

// 진도율 기준: 실습 레벨 (백엔드 PROGRESS_KEYS 와 동일한 순서)
const STEPS = [
  { key: "tier_low", label: "하" },
  { key: "tier_medium", label: "중" },
  { key: "tier_high", label: "상" },
  { key: "tier_impossible", label: "안전" },
];
const STEP_TOTAL = STEPS.length;

// 아이콘은 seed.py 의 과목 아이콘과 동일 (대시보드 응답이 없는 미수강 과목용)
const COURSE_ICONS = {
  "command-injection": "bi-terminal",
  "xss-reflected": "bi-code-slash",
  "xss-dom": "bi-braces",
  "xss-stored": "bi-chat-square-text",
  "sql-injection": "bi-database",
  csrf: "bi-shuffle",
  "file-upload": "bi-file-earmark-arrow-up",
  "sql-injection-blind": "bi-search",
};

const DIFFICULTY_ORDER = ["초급", "중급", "고급"];
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };
function difficultyTone(difficulty) {
  return DIFFICULTY_TONE[difficulty] || "success";
}

const loading = ref(true);
const errorMessage = ref("");
// slug → 대시보드 진도 정보 { completed, total, percent, doneKeys }
const progressBySlug = ref({});

// 진도율에 따른 상태 라벨 · 버튼 문구
function courseState(enrolled, percent) {
  if (!enrolled) return { label: "미수강", tone: "none", action: "수강신청하러 가기" };
  if (percent >= 100) return { label: "완료", tone: "done", action: "복습하기" };
  if (percent > 0) return { label: "학습 중", tone: "progress", action: "이어하기" };
  return { label: "시작 전", tone: "ready", action: "학습 시작" };
}

const courses = computed(() =>
  enrollStore.items.map((item) => {
    const progress = progressBySlug.value[item.id];
    const completed = progress?.completed ?? 0;
    const total = progress?.total ?? STEP_TOTAL;
    const percent = progress?.percent ?? 0;
    return {
      id: item.id,
      title: item.title,
      desc: item.desc,
      difficulty: item.difficulty,
      icon: progress?.icon || COURSE_ICONS[item.id] || "bi-shield-check",
      enrolled: item.enrolled,
      completed,
      total,
      percent,
      doneKeys: progress?.doneKeys ?? [],
      state: courseState(item.enrolled, percent),
    };
  })
);

const groups = computed(() =>
  DIFFICULTY_ORDER.map((difficulty) => ({
    difficulty,
    items: courses.value.filter((c) => c.difficulty === difficulty),
  })).filter((g) => g.items.length)
);

// 전체 진도율: 전체 과목(8개) × 4레벨 기준 — 모두 수강하고 전부 통과해야 100% (대시보드와 같은 계산)
const overall = computed(() => {
  const enrolled = courses.value.filter((c) => c.enrolled);
  const completed = enrolled.reduce((sum, c) => sum + c.completed, 0);
  const total = courses.value.length * STEP_TOTAL;
  return {
    enrolled: enrolled.length,
    completed,
    total,
    percent: total ? Math.round((completed / total) * 100) : 0,
  };
});

function handleSelect(course) {
  if (course.enrolled) {
    router.push(`/dashboard/courses/${course.id}`);
  } else {
    router.push("/enroll");
  }
}

onMounted(async () => {
  try {
    await enrollStore.fetchEnrollments();
    if (!authStore.isAdmin) {
      const { data } = await client.get("/dashboard");
      const map = {};
      (data.courses || []).forEach((c) => {
        map[c.slug] = c;
      });
      progressBySlug.value = map;
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "과목 정보를 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.sq-chapters {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
  font-family: var(--sq-font-family);
  color: var(--sq-text-body);
}

/* 상단 요약 카드 */
.sq-chapters__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-chapters__title {
  margin: 0;
  font-size: 32px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-chapters__subtitle {
  margin: 6px 0 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-chapters__overall {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sq-chapters__overall-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.sq-chapters__overall-label {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-chapters__overall-value {
  font-size: 24px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-color-accent);
}

.sq-chapters__overall-meta {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-chapters__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-chapters__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

/* 난이도 그룹 */
.sq-diff-group__title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0 12px;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
}

.sq-diff-group__meta {
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-text-sub);
}

.sq-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--sq-radius-none);
  font-size: 13px;
  font-weight: 700;
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

/* 과목 카드 */
.sq-chapter-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
  transition: border-color 200ms ease, box-shadow 200ms ease;
}

.sq-chapter-card:hover {
  border-color: var(--sq-color-accent);
  box-shadow: var(--sq-card-shadow-hover);
}

.sq-chapter-card--locked .sq-chapter-card__icon,
.sq-chapter-card--locked .sq-chapter-card__title {
  opacity: 0.6;
}

.sq-chapter-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sq-chapter-card__icon {
  font-size: 22px;
  color: var(--sq-color-accent);
}

.sq-chapter-card__state {
  padding: 3px 10px;
  border-radius: var(--sq-radius-none);
  font-size: 12px;
  font-weight: 700;
}

.sq-chapter-card__state--none {
  background: var(--sq-card-border);
  color: var(--sq-text-sub);
}

.sq-chapter-card__state--ready {
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
}

.sq-chapter-card__state--progress {
  background: var(--sq-color-accent-subtle);
  color: var(--sq-color-accent);
}

.sq-chapter-card__state--done {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-chapter-card__title {
  margin: 0;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-chapter-card__desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: var(--sq-text-sub);
}

.sq-chapter-card__progress-label {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-chapter-card__hint {
  margin: 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

/* 단계 표시 (개념 · 실습 · 퀴즈) */
.sq-step-list {
  display: flex;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-step {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-step--done {
  color: var(--sq-badge-submitted-text);
  font-weight: 600;
}

.sq-chapter-card__btn {
  margin-top: auto;
  padding: 10px 16px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.sq-chapter-card__btn:hover {
  background: var(--sq-color-accent-hover);
  border-color: var(--sq-color-accent-hover);
}

.sq-chapter-card__btn--outline {
  background: transparent;
  color: var(--sq-color-accent);
}

.sq-chapter-card__btn--outline:hover {
  background: var(--sq-color-accent-subtle);
  border-color: var(--sq-color-accent);
}

/* 진행 바 (대시보드와 동일 규격) */
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
  transition: width 300ms ease;
}

@media (prefers-reduced-motion: reduce) {
  .sq-progress-bar__fill,
  .sq-chapter-card {
    transition: none;
  }
}

/* 반응형 */
@media (max-width: 768px) {
  .sq-chapters__header {
    flex-direction: column;
    align-items: stretch;
  }

  .sq-chapters__overall {
    flex-basis: auto;
  }

  .sq-chapters__title {
    font-size: 24px;
  }
}
</style>
