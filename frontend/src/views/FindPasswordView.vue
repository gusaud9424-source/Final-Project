<!--
  SecuQuest — 비밀번호 찾기
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="비밀번호 찾기">
    <div class="sq-auth-form">
      <label class="sq-auth-label" for="username">아이디</label>
      <input id="username" v-model="username" class="sq-auth-input" type="text" required />
    </div>

    <form class="sq-auth-form" @submit.prevent="onSendEmailCode">
      <label class="sq-auth-label" for="email">이메일</label>
      <input id="email" v-model="email" class="sq-auth-input" type="email" required />

      <p v-if="sendEmailError" class="sq-auth-error">{{ sendEmailError }}</p>
      <p v-if="sendEmailMessage" class="sq-auth-notice">{{ sendEmailMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="sendingEmail">
        {{ sendingEmail ? "발송 중..." : "이메일 인증코드 발송" }}
      </button>
    </form>

    <form class="sq-auth-form" @submit.prevent="onSendSmsCode">
      <label class="sq-auth-label" for="phone">휴대폰 번호</label>
      <input id="phone" v-model="phone" class="sq-auth-input" type="tel" required />

      <p v-if="sendSmsError" class="sq-auth-error">{{ sendSmsError }}</p>
      <p v-if="sendSmsMessage" class="sq-auth-notice">{{ sendSmsMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="sendingSms">
        {{ sendingSms ? "발송 중..." : "SMS 인증코드 발송" }}
      </button>
    </form>

    <form class="sq-auth-form" @submit.prevent="onVerifyCodes">
      <label class="sq-auth-label" for="email-code">이메일 인증코드</label>
      <input id="email-code" v-model="emailCode" class="sq-auth-input" type="text" required />

      <label class="sq-auth-label" for="sms-code">SMS 인증코드</label>
      <input id="sms-code" v-model="smsCode" class="sq-auth-input" type="text" required />

      <p v-if="verifyError" class="sq-auth-error">{{ verifyError }}</p>
      <p v-if="verified" class="sq-auth-notice">인증이 완료되었습니다. 새 비밀번호를 설정하세요.</p>

      <button type="submit" class="sq-auth-submit" :disabled="verifying">
        {{ verifying ? "확인 중..." : "인증 확인" }}
      </button>
    </form>

    <form v-if="verified" class="sq-auth-form" @submit.prevent="onConfirm">
      <label class="sq-auth-label" for="new-password">새 비밀번호</label>
      <input
        id="new-password"
        v-model="newPassword"
        class="sq-auth-input"
        type="password"
        minlength="8"
        required
      />

      <label class="sq-auth-label" for="confirm-password">새 비밀번호 확인</label>
      <input
        id="confirm-password"
        v-model="confirmPassword"
        class="sq-auth-input"
        type="password"
        minlength="8"
        required
      />

      <p v-if="confirmError" class="sq-auth-error">{{ confirmError }}</p>
      <p v-if="confirmMessage" class="sq-auth-notice">{{ confirmMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="confirming">
        {{ confirming ? "변경 중..." : "비밀번호 변경" }}
      </button>
    </form>

    <template #links>
      <router-link to="/login">로그인으로 돌아가기</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import AuthCard from "@/components/auth/AuthCard.vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const NEED_USERNAME_MESSAGE = "아이디를 먼저 입력하세요.";

const router = useRouter();

const username = ref("");
const email = ref("");
const phone = ref("");
const emailCode = ref("");
const smsCode = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const sendingEmail = ref(false);
const sendingSms = ref(false);
const verifying = ref(false);
const confirming = ref(false);

const sendEmailMessage = ref("");
const sendEmailError = ref("");
const sendSmsMessage = ref("");
const sendSmsError = ref("");
const verifyError = ref("");
const verified = ref(false);
const confirmError = ref("");
const confirmMessage = ref("");

async function onSendEmailCode() {
  sendEmailMessage.value = "";
  sendEmailError.value = "";
  if (!username.value.trim()) {
    sendEmailError.value = NEED_USERNAME_MESSAGE;
    return;
  }

  sendingEmail.value = true;
  try {
    const { data } = await client.post("/auth/reset-password/send-email-code", {
      username: username.value,
      email: email.value,
    });
    sendEmailMessage.value = data.message;
  } catch (error) {
    sendEmailError.value = getErrorMessage(error, "요청 처리 중 오류가 발생했습니다.");
  } finally {
    sendingEmail.value = false;
  }
}

async function onSendSmsCode() {
  sendSmsMessage.value = "";
  sendSmsError.value = "";
  if (!username.value.trim()) {
    sendSmsError.value = NEED_USERNAME_MESSAGE;
    return;
  }

  sendingSms.value = true;
  try {
    const { data } = await client.post("/auth/reset-password/send-sms-code", {
      username: username.value,
      phone: phone.value,
    });
    sendSmsMessage.value = data.message;
  } catch (error) {
    sendSmsError.value = getErrorMessage(error, "요청 처리 중 오류가 발생했습니다.");
  } finally {
    sendingSms.value = false;
  }
}

async function onVerifyCodes() {
  verifyError.value = "";
  verified.value = false;
  if (!username.value.trim()) {
    verifyError.value = NEED_USERNAME_MESSAGE;
    return;
  }

  verifying.value = true;
  try {
    await client.post("/auth/reset-password/verify-codes", {
      username: username.value,
      email_code: emailCode.value,
      sms_code: smsCode.value,
    });
    verified.value = true;
  } catch (error) {
    verifyError.value = getErrorMessage(error, "인증에 실패했습니다.");
  } finally {
    verifying.value = false;
  }
}

async function onConfirm() {
  confirmError.value = "";
  confirmMessage.value = "";
  if (newPassword.value !== confirmPassword.value) {
    confirmError.value = "새 비밀번호가 일치하지 않습니다.";
    return;
  }

  confirming.value = true;
  try {
    const { data } = await client.post("/auth/reset-password/confirm", {
      username: username.value,
      new_password: newPassword.value,
    });
    confirmMessage.value = data.message;
    setTimeout(() => router.push("/login"), 1500);
  } catch (error) {
    confirmError.value = getErrorMessage(error, "비밀번호 변경에 실패했습니다.");
  } finally {
    confirming.value = false;
  }
}
</script>
