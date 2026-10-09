<!--
  SecuQuest — 1회차 개념 학습 확인 문제 (과목 정보 탭 하단)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <section class="sq-concept">
    <div class="sq-concept__head">
      <h3 class="sq-concept__title"><i class="bi bi-patch-question" aria-hidden="true"></i> 개념 확인 문제</h3>
      <p class="sq-concept__desc">
        위 과목 정보를 읽고 5문제를 풀어 보세요. <strong>3문제 이상</strong> 맞히면 미션 1회차(개념 학습)가 완료되고,
        미션 탭 오른쪽 칸에서 보상을 받을 수 있습니다.
      </p>
    </div>

    <p v-if="completed" class="sq-concept__done">
      <i class="bi bi-check-circle-fill" aria-hidden="true"></i> 개념 학습을 완료했습니다. 미션 탭에서 보상을 확인하세요.
    </p>

    <template v-else>
      <button v-if="!questions.length && !result" type="button" class="sq-btn" :disabled="loading" @click="loadQuestions">
        {{ loading ? "불러오는 중..." : "문제 풀기" }}
      </button>

      <form v-if="questions.length" class="sq-concept__form" @submit.prevent="submit">
        <fieldset v-for="(q, i) in questions" :key="q.id" class="sq-concept__q">
          <legend class="sq-concept__question">{{ i + 1 }}. {{ q.question }}</legend>
          <label
            v-for="(opt, oi) in q.options"
            :key="oi"
            class="sq-concept__option"
            :class="optionClass(q.id, oi)"
          >
            <input v-model="answers[q.id]" type="radio" :name="q.id" :value="oi" :disabled="!!result" />
            <span>{{ opt }}</span>
          </label>
          <p v-if="resultOf(q.id)" class="sq-concept__explain">
            <strong>{{ resultOf(q.id).correct ? "맞았습니다" : "틀렸습니다" }}</strong>
          </p>
        </fieldset>

        <button v-if="!result" type="submit" class="sq-btn" :disabled="!allAnswered || submitting">
          {{ submitting ? "채점 중..." : `제출하기 (${answeredCount}/${questions.length})` }}
        </button>
      </form>

      <div v-if="result" class="sq-concept__result" :class="result.passed ? 'is-pass' : 'is-fail'">
        <p class="sq-concept__score">{{ result.correct }} / {{ result.total }} 정답</p>
        <p v-if="result.passed">통과! 미션 1회차가 완료되었습니다. 미션 탭에서 보상을 받으세요.</p>
        <template v-else>
          <p>{{ result.passScore }}문제 이상 맞혀야 통과합니다. 과목 정보를 다시 읽고 도전해 보세요.</p>
          <button type="button" class="sq-btn sq-btn--ghost" :disabled="loading" @click="loadQuestions">다시 풀기</button>
        </template>
      </div>
    </template>

    <p v-if="notice" class="sq-concept__notice">
      <i class="bi bi-hourglass-split" aria-hidden="true"></i> {{ notice }}
    </p>
    <p v-if="error" class="sq-concept__error">{{ error }}</p>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const props = defineProps({
  slug: { type: String, required: true },
  completed: { type: Boolean, default: false },
});
const emit = defineEmits(["passed"]);

const questions = ref([]);
const answers = ref({});
const result = ref(null);
const loading = ref(false);
const submitting = ref(false);
const error = ref("");
// 문항 미등록(404) 시 안내 문구 — 오류가 아닌 "준비 중" 상태로 표시
const notice = ref("");

const answeredCount = computed(() => questions.value.filter((q) => answers.value[q.id] !== undefined).length);
const allAnswered = computed(() => questions.value.length > 0 && answeredCount.value === questions.value.length);

async function loadQuestions() {
  loading.value = true;
  error.value = "";
  notice.value = "";
  result.value = null;
  answers.value = {};
  try {
    const { data } = await client.get(`/courses/${props.slug}/concept-check`);
    questions.value = data.questions;
  } catch (err) {
    if (err.response?.status === 404) {
      notice.value = "개념 확인 문제를 준비 중입니다. 조금만 기다려 주세요.";
    } else {
      error.value = getErrorMessage(err, "문제를 불러오지 못했습니다.");
    }
  } finally {
    loading.value = false;
  }
}

async function submit() {
  if (!allAnswered.value || submitting.value) return;
  submitting.value = true;
  error.value = "";
  try {
    const { data } = await client.post(`/courses/${props.slug}/concept-check/submit`, { answers: answers.value });
    result.value = data;
    if (data.passed) emit("passed");
  } catch (err) {
    error.value = getErrorMessage(err, "채점하지 못했습니다.");
  } finally {
    submitting.value = false;
  }
}

function resultOf(id) {
  return result.value?.results.find((r) => r.id === id) || null;
}

// 채점 후 내가 고른 보기만 맞으면 초록, 틀리면 빨강 (정답 보기는 공개하지 않음)
function optionClass(id, index) {
  const r = resultOf(id);
  if (!r) return {};
  // 정답 보기는 표시하지 않고, 내가 고른 보기의 맞음/틀림만 표시
  const chosen = answers.value[id] === index;
  return { "is-answer": chosen && r.correct, "is-wrong": chosen && !r.correct };
}
</script>

<style scoped>
.sq-concept {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 8px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
  font-family: var(--sq-font-family);
}

.sq-concept__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-concept__desc {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-concept__done {
  margin: 0;
  font-weight: 700;
  color: var(--sq-badge-submitted-text);
}

.sq-concept__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sq-concept__q {
  margin: 0;
  padding: 14px 16px;
  border: 1px solid var(--sq-card-border);
  background: var(--sq-bg-card);
}

.sq-concept__question {
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-concept__option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  font-size: 14px;
  color: var(--sq-text-main);
  cursor: pointer;
}

.sq-concept__option.is-answer {
  background: var(--sq-badge-submitted-bg);
}

.sq-concept__option.is-wrong {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

.sq-concept__explain {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-concept__result {
  padding: 14px 16px;
  border-left: 4px solid var(--sq-color-accent);
  background: var(--sq-bg-card);
}

.sq-concept__result.is-fail {
  border-left-color: var(--sq-badge-absent-text);
}

.sq-concept__result p {
  margin: 0 0 8px;
  font-size: 14px;
}

.sq-concept__score {
  font-size: 18px !important;
  font-weight: 800;
  color: var(--sq-text-main);
}

.sq-concept__notice {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 10px 14px;
  background: var(--sq-bg-card);
  border-left: 4px solid var(--sq-color-accent);
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-concept__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

.sq-btn {
  align-self: flex-start;
  padding: 10px 18px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.sq-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sq-btn--ghost {
  background: var(--sq-bg-card);
  color: var(--sq-color-accent);
}
</style>
