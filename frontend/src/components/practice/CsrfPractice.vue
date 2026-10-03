<!--
  SecuQuest — CSRF 실습 (DVWA 비밀번호 변경 + 외부 위조 요청 시뮬레이션)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-dvwa">
    <div class="sq-dvwa__box">
      <h3 class="sq-dvwa__title">CSRF</h3>
      <p class="sq-dvwa__goal">{{ info }}</p>

      <p class="sq-dvwa__attacker">🕸️ 외부 공격 사이트(evil.example)에서 보내는 위조 요청</p>
      <form class="sq-dvwa__form" @submit.prevent="attack">
        <label class="sq-dvwa__label" for="pw-new">New password:</label>
        <input id="pw-new" v-model="pwNew" type="text" class="sq-dvwa__input" maxlength="64" />
        <label class="sq-dvwa__label" for="pw-conf">Confirm new password:</label>
        <input id="pw-conf" v-model="pwConf" type="text" class="sq-dvwa__input" maxlength="64" />

        <template v-if="tier === 'medium'">
          <label class="sq-dvwa__label" for="ref">Referer 헤더 (위조):</label>
          <input id="ref" v-model="referer" type="text" class="sq-dvwa__input" placeholder="http://evil.example/attack" />
        </template>

        <template v-if="tier === 'high' || tier === 'impossible'">
          <label class="sq-dvwa__label" for="tok">user_token (유출한 값):</label>
          <input id="tok" v-model="token" type="text" class="sq-dvwa__input" placeholder="유출한 토큰" />
          <button type="button" class="sq-dvwa__light" @click="leakToken">토큰 유출(XSS 시뮬)</button>
        </template>

        <template v-if="tier === 'impossible'">
          <label class="sq-dvwa__label" for="cur">현재 비밀번호(공격자가 알 수 없음):</label>
          <input id="cur" v-model="current" type="text" class="sq-dvwa__input" />
        </template>

        <div class="sq-dvwa__actions-row">
          <button type="submit" class="sq-dvwa__submit" :disabled="running || !pwNew.trim() || !pwConf.trim()">
            {{ running ? "..." : "위조 요청 전송" }}
          </button>
          <button type="button" class="sq-dvwa__light" :disabled="running" @click="reset">초기화</button>
        </div>
      </form>

      <pre v-if="output" class="sq-dvwa__pre">{{ output }}</pre>
    </div>
    <div class="sq-dvwa__actions"><slot name="actions" /></div>
    <p v-if="error" class="sq-dvwa__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useRewardStore } from "@/stores/reward";

const props = defineProps({
  slug: { type: String, required: true },
  tier: { type: String, required: true },
});
const emit = defineEmits(["result"]);

const rewardStore = useRewardStore();
const pwNew = ref("hacked");
const pwConf = ref("hacked");
const referer = ref("");
const token = ref("");
const current = ref("");
const info = ref("");
const output = ref("");
const error = ref("");
const running = ref(false);

async function call(input) {
  const { data } = await client.post(`/courses/${props.slug}/practice/run`, { difficulty: props.tier, input });
  return data;
}
async function loadInfo() {
  try { info.value = (await call({ action: "info" })).output; } catch { info.value = ""; }
}
async function leakToken() {
  try { token.value = (await call({ action: "leak_token" })).output.replace(/.*user_token:\s*/, ""); } catch {}
}
async function attack() {
  if (running.value) return;
  running.value = true; error.value = ""; emit("result", null);
  try {
    const data = await call({
      action: "attack",
      password_new: pwNew.value,
      password_conf: pwConf.value,
      referer: referer.value,
      user_token: token.value,
      password_current: current.value,
    });
    output.value = data.output;
    emit("result", data);
    if (data.rewarded) await rewardStore.fetchPending();
    loadInfo();
  } catch (err) { error.value = getErrorMessage(err, "요청에 실패했습니다."); }
  finally { running.value = false; }
}
async function reset() {
  try { await call({ action: "reset" }); output.value = ""; emit("result", null); loadInfo(); } catch {}
}

watch(() => props.tier, () => {
  output.value = ""; error.value = ""; referer.value = ""; token.value = ""; current.value = "";
  emit("result", null); loadInfo();
});
onMounted(loadInfo);
</script>

<style scoped>
.sq-dvwa { width: 100%; display: flex; flex-direction: column; gap: 12px; }
.sq-dvwa__box { border: 1px solid #c9c9c9; background: #e7e7e7; padding: 16px 18px; color: #1a1a1a; }
.sq-dvwa__title { margin: 0 0 8px; font-size: 18px; font-weight: 700; }
.sq-dvwa__goal { margin: 0 0 10px; font-size: 13px; color: #444; }
.sq-dvwa__attacker { margin: 0 0 8px; font-size: 13px; font-weight: 700; color: #a3303a; }
.sq-dvwa__form { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
.sq-dvwa__label { font-size: 14px; }
.sq-dvwa__input { width: 100%; max-width: 360px; padding: 4px 6px; border: 1px solid #999; background: #fff; font-size: 14px; }
.sq-dvwa__actions-row { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.sq-dvwa__submit { padding: 4px 14px; border: 1px solid #a33; background: #d33; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; }
.sq-dvwa__submit:hover:not(:disabled) { background: #b22; }
.sq-dvwa__submit:disabled { opacity: 0.6; cursor: not-allowed; }
.sq-dvwa__light { padding: 4px 12px; border: 1px solid #aaa; background: #f3f3f3; color: #333; font-size: 13px; cursor: pointer; }
.sq-dvwa__light:hover:not(:disabled) { background: #e3e3e3; }
.sq-dvwa__pre { margin: 12px 0 0; padding: 10px 12px; background: #fff; border: 1px solid #bbb; font-size: 13px; font-family: ui-monospace, SFMono-Regular, monospace; white-space: pre-wrap; word-break: break-all; color: #111; }
.sq-dvwa__actions { display: flex; gap: 8px; }
.sq-dvwa__error { margin: 0; font-size: 14px; color: var(--sq-badge-absent-text); }
.sq-dvwa :deep(.sq-btn--ghost) { background: transparent; color: var(--sq-color-accent); border: 1px solid var(--sq-color-accent); padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; }
</style>
