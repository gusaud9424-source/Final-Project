<!--
  SecuQuest — 방어 퀴즈 세트 모달 (문항 선택 즉시 채점 → 1.5초 강조 후 자동 진행)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <Teleport to="body">
    <div class="sq-quizset-modal" @click.self="handleOverlayClick">
      <div class="sq-quizset-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="sq-quizset-title">
        <div class="sq-quizset-modal__header">
          <h2 id="sq-quizset-title" class="sq-quizset-modal__title">{{ title ? title + " 퀴즈" : "퀴즈" }}</h2>
          <button type="button" class="sq-quizset-modal__close" aria-label="닫기" @click="handleClose">
            <i class="bi bi-x-lg" aria-hidden="true"></i>
          </button>
        </div>

        <p v-if="phase === 'loading'" class="sq-quizset-modal__status">불러오는 중...</p>
        <p v-else-if="phase === 'error'" class="sq-quizset-modal__error">{{ errorMessage }}</p>

        <template v-else-if="phase === 'result'">
          <div class="sq-quizset-result">
            <p class="sq-quizset-result__score">{{ scoreCorrectCount }}/{{ result.total }} 정답 · {{ result.score }}%</p>
            <p
              class="sq-quizset-result__status"
              :class="result.passed ? 'sq-quizset-result__status--pass' : 'sq-quizset-result__status--fail'"
            >
              {{ result.passed ? "통과" : "70% 미만으로 미통과" }}
            </p>
            <p v-if="result.rewarded" class="sq-quizset-result__reward">
              보상 대기 중: {{ result.rewardType === "xp" ? "XP" : "포인트" }} +{{ result.amount }}
              — 상단 보물상자에서 받으세요
            </p>

            <ul class="sq-quizset-result__list">
              <li
                v-for="r in result.results"
                :key="r.questionId"
                :class="r.correct ? 'sq-quizset-result__item--correct' : 'sq-quizset-result__item--wrong'"
              >
                <p class="sq-quizset-result__item-question">{{ questionText(r.questionId) }}</p>
                <p v-if="!r.correct" class="sq-quizset-result__explanation">{{ r.explanation }}</p>
              </li>
            </ul>
          </div>
          <button type="button" class="sq-btn" @click="handleClose">닫기</button>
        </template>

        <template v-else-if="currentQuestion">
          <p class="sq-quizset-progress">{{ currentIndex + 1 }}/{{ questions.length }}</p>
          <p class="sq-quizset-question">{{ currentQuestion.question }}</p>

          <div class="sq-quizset-options">
            <button
              v-for="(option, index) in currentQuestion.options"
              :key="index"
              type="button"
              class="sq-quizset-option"
              :class="optionClass(index)"
              :disabled="answering"
              @click="selectOption(index)"
            >
              {{ option }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const REVEAL_DELAY_MS = 1500;

const props = defineProps({
  slug: { type: String, required: true },
  title: { type: String, default: "" },
});
const emit = defineEmits(["close", "finished"]);

const phase = ref("loading"); // loading | error | question | result
const errorMessage = ref("");

const attemptId = ref(null);
const questions = ref([]);
const currentIndex = ref(0);

const answering = ref(false);
const revealedAnswer = ref(null);
const selectedChoice = ref(null);

const result = ref(null);
let revealTimer = null;

const currentQuestion = computed(() => questions.value[currentIndex.value] || null);
const scoreCorrectCount = computed(() =>
  result.value ? result.value.results.filter((r) => r.correct).length : 0
);

function optionClass(index) {
  if (revealedAnswer.value === null) return "";
  if (index === revealedAnswer.value) return "sq-quizset-option--correct";
  if (index === selectedChoice.value) return "sq-quizset-option--wrong";
  return "";
}

function questionText(questionId) {
  return questions.value.find((q) => q.id === questionId)?.question || "";
}

async function load() {
  phase.value = "loading";
  errorMessage.value = "";
  try {
    const { data } = await client.get(`/courses/${props.slug}/quiz-set`);
    attemptId.value = data.attemptId;
    questions.value = data.questions;
    currentIndex.value = 0;
    phase.value = "question";
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "문제를 불러오지 못했습니다.");
    phase.value = "error";
  }
}

async function selectOption(index) {
  if (answering.value || !currentQuestion.value) return;
  answering.value = true;
  try {
    const { data } = await client.post(`/courses/${props.slug}/quiz-set/answer`, {
      attemptId: attemptId.value,
      questionId: currentQuestion.value.id,
      choice: index,
    });
    selectedChoice.value = index;
    revealedAnswer.value = data.answer;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "채점에 실패했습니다.");
    phase.value = "error";
    answering.value = false;
    return;
  }

  revealTimer = setTimeout(advance, REVEAL_DELAY_MS);
}

async function advance() {
  const isLast = currentIndex.value >= questions.value.length - 1;
  selectedChoice.value = null;
  revealedAnswer.value = null;

  if (isLast) {
    await submitAttempt();
    return;
  }

  currentIndex.value += 1;
  answering.value = false;
}

async function submitAttempt() {
  try {
    const { data } = await client.post(`/courses/${props.slug}/quiz-set/submit`, {
      attemptId: attemptId.value,
    });
    result.value = data;
    phase.value = "result";
    emit("finished", data);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "채점에 실패했습니다.");
    phase.value = "error";
  } finally {
    answering.value = false;
  }
}

function handleOverlayClick() {
  if (phase.value === "question") return;
  emit("close");
}

function handleClose() {
  if (phase.value === "question") {
    if (!window.confirm("진행 중인 퀴즈가 초기화됩니다. 닫을까요?")) return;
  }
  emit("close");
}

onMounted(load);
onUnmounted(() => {
  if (revealTimer) clearTimeout(revealTimer);
});
</script>

<style scoped>
.sq-quizset-modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: color-mix(in srgb, var(--sq-text-main) 40%, transparent);
  font-family: var(--sq-font-family);
  z-index: 1050;
}

.sq-quizset-modal__dialog {
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow-hover);
  max-height: 80vh;
  overflow-y: auto;
}

.sq-quizset-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sq-quizset-modal__title {
  margin: 0;
  font-size: 18px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-quizset-modal__close {
  border: none;
  background: transparent;
  color: var(--sq-text-sub);
  font-size: 16px;
  cursor: pointer;
}

.sq-quizset-modal__status,
.sq-quizset-modal__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-quizset-progress {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-quizset-question {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--sq-text-main);
}

.sq-quizset-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sq-quizset-option {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.sq-quizset-option:hover:not(:disabled) {
  background: var(--sq-color-accent-subtle);
}

.sq-quizset-option:disabled {
  cursor: not-allowed;
}

.sq-quizset-option--correct {
  border-color: var(--sq-badge-submitted-text);
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-text-main);
}

.sq-quizset-option--wrong {
  border-color: var(--sq-badge-absent-text);
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

.sq-quizset-result {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sq-quizset-result__score {
  margin: 0;
  font-size: 20px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-quizset-result__status {
  margin: 0;
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 700;
}

.sq-quizset-result__status--pass {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-quizset-result__status--fail {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

.sq-quizset-result__reward {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-quizset-result__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.sq-quizset-result__list li {
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 13px;
}

.sq-quizset-result__item--wrong {
  background: var(--sq-badge-absent-bg);
}

.sq-quizset-result__item-question {
  margin: 0;
  font-weight: 600;
  color: var(--sq-text-main);
}

.sq-quizset-result__explanation {
  margin: 4px 0 0;
  color: var(--sq-badge-absent-text);
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
  cursor: pointer;
}

.sq-btn:hover {
  background: var(--sq-color-accent-hover);
}
</style>
