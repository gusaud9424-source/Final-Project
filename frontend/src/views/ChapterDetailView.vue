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
          <!-- 레벨 스테퍼: 하 → 중 → 상 → 안전 순서로만 진행 (이전 레벨 통과 시 다음 레벨 열림) -->
          <ol class="sq-tiers" aria-label="실습 레벨">
            <li v-for="(tier, i) in tierList" :key="tier.key" class="sq-tiers__item">
              <button
                type="button"
                class="sq-tiers__step"
                :class="{
                  'is-active': selectedTier === tier.key,
                  'is-cleared': tier.cleared,
                  'is-locked': !tier.unlocked,
                }"
                :disabled="!tier.unlocked"
                :aria-current="selectedTier === tier.key ? 'step' : undefined"
                @click="selectTier(tier.key)"
              >
                <span class="sq-tiers__num">
                  <i v-if="tier.cleared" class="bi bi-check-lg" aria-hidden="true"></i>
                  <i v-else-if="!tier.unlocked" class="bi bi-lock-fill" aria-hidden="true"></i>
                  <template v-else>{{ i + 1 }}</template>
                </span>
                <span class="sq-tiers__label">{{ TIER_META[tier.key].label }} ({{ TIER_META[tier.key].name }})</span>
                <span class="sq-tiers__state">{{ tier.cleared ? "통과" : tier.unlocked ? "진행 가능" : "잠김" }}</span>
              </button>
            </li>
          </ol>

          <div class="sq-tiers__guide">
            <p class="sq-tiers__guide-title">
              {{ TIER_META[selectedTier].label }} 레벨 — {{ TIER_META[selectedTier].summary }}
            </p>
            <p v-if="tierNotice" class="sq-tiers__notice">{{ tierNotice }}</p>
          </div>

          <CsrfPractice
            v-if="isCsrf"
            :key="slug + '-csrf'"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </CsrfPractice>

          <SqlInjectionPractice
            v-else-if="isSql"
            :key="slug + '-sql'"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </SqlInjectionPractice>

          <CmdInjectionPractice
            v-else-if="isCmd"
            :key="slug + '-cmd'"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </CmdInjectionPractice>

          <FileUploadPractice
            v-else-if="isUpload"
            :key="slug + '-upload'"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </FileUploadPractice>

          <BlindSqlPractice
            v-else-if="isBlind"
            :key="slug + '-blind'"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </BlindSqlPractice>

          <StoredXssPractice
            v-else-if="isStored"
            :key="slug + '-stored'"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </StoredXssPractice>

          <XssPractice
            v-else-if="isXss"
            :key="slug"
            :slug="slug"
            :tier="selectedTier"
            @result="onResult"
          >
            <template #actions>
              <button type="button" class="sq-btn sq-btn--ghost" @click="toggleHints">
                {{ hintsOpen ? "힌트 숨기기" : "힌트 보기" }}
              </button>
            </template>
          </XssPractice>

          <form v-else class="sq-practice__form" @submit.prevent="runPractice">
            <label class="sq-practice__label" for="practice-input">{{ inputLabel }}</label>
            <input
              id="practice-input"
              v-model="userInput"
              type="text"
              class="sq-practice__input"
              :placeholder="inputPlaceholder"
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

          <!-- 단계별 힌트: 한 번에 하나씩 펼쳐 스스로 생각할 시간을 준다 -->
          <div v-if="hintsOpen" class="sq-hints">
            <p v-if="hintsLoading" class="sq-chapter__status">힌트 불러오는 중...</p>
            <p v-else-if="!hints.length" class="sq-chapter__status">이 레벨에는 힌트가 없습니다.</p>
            <template v-else>
              <div class="sq-hints__head">
                <span class="sq-hints__title">
                  <i class="bi bi-lightbulb" aria-hidden="true"></i>
                  {{ TIER_META[selectedTier].label }} 레벨 힌트
                </span>
                <span class="sq-hints__count">{{ revealedCount }} / {{ hints.length }}</span>
              </div>
              <div class="sq-hints__bar" aria-hidden="true">
                <span
                  v-for="(hint, i) in hints"
                  :key="i"
                  class="sq-hints__dot"
                  :class="{ 'is-on': i < revealedCount }"
                ></span>
              </div>
              <ol class="sq-hints__list">
                <li v-for="(hint, i) in hints.slice(0, revealedCount)" :key="i" class="sq-hints__item">
                  <span class="sq-hints__step">힌트 {{ i + 1 }}</span>
                  <p class="sq-hints__text">{{ hint }}</p>
                </li>
              </ol>
              <div class="sq-hints__actions">
                <button
                  v-if="revealedCount < hints.length"
                  type="button"
                  class="sq-btn sq-btn--ghost"
                  @click="revealedCount++"
                >
                  다음 힌트 보기 ({{ revealedCount + 1 }}/{{ hints.length }})
                </button>
                <p v-else class="sq-hints__done">모든 힌트를 확인했습니다. 직접 시도해 보세요!</p>
              </div>
            </template>
          </div>
        </template>
        <p v-else class="sq-chapter__status">이 과목의 실습은 준비 중입니다.</p>
      </template>

      <template #result>
        <template v-if="practiceSupported">
          <!-- 통과한 레벨은 다른 레벨로 갔다 와도·새로고침해도 통과 표시를 유지 (서버 기록 기준) -->
          <p v-if="selectedTierCleared" class="sq-practice__cleared">
            ✅ 이 레벨은 통과했습니다
          </p>
          <p v-if="!lastResult && !selectedTierCleared" class="sq-chapter__status">아직 실행 결과가 없습니다.</p>
          <!-- lastResult가 있을 때만 렌더링 (통과 레벨 재선택 시 lastResult=null → v-else면 null.success 오류로 화면 멈춤) -->
          <div v-else-if="lastResult" class="sq-practice__result">
            <span class="sq-badge" :class="lastResult.success ? 'sq-badge--success' : 'sq-badge--danger'">
              {{ lastResult.success ? "성공" : "실패" }}
            </span>
            <pre class="sq-practice__output">{{ lastResult.output }}</pre>
            <p v-if="lastResult.rewarded" class="sq-practice__reward">
              {{ TIER_META[selectedTier].label }} 레벨 클리어 보상:
              <template v-if="lastResult.xp">경험치 +{{ lastResult.xp }}</template>
              <template v-else>포인트 +{{ lastResult.points }}</template>
              — 헤더의 보물상자에서 받으세요
            </p>
            <p v-else-if="lastResult.success" class="sq-practice__reward sq-practice__reward--muted">
              이미 이 레벨의 클리어 보상을 받았습니다.
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
import XssPractice from "@/components/practice/XssPractice.vue";
import BlindSqlPractice from "@/components/practice/BlindSqlPractice.vue";
import FileUploadPractice from "@/components/practice/FileUploadPractice.vue";
import CmdInjectionPractice from "@/components/practice/CmdInjectionPractice.vue";
import SqlInjectionPractice from "@/components/practice/SqlInjectionPractice.vue";
import StoredXssPractice from "@/components/practice/StoredXssPractice.vue";
import CsrfPractice from "@/components/practice/CsrfPractice.vue";
import { useEnrollStore } from "@/stores/enroll";
import { TIER_META } from "@/content/tierGuides";
import { useRewardStore } from "@/stores/reward";

// 백엔드 PRACTICE_BUILDERS에 등록된 과목만 실습 UI를 노출한다.
const PRACTICE_SUPPORTED_SLUGS = ["command-injection", "xss-reflected", "xss-dom", "xss-stored", "sql-injection", "sql-injection-blind", "file-upload", "csrf"];
const XSS_SLUGS = ["xss-reflected", "xss-dom", "xss-stored"];
// 피드백 반영: 하 → 중 → 상 순서로 학습, 마지막은 방어 코드가 적용된 "안전" 단계
// 레벨 잠금·통과 상태는 서버(/practice/tiers)가 기준이며, 서버에서도 순서를 강제한다.
const TIER_ORDER = ["low", "medium", "high", "impossible"];
const INPUT_LABELS = {
  "command-injection": {
    low: "로그 검색어",
    medium: "로그 검색어",
    high: "로그 검색어",
    impossible: "로그 검색어 (영문·숫자·.·_·- 만 허용)",
  },
  "sql-injection": {
    low: "조회할 사용자명",
    medium: "조회할 사용자명",
    high: "조회할 사용자명",
    impossible: "조회할 사용자명 (파라미터 바인딩 적용)",
  },
};
const INPUT_PLACEHOLDERS = {
  "command-injection": "검색어를 입력하세요",
  "sql-injection": "예: guest",
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
const isStored = slug === "xss-stored";
const isXss = XSS_SLUGS.includes(slug) && !isStored;
const isBlind = slug === "sql-injection-blind";
const isUpload = slug === "file-upload";
const isCmd = slug === "command-injection";
const isSql = slug === "sql-injection";
const isCsrf = slug === "csrf";
const inputLabel = computed(() => (INPUT_LABELS[slug] || {})[selectedTier.value] || "입력값");
const inputPlaceholder = INPUT_PLACEHOLDERS[slug] || "값을 입력하세요";
const detail = computed(() => enrollStore.items.find((i) => i.id === slug)?.detail || null);

const selectedTier = ref("low");
// 서버 응답 전 기본값: 하만 열림
const tierList = ref(TIER_ORDER.map((key, i) => ({ key, unlocked: i === 0, cleared: false })));
const tierNotice = ref("");
// 현재 선택한 레벨의 통과 여부 (서버의 tier 상태 기준)
const selectedTierCleared = computed(
  () => !!tierList.value.find((t) => t.key === selectedTier.value)?.cleared
);
const userInput = ref("");
const running = ref(false);
const runError = ref("");
const lastResult = ref(null);

const hintsOpen = ref(false);
const hintsLoading = ref(false);
const hints = ref([]);
const hintsCache = {};
// 펼친 힌트 개수 (힌트를 열면 1개부터, 레벨을 바꾸면 다시 1개부터)
const revealedCount = ref(1);

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
  if (hintsOpen.value) {
    revealedCount.value = 1;
    fetchHints();
  }
}

function selectTier(key) {
  const tier = tierList.value.find((t) => t.key === key);
  if (!tier?.unlocked || selectedTier.value === key) return;
  selectedTier.value = key;
  tierNotice.value = "";
  revealedCount.value = 1;
  if (hintsOpen.value) fetchHints();
}

// 아직 통과하지 않은 첫 번째 열린 레벨 (모두 통과했으면 마지막 레벨)
function firstOpenTier(list) {
  const next = list.find((t) => t.unlocked && !t.cleared);
  return next ? next.key : list[list.length - 1].key;
}

async function loadTiers() {
  try {
    const { data } = await client.get(`/courses/${slug}/practice/tiers`);
    tierList.value = data.tiers;
    selectedTier.value = firstOpenTier(data.tiers);
  } catch {
    // 실패 시 기본값(하만 열림) 유지
  }
}

// 각 실습 컴포넌트의 실행 결과 처리: 결과 표시 + 레벨 상태 갱신
function onResult(data) {
  lastResult.value = data;
  if (!data?.tiers) return;
  const wasCleared = tierList.value.find((t) => t.key === selectedTier.value)?.cleared;
  tierList.value = data.tiers;
  if (data.tierCleared && !wasCleared) {
    const index = TIER_ORDER.indexOf(selectedTier.value);
    const nextKey = TIER_ORDER[index + 1];
    tierNotice.value = nextKey
      ? `${TIER_META[selectedTier.value].label} 레벨 통과! 이제 ${TIER_META[nextKey].label} 레벨이 열렸습니다.`
      : "모든 레벨을 마쳤습니다. 안전 레벨의 방어 원리를 과목 정보 탭에서 다시 정리해 보세요.";
  }
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
    onResult(data);
    // 보상은 미수령 상태로 쌓이고 헤더 보물상자에서 수령
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
    if (practiceSupported.value) await loadTiers();
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

/* 레벨 스테퍼 (하 → 중 → 상 → 안전) */
.sq-tiers {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 0 0 12px;
  padding: 0;
  list-style: none;
}

.sq-tiers__step {
  display: flex;
  width: 100%;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-family: var(--sq-font-family);
  text-align: left;
  cursor: pointer;
}

.sq-tiers__step.is-active {
  border-color: var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
}

.sq-tiers__step.is-locked {
  color: var(--sq-text-sub);
  cursor: not-allowed;
  opacity: 0.6;
}

.sq-tiers__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--sq-card-border);
  color: var(--sq-text-sub);
  font-size: 13px;
  font-weight: 700;
}

.sq-tiers__step.is-active .sq-tiers__num {
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
}

.sq-tiers__step.is-cleared .sq-tiers__num {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-tiers__label {
  font-size: 14px;
  font-weight: 700;
}

.sq-tiers__state {
  font-size: 12px;
  color: var(--sq-text-sub);
}

.sq-tiers__guide {
  margin: 0 0 12px;
  padding: 12px 14px;
  border-left: 3px solid var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
}

.sq-tiers__guide-title {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-main);
}

.sq-tiers__notice {
  margin: 6px 0 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

@media (max-width: 640px) {
  .sq-tiers {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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

/* 단계별 힌트 */
.sq-hints {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--sq-card-border);
  border-left: 3px solid var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
}

.sq-hints__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sq-hints__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-hints__count {
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-hints__bar {
  display: flex;
  gap: 4px;
}

.sq-hints__dot {
  flex: 1;
  height: 4px;
  background: var(--sq-card-border);
}

.sq-hints__dot.is-on {
  background: var(--sq-color-accent);
}

.sq-hints__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-hints__item {
  padding: 10px 12px;
  background: var(--sq-bg-card);
  border: 1px solid var(--sq-card-border);
}

.sq-hints__step {
  display: inline-block;
  margin-bottom: 4px;
  padding: 1px 8px;
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 12px;
  font-weight: 700;
}

.sq-hints__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--sq-text-main);
  white-space: pre-wrap;
}

.sq-hints__done {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-practice__cleared {
  margin: 0 0 10px;
  padding: 10px 14px;
  border-left: 4px solid var(--sq-badge-submitted-text);
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-text-main);
  font-size: 14px;
  font-weight: 700;
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
