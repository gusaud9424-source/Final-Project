<!--
  SecuQuest — Blind SQL Injection 실습 (DVWA: User ID → exists/missing)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-dvwa">
    <div class="sq-dvwa__box">
      <h3 class="sq-dvwa__title">SQL Injection (Blind)</h3>
      <p class="sq-dvwa__goal">{{ info || "User ID 조회 결과는 보이지 않고 exists/missing 만 응답합니다." }}</p>

      <form class="sq-dvwa__form" @submit.prevent="probe">
        <label class="sq-dvwa__label" for="blind-id">User ID:</label>
        <input id="blind-id" v-model="condition" type="text" name="id" class="sq-dvwa__input" autocomplete="off" maxlength="200" />
        <button type="submit" class="sq-dvwa__submit" :disabled="running || !condition.trim()">
          {{ running ? "..." : "Submit" }}
        </button>
      </form>

      <p v-if="verdict" class="sq-dvwa__verdict" :class="verdictTone">{{ verdict }}</p>

      <div class="sq-dvwa__answer">
        <label class="sq-dvwa__label" for="blind-answer">알아낸 admin 비밀번호 제출:</label>
        <div class="sq-dvwa__answer-row">
          <input id="blind-answer" v-model="guess" type="text" class="sq-dvwa__input" placeholder="추출한 비밀번호" maxlength="64" />
          <button type="button" class="sq-dvwa__submit" :disabled="running || !guess.trim()" @click="submitGuess">제출</button>
        </div>
      </div>
    </div>
    <div class="sq-dvwa__actions"><slot name="actions" /></div>
    <p v-if="error" class="sq-dvwa__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useRewardStore } from "@/stores/reward";

const props = defineProps({
  slug: { type: String, required: true },
  tier: { type: String, required: true },
});
const emit = defineEmits(["result"]);

const rewardStore = useRewardStore();
const condition = ref("");
const guess = ref("");
const verdict = ref("");
const info = ref("");
const error = ref("");
const running = ref(false);

const verdictTone = computed(() =>
  verdict.value.includes("exists") ? "sq-dvwa__verdict--true" : "sq-dvwa__verdict--false"
);

async function call(input) {
  const { data } = await client.post(`/courses/${props.slug}/practice/run`, { difficulty: props.tier, input });
  return data;
}
async function loadInfo() {
  try { info.value = (await call({ action: "info", payload: "" })).output; } catch { info.value = ""; }
}
async function probe() {
  if (running.value || !condition.value.trim()) return;
  running.value = true; error.value = ""; emit("result", null);
  try { verdict.value = (await call({ action: "probe", payload: condition.value })).output; }
  catch (err) { error.value = getErrorMessage(err, "확인에 실패했습니다."); }
  finally { running.value = false; }
}
async function submitGuess() {
  if (running.value || !guess.value.trim()) return;
  running.value = true; error.value = "";
  try {
    const data = await call({ action: "submit", payload: guess.value });
    emit("result", data);
    if (data.rewarded) await rewardStore.fetchPending();
  } catch (err) { error.value = getErrorMessage(err, "제출에 실패했습니다."); }
  finally { running.value = false; }
}

watch(() => props.tier, () => {
  condition.value = ""; guess.value = ""; verdict.value = ""; error.value = "";
  emit("result", null); loadInfo();
});
onMounted(loadInfo);
</script>

<style scoped>
.sq-dvwa { width: 100%; display: flex; flex-direction: column; gap: 12px; }
.sq-dvwa__box { border: 1px solid #c9c9c9; background: #e7e7e7; padding: 16px 18px; color: #1a1a1a; }
.sq-dvwa__title { margin: 0 0 8px; font-size: 18px; font-weight: 700; }
.sq-dvwa__goal { margin: 0 0 12px; font-size: 13px; color: #444; }
.sq-dvwa__form { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.sq-dvwa__label { font-size: 14px; font-weight: 700; }
.sq-dvwa__input { padding: 4px 6px; border: 1px solid #999; background: #fff; font-size: 14px; min-width: 220px; font-family: ui-monospace, SFMono-Regular, monospace; }
.sq-dvwa__submit { padding: 4px 14px; border: 1px solid #a33; background: #d33; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; }
.sq-dvwa__submit:hover:not(:disabled) { background: #b22; }
.sq-dvwa__submit:disabled { opacity: 0.6; cursor: not-allowed; }
.sq-dvwa__verdict { margin: 12px 0 0; padding: 8px 12px; border: 1px solid #bbb; background: #fff; font-size: 14px; font-weight: 700; }
.sq-dvwa__verdict--true { color: #2e7d4f; }
.sq-dvwa__verdict--false { color: #a3303a; }
.sq-dvwa__answer { margin-top: 14px; padding-top: 12px; border-top: 1px dashed #bbb; display: flex; flex-direction: column; gap: 6px; }
.sq-dvwa__answer-row { display: flex; gap: 8px; flex-wrap: wrap; }
.sq-dvwa__actions { display: flex; gap: 8px; }
.sq-dvwa__error { margin: 0; font-size: 14px; color: var(--sq-badge-absent-text); }
.sq-dvwa :deep(.sq-btn--ghost) { background: transparent; color: var(--sq-color-accent); border: 1px solid var(--sq-color-accent); padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; }
</style>
