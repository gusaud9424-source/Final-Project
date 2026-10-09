<!--
  SecuQuest — XSS 3종(Reflected/DOM/Stored) 공통 실습 패널 (격리 iframe + flag postMessage 판정)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-xss">
    <form class="sq-xss__form" @submit.prevent="submit">
      <label class="sq-xss__label" for="xss-input">{{ config.label }}</label>
      <div class="sq-xss__row">
        <span v-if="config.prefix" class="sq-xss__prefix">{{ config.prefix }}</span>
        <input
          id="xss-input"
          v-model="payload"
          type="text"
          class="sq-xss__input"
          :placeholder="config.placeholder"
          maxlength="200"
        />
      </div>
      <div class="sq-xss__actions">
        <button type="submit" class="sq-btn" :disabled="running || (isStored && !payload.trim())">
          {{ running ? "처리 중..." : config.submitLabel }}
        </button>
        <button v-if="isStored" type="button" class="sq-btn sq-btn--ghost" :disabled="running" @click="resetBoard">
          방명록 비우기
        </button>
        <slot name="actions" />
      </div>
      <p v-if="error" class="sq-xss__error">{{ error }}</p>
    </form>

    <div v-if="html" class="sq-xss__viewer">
      <p class="sq-xss__caption">
        취약한 페이지 미리보기 — 격리된 iframe(sandbox)이라 SecuQuest 세션·쿠키에는 접근할 수 없습니다.
      </p>
      <PracticeFrame ref="frameRef" class="sq-xss__frame" :html="html" title="취약한 페이지 미리보기" />
      <button type="button" class="sq-btn sq-btn--ghost sq-xss__source-toggle" @click="showSource = !showSource">
        {{ showSource ? "페이지 소스 숨기기" : "페이지 소스 보기" }}
      </button>
      <pre v-if="showSource" class="sq-xss__source">{{ bodySource }}</pre>
    </div>
  </div>
</template>

<script setup>
import PracticeFrame from "@/components/practice/PracticeFrame.vue";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useRewardStore } from "@/stores/reward";

const props = defineProps({
  slug: { type: String, required: true },
  tier: { type: String, required: true },
});
const emit = defineEmits(["result"]);

const CONFIG = {
  "xss-reflected": {
    label: "What's your name?",
    prefix: "",
    placeholder: "이름을 입력하세요",
    submitLabel: "Submit",
  },
  "xss-dom": {
    label: "Please choose a language (default 값):",
    prefix: "?default=",
    placeholder: "English",
    submitLabel: "Submit",
  },
  "xss-stored": {
    label: "Message:",
    prefix: "",
    placeholder: "방명록에 남길 글",
    submitLabel: "Sign Guestbook",
  },
};

const rewardStore = useRewardStore();
const config = computed(() => CONFIG[props.slug]);
const isStored = computed(() => props.slug === "xss-stored");

const payload = ref("");
const html = ref("");
const running = ref(false);
const error = ref("");
const showSource = ref(false);
const frameRef = ref(null);
let verifying = false;

// 감시 스크립트(<head>)는 판정용 장치라 소스 보기에서는 <body>만 보여준다.
const bodySource = computed(() => {
  const match = html.value.match(/<body>([\s\S]*)<\/body>/);
  return match ? match[1] : html.value;
});

async function call(input) {
  const { data } = await client.post(`/courses/${props.slug}/practice/run`, {
    difficulty: props.tier,
    input,
  });
  return data;
}

async function load(action) {
  if (running.value) return;
  running.value = true;
  error.value = "";
  emit("result", null);
  try {
    const data = await call({ action, payload: payload.value });
    html.value = data.output;
    if (action === "post") payload.value = "";
  } catch (err) {
    error.value = getErrorMessage(err, "요청에 실패했습니다.");
  } finally {
    running.value = false;
  }
}

function submit() {
  load(isStored.value ? "post" : "render");
}

function resetBoard() {
  load("reset");
}

async function onMessage(event) {
  // 우리 iframe에서 온 판정 메시지만 처리
  if (!frameRef.value || event.source !== frameRef.value.getWindow()) return;
  if (event.data?.type !== "sq-xss" || typeof event.data.flag !== "string") return;
  if (verifying) return; // alert이 여러 번 호출돼도 한 번만 제출
  verifying = true;
  try {
    const data = await call({ action: "verify", flag: event.data.flag });
    emit("result", data);
    if (data.rewarded) await rewardStore.fetchPending();
  } catch (err) {
    error.value = getErrorMessage(err, "판정 요청에 실패했습니다.");
  }
}

watch(html, () => {
  verifying = false;
});

watch(
  () => props.tier,
  () => {
    html.value = "";
    error.value = "";
    if (isStored.value) load("render");
  }
);

onMounted(() => {
  window.addEventListener("message", onMessage);
  if (isStored.value) load("render");
});

onBeforeUnmount(() => {
  window.removeEventListener("message", onMessage);
});
</script>

<style scoped>
.sq-xss {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border: 1px solid #c9c9c9;
  background: #e7e7e7;
  padding: 16px 18px;
  color: #1a1a1a;
}

.sq-xss__form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.sq-xss__label {
  font-size: 13px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-xss__row {
  width: 100%;
  max-width: 640px;
  display: flex;
  align-items: stretch;
}

.sq-xss__prefix {
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border: 1px solid var(--sq-card-border);
  border-right: none;
  background: var(--sq-color-accent-subtle);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  color: var(--sq-text-sub);
  white-space: nowrap;
}

.sq-xss__input {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 14px;
}

.sq-xss__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sq-xss__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

.sq-xss__viewer {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.sq-xss__caption {
  margin: 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-xss__frame {
  width: 100%;
  height: 220px;
  border: 1px solid var(--sq-card-border);
  background: var(--sq-bg-card);
}

.sq-xss__source {
  width: 100%;
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

.sq-btn {
  display: inline-block;
  padding: 6px 16px;
  border: 1px solid #a33;
  border-radius: 0;
  background: #d33;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.sq-btn:hover:not(:disabled) {
  background: #b22;
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
</style>
