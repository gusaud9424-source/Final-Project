<!--
  SecuQuest — 취약점 실습 (VulnerabilityPage 공통 뼈대 + practice/result/explanation 슬롯)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-chapter">
    <p v-if="loading" class="sq-chapter__status">불러오는 중...</p>

    <div v-else-if="errorMessage" class="sq-chapter__error-panel">
      <p class="sq-chapter__error">{{ errorMessage }}</p>
      <router-link v-if="errorStatus === 403" to="/enroll" class="sq-btn">수강신청하러 가기</router-link>
    </div>

    <VulnerabilityPage
      v-else
      :slug="slug"
      :title="course.title"
      :description="course.description"
      :difficulty="course.difficulty"
    >
      <template #practice>
        <template v-if="practiceSupported">
          <form class="sq-practice__form" @submit.prevent="runPractice">
            <div class="sq-practice__tiers" role="radiogroup" aria-label="난이도">
              <label v-for="tier in TIERS" :key="tier.key" class="sq-practice__tier">
                <input v-model="selectedTier" type="radio" name="tier" :value="tier.key" @change="onTierChange" />
                <span>{{ tier.label }}</span>
              </label>
            </div>

            <label class="sq-practice__label" for="practice-input">{{ TIER_INPUT_LABEL[selectedTier] }}</label>
            <input
              id="practice-input"
              v-model="userInput"
              type="text"
              class="sq-practice__input"
              placeholder="검색어를 입력하세요"
              maxlength="200"
            />

            <div class="sq-practice__actions">
              <button type="submit" class="sq-btn" :disabled="!userInput.trim() || running">
                {{ running ? "실행 중..." : "실행" }}
              </button>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </div>

            <p v-if="runError" class="sq-chapter__error">{{ runError }}</p>
          </form>

          <div v-if="hintsOpen" class="sq-practice__hints">
            <p v-if="hintsLoading" class="sq-chapter__status">힌트 불러오는 중...</p>
            <ol v-else>
              <li v-for="(hint, i) in hints" :key="i">{{ hint }}</li>
            </ol>
          </div>
        </template>
        <p v-else class="sq-chapter__status">이 과목의 실습은 준비 중입니다.</p>
      </template>

      <template #result>
        <template v-if="practiceSupported">
          <p v-if="!lastResult" class="sq-chapter__status">아직 실행 결과가 없습니다.</p>
          <div v-else class="sq-practice__result">
            <span class="sq-badge" :class="lastResult.success ? 'sq-badge--success' : 'sq-badge--danger'">
              {{ lastResult.success ? "성공" : "실패" }}
            </span>
            <pre class="sq-practice__output">{{ lastResult.output }}</pre>
            <p v-if="lastResult.rewarded" class="sq-practice__reward">
              보상 대기 중: XP +{{ lastResult.xp }} · 포인트 +{{ lastResult.points }} — 상단 보물상자에서 받으세요
            </p>
            <p v-else-if="lastResult.success" class="sq-practice__reward sq-practice__reward--muted">
              이미 실습 보상을 받은 과목입니다.
            </p>
          </div>
        </template>
      </template>

      <template #explanation>
        <dl v-if="detail" class="sq-info">
          <dt>공격 예시</dt>
          <dd>{{ detail.exploit }}</dd>
          <dt>방어 방법</dt>
          <dd>{{ detail.defense }}</dd>
        </dl>
      </template>
    </VulnerabilityPage>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import VulnerabilityPage from "@/components/common/VulnerabilityPage.vue";
import { useEnrollStore } from "@/stores/enroll";
import { useRewardStore } from "@/stores/reward";

// 백엔드 PRACTICE_BUILDERS에 등록된 과목만 실습 UI를 노출한다.
const PRACTICE_SUPPORTED_SLUGS = ["command-injection"];
const TIERS = [
  { key: "low", label: "Low" },
  { key: "medium", label: "Medium" },
  { key: "high", label: "High" },
  { key: "impossible", label: "Impossible" },
];
const TIER_INPUT_LABEL = {
  low: "로그 검색어",
  medium: "로그 검색어",
  high: "로그 검색어",
  impossible: "로그 검색어 (영문·숫자·.·_·- 만 허용)",
};

const route = useRoute();
const enrollStore = useEnrollStore();
const rewardStore = useRewardStore();
const slug = route.params.id;

const loading = ref(true);
const errorMessage = ref("");
const errorStatus = ref(null);
const course = ref({});

const practiceSupported = computed(() => PRACTICE_SUPPORTED_SLUGS.includes(slug));
const detail = computed(() => enrollStore.items.find((i) => i.id === slug)?.detail || null);

const selectedTier = ref("low");
const userInput = ref("");
const running = ref(false);
const runError = ref("");
const lastResult = ref(null);

const hintsOpen = ref(false);
const hintsLoading = ref(false);
const hints = ref([]);
const hintsCache = {};

async function loadCourse() {
  const { data } = await client.get(`/courses/${slug}`);
  course.value = data.course;
}

async function fetchHints() {
  if (hintsCache[selectedTier.value]) {
    hints.value = hintsCache[selectedTier.value];
    return;
  }
  hintsLoading.value = true;
  try {
    const { data } = await client.get(`/courses/${slug}/practice/hints`, {
      params: { difficulty: selectedTier.value },
    });
    hintsCache[selectedTier.value] = data.hints;
    hints.value = data.hints;
  } catch {
    hints.value = [];
  } finally {
    hintsLoading.value = false;
  }
}

function toggleHints() {
  hintsOpen.value = !hintsOpen.value;
  if (hintsOpen.value) fetchHints();
}

function onTierChange() {
  if (hintsOpen.value) fetchHints();
}

async function runPractice() {
  if (!userInput.value.trim() || running.value) return;
  running.value = true;
  runError.value = "";
  try {
    const { data } = await client.post(`/courses/${slug}/practice/run`, {
      difficulty: selectedTier.value,
      input: userInput.value,
    });
    lastResult.value = data;
    // 보상은 미수령 상태로 쌓이므로 보물상자 배지만 갱신
    if (data.rewarded) await rewardStore.fetchPending();
  } catch (error) {
    runError.value = getErrorMessage(error, "실행에 실패했습니다.");
  } finally {
    running.value = false;
  }
}

watch(selectedTier, () => {
  lastResult.value = null;
  runError.value = "";
});

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
.sq-chapter {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-chapter__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-chapter__error-panel {
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

.sq-chapter__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

.sq-practice__form {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.sq-practice__tiers {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sq-practice__tier {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--sq-card-border);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.sq-practice__tier:has(input:checked) {
  border-color: var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
}

.sq-practice__label {
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-practice__input {
  width: 100%;
  max-width: 420px;
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 14px;
}

.sq-practice__actions {
  display: flex;
  gap: 8px;
}

.sq-practice__hints {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--sq-card-border);
  background: var(--sq-color-accent-subtle);
  font-size: 13px;
  line-height: 1.6;
}

.sq-practice__hints ol {
  margin: 0;
  padding-left: 18px;
}

.sq-practice__result {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sq-practice__output {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid var(--sq-card-border);
  background: var(--sq-text-main);
  color: var(--sq-color-terminal-fg);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.sq-practice__reward {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-practice__reward--muted {
  color: var(--sq-text-sub);
  font-weight: 400;
}

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

.sq-btn--ghost {
  background: transparent;
  color: var(--sq-color-accent);
  border: 1px solid var(--sq-color-accent);
}

.sq-btn--ghost:hover:not(:disabled) {
  background: var(--sq-color-accent-subtle);
}

.sq-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--sq-radius-none);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.sq-badge--success {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-badge--danger {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}
</style>
