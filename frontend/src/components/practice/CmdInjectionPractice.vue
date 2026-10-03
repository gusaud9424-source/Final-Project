<!--
  SecuQuest — Command Injection 실습 (DVWA "Ping a device" 재현)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-dvwa">
    <div class="sq-dvwa__box">
      <h3 class="sq-dvwa__title">Command Injection</h3>
      <p class="sq-dvwa__sub">Ping a device</p>
      <form class="sq-dvwa__form" @submit.prevent="submit">
        <label class="sq-dvwa__label" for="ci-ip">Enter an IP address:</label>
        <input
          id="ci-ip"
          v-model="ip"
          type="text"
          name="ip"
          class="sq-dvwa__input"
          autocomplete="off"
          maxlength="200"
        />
        <button type="submit" name="Submit" class="sq-dvwa__submit" :disabled="running || !ip.trim()">
          {{ running ? "..." : "Submit" }}
        </button>
      </form>
      <pre v-if="output" class="sq-dvwa__pre">{{ output }}</pre>
    </div>
    <div class="sq-dvwa__actions">
      <slot name="actions" />
    </div>
    <p v-if="error" class="sq-dvwa__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useRewardStore } from "@/stores/reward";

const props = defineProps({
  slug: { type: String, required: true },
  tier: { type: String, required: true },
});
const emit = defineEmits(["result"]);

const rewardStore = useRewardStore();
const ip = ref("");
const output = ref("");
const running = ref(false);
const error = ref("");

async function submit() {
  if (running.value || !ip.value.trim()) return;
  running.value = true;
  error.value = "";
  emit("result", null);
  try {
    const { data } = await client.post(`/courses/${props.slug}/practice/run`, {
      difficulty: props.tier,
      input: ip.value,
    });
    output.value = data.output;
    emit("result", data);
    if (data.rewarded) await rewardStore.fetchPending();
  } catch (err) {
    error.value = getErrorMessage(err, "실행에 실패했습니다.");
  } finally {
    running.value = false;
  }
}

watch(
  () => props.tier,
  () => {
    output.value = "";
    error.value = "";
    emit("result", null);
  }
);
</script>

<style scoped>
/* DVWA 특유의 회색 박스 + 빨간 Submit 버튼 느낌을 재현 (실습 화면 한정) */
.sq-dvwa {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sq-dvwa__box {
  border: 1px solid #c9c9c9;
  background: #e7e7e7;
  padding: 16px 18px;
  color: #1a1a1a;
}

.sq-dvwa__title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
}

.sq-dvwa__sub {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: #333;
}

.sq-dvwa__form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.sq-dvwa__label {
  font-size: 14px;
}

.sq-dvwa__input {
  padding: 4px 6px;
  border: 1px solid #999;
  background: #fff;
  font-size: 14px;
  min-width: 200px;
}

.sq-dvwa__submit {
  padding: 4px 14px;
  border: 1px solid #a33;
  background: #d33;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.sq-dvwa__submit:hover:not(:disabled) {
  background: #b22;
}

.sq-dvwa__submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-dvwa__pre {
  margin: 12px 0 0;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #bbb;
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  white-space: pre-wrap;
  word-break: break-all;
  color: #111;
}

.sq-dvwa__actions {
  display: flex;
  gap: 8px;
}

.sq-dvwa__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

.sq-dvwa :deep(.sq-btn--ghost) {
  background: transparent;
  color: var(--sq-color-accent);
  border: 1px solid var(--sq-color-accent);
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
</style>
