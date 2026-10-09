<!--
  SecuQuest — Stored XSS 실습 (DVWA Guestbook: Name + Message 재현)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-xss">
    <form class="sq-xss__form" @submit.prevent="post">
      <label class="sq-xss__label" for="xss-name">Name:</label>
      <input id="xss-name" v-model="name" type="text" class="sq-xss__input" maxlength="200" />
      <label class="sq-xss__label" for="xss-msg">Message:</label>
      <textarea id="xss-msg" v-model="message" class="sq-xss__textarea" rows="3" maxlength="200"></textarea>
      <div class="sq-xss__actions">
        <button type="submit" class="sq-btn" :disabled="running || !name.trim() || !message.trim()">
          {{ running ? "..." : "Sign Guestbook" }}
        </button>
        <button type="button" class="sq-btn sq-btn--light" :disabled="running" @click="resetBoard">
          방명록 비우기
        </button>
        <slot name="actions" />
      </div>
      <p v-if="error" class="sq-xss__error">{{ error }}</p>
    </form>

    <div v-if="html" class="sq-xss__viewer">
      <p class="sq-xss__caption">
        방명록 미리보기 — 격리된 iframe(sandbox)이라 SecuQuest 세션·쿠키에는 접근할 수 없습니다.
      </p>
      <PracticeFrame ref="frameRef" class="sq-xss__frame" :html="html" title="방명록 미리보기" />
      <button type="button" class="sq-btn sq-btn--light" @click="showSource = !showSource">
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

const rewardStore = useRewardStore();
const name = ref("");
const message = ref("");
const html = ref("");
const running = ref(false);
const error = ref("");
const showSource = ref(false);
const frameRef = ref(null);
let verifying = false;

const bodySource = computed(() => {
  const m = html.value.match(/<body>([\s\S]*)<\/body>/);
  return m ? m[1] : html.value;
});

async function call(input) {
  const { data } = await client.post(`/courses/${props.slug}/practice/run`, {
    difficulty: props.tier,
    input,
  });
  return data;
}

async function load(action, extra = {}) {
  if (running.value) return;
  running.value = true;
  error.value = "";
  emit("result", null);
  try {
    const data = await call({ action, ...extra });
    html.value = data.output;
    if (action === "post") {
      name.value = "";
      message.value = "";
    }
  } catch (err) {
    error.value = getErrorMessage(err, "요청에 실패했습니다.");
  } finally {
    running.value = false;
  }
}

function post() {
  if (!name.value.trim() || !message.value.trim()) return;
  load("post", { name: name.value, message: message.value });
}

function resetBoard() {
  load("reset");
}

async function onMessage(event) {
  if (!frameRef.value || event.source !== frameRef.value.getWindow()) return;
  if (event.data?.type !== "sq-xss" || typeof event.data.flag !== "string") return;
  if (verifying) return;
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
    load("render");
  }
);

onMounted(() => {
  window.addEventListener("message", onMessage);
  load("render");
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
  gap: 8px;
}

.sq-xss__label {
  font-size: 14px;
  font-weight: 700;
}

.sq-xss__input {
  width: 100%;
  max-width: 420px;
  padding: 6px 8px;
  border: 1px solid #999;
  background: #fff;
  font-size: 14px;
}

.sq-xss__textarea {
  width: 100%;
  max-width: 560px;
  padding: 6px 8px;
  border: 1px solid #999;
  background: #fff;
  font-size: 14px;
  resize: vertical;
}

.sq-xss__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.sq-xss__error {
  margin: 0;
  font-size: 14px;
  color: #a3787b;
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
  color: #444;
}

.sq-xss__frame {
  width: 100%;
  height: 220px;
  border: 1px solid #bbb;
  background: #fff;
}

.sq-xss__source {
  width: 100%;
  margin: 0;
  padding: 12px 14px;
  background: #1a1d2a;
  color: #f5f5f5;
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.sq-btn {
  display: inline-block;
  padding: 6px 16px;
  border: 1px solid #a33;
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

.sq-btn--light {
  background: #f3f3f3;
  color: #333;
  border: 1px solid #aaa;
}

.sq-btn--light:hover:not(:disabled) {
  background: #e3e3e3;
}
</style>
