<!--
  SecuQuest — File Upload 실습 (DVWA Upload 재현)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-dvwa">
    <div class="sq-dvwa__box">
      <h3 class="sq-dvwa__title">File Upload</h3>
      <p class="sq-dvwa__sub">Choose an image to upload:</p>
      <form class="sq-dvwa__form" @submit.prevent="upload">
        <label class="sq-dvwa__label" for="up-name">파일명</label>
        <input id="up-name" v-model="filename" type="text" class="sq-dvwa__input" placeholder="예: shell.sh" maxlength="100" />
        <label class="sq-dvwa__label" for="up-content">파일 내용</label>
        <textarea id="up-content" v-model="content" class="sq-dvwa__textarea" rows="4" placeholder="예: cat /tmp/flag.txt" maxlength="2000"></textarea>
        <p class="sq-dvwa__mime">전송될 Content-Type: <code>{{ mimetype }}</code></p>
        <button type="submit" class="sq-dvwa__submit" :disabled="running || !filename.trim() || !content.trim()">
          {{ running ? "..." : "Upload" }}
        </button>
      </form>
      <p class="sq-dvwa__note">
        ※ Medium은 Content-Type(MIME)만 검사합니다. DevTools/Burp로 요청의 <code>mimetype</code>을
        <code>image/jpeg</code>로 위조하면 .sh/.php도 통과합니다.
      </p>
      <pre v-if="output" class="sq-dvwa__pre">{{ output }}</pre>
    </div>
    <div class="sq-dvwa__actions"><slot name="actions" /></div>
    <p v-if="error" class="sq-dvwa__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useRewardStore } from "@/stores/reward";

const props = defineProps({
  slug: { type: String, required: true },
  tier: { type: String, required: true },
});
const emit = defineEmits(["result"]);

const rewardStore = useRewardStore();
const filename = ref("");
const content = ref("");
const running = ref(false);
const error = ref("");

const MIME_BY_EXT = {
  jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", gif: "image/gif",
  sh: "application/x-sh", php: "application/x-httpd-php", txt: "text/plain",
};
// 브라우저가 파일 확장자로 Content-Type을 정하는 동작을 모사
const mimetype = computed(() => {
  const ext = filename.value.includes(".") ? filename.value.split(".").pop().toLowerCase() : "";
  return MIME_BY_EXT[ext] || "application/octet-stream";
});

async function upload() {
  if (running.value || !filename.value.trim() || !content.value.trim()) return;
  running.value = true;
  error.value = "";
  emit("result", null);
  try {
    const { data } = await client.post(`/courses/${props.slug}/practice/run`, {
      difficulty: props.tier,
      input: { filename: filename.value, content: content.value, mimetype: mimetype.value },
    });
    output.value = data.output;
    emit("result", data);
    if (data.rewarded) await rewardStore.fetchPending();
  } catch (err) {
    error.value = getErrorMessage(err, "업로드에 실패했습니다.");
  } finally {
    running.value = false;
  }
}

const output = ref("");

watch(() => props.tier, () => {
  output.value = "";
  error.value = "";
  emit("result", null);
});
</script>

<style scoped>
.sq-dvwa { width: 100%; display: flex; flex-direction: column; gap: 12px; }
.sq-dvwa__box { border: 1px solid #c9c9c9; background: #e7e7e7; padding: 16px 18px; color: #1a1a1a; }
.sq-dvwa__title { margin: 0 0 4px; font-size: 18px; font-weight: 700; }
.sq-dvwa__sub { margin: 0 0 12px; font-size: 15px; font-weight: 700; color: #333; }
.sq-dvwa__form { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
.sq-dvwa__label { font-size: 14px; font-weight: 700; }
.sq-dvwa__input { width: 100%; max-width: 420px; padding: 6px 8px; border: 1px solid #999; background: #fff; font-size: 14px; font-family: ui-monospace, SFMono-Regular, monospace; }
.sq-dvwa__textarea { width: 100%; max-width: 560px; padding: 6px 8px; border: 1px solid #999; background: #fff; font-size: 14px; font-family: ui-monospace, SFMono-Regular, monospace; resize: vertical; }
.sq-dvwa__mime { margin: 4px 0; font-size: 13px; color: #444; }
.sq-dvwa__mime code, .sq-dvwa__note code { background: #fff; border: 1px solid #ccc; padding: 0 4px; }
.sq-dvwa__submit { margin-top: 4px; padding: 4px 14px; border: 1px solid #a33; background: #d33; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; }
.sq-dvwa__submit:hover:not(:disabled) { background: #b22; }
.sq-dvwa__submit:disabled { opacity: 0.6; cursor: not-allowed; }
.sq-dvwa__note { margin: 10px 0 0; font-size: 13px; color: #444; }
.sq-dvwa__pre { margin: 12px 0 0; padding: 10px 12px; background: #fff; border: 1px solid #bbb; font-size: 13px; font-family: ui-monospace, SFMono-Regular, monospace; white-space: pre-wrap; word-break: break-all; color: #111; }
.sq-dvwa__actions { display: flex; gap: 8px; }
.sq-dvwa__error { margin: 0; font-size: 14px; color: var(--sq-badge-absent-text); }
.sq-dvwa :deep(.sq-btn--ghost) { background: transparent; color: var(--sq-color-accent); border: 1px solid var(--sq-color-accent); padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; }
</style>
