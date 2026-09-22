<!--
  SecuQuest — 아이디 찾기
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="아이디 찾기">
    <form class="sq-auth-form" @submit.prevent="onSendCode">
      <label class="sq-auth-label" for="email">이메일</label>
      <input id="email" v-model="email" class="sq-auth-input" type="email" required />

      <p v-if="sendError" class="sq-auth-error">{{ sendError }}</p>
      <p v-if="sendMessage" class="sq-auth-notice">{{ sendMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="sending">
        {{ sending ? "발송 중..." : "인증코드 발송" }}
      </button>
    </form>

    <form class="sq-auth-form" @submit.prevent="onVerify">
      <label class="sq-auth-label" for="code">인증코드</label>
      <input id="code" v-model="code" class="sq-auth-input" type="text" required />

      <p v-if="errorMessage" class="sq-auth-error">{{ errorMessage }}</p>
      <p v-if="foundUsername" class="sq-auth-notice">아이디: <strong>{{ foundUsername }}</strong></p>

      <button type="submit" class="sq-auth-submit" :disabled="verifying">
        {{ verifying ? "확인 중..." : "확인" }}
      </button>
    </form>

    <template #links>
      <router-link to="/login">로그인으로 돌아가기</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from "vue";
import AuthCard from "@/components/auth/AuthCard.vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const email = ref("");
const code = ref("");
const sending = ref(false);
const verifying = ref(false);
const sendMessage = ref("");
const sendError = ref("");
const errorMessage = ref("");
const foundUsername = ref("");

async function onSendCode() {
  sending.value = true;
  sendMessage.value = "";
  sendError.value = "";
  try {
    const { data } = await client.post("/auth/find-id/send-code", { email: email.value });
    sendMessage.value = data.message;
  } catch (error) {
    sendError.value = getErrorMessage(error, "요청 처리 중 오류가 발생했습니다.");
  } finally {
    sending.value = false;
  }
}

async function onVerify() {
  verifying.value = true;
  errorMessage.value = "";
  foundUsername.value = "";
  try {
    const { data } = await client.post("/auth/find-id/verify", {
      email: email.value,
      code: code.value,
    });
    foundUsername.value = data.username;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "인증에 실패했습니다.");
  } finally {
    verifying.value = false;
  }
}
</script>
