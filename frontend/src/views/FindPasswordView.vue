<!--
  SecuQuest — 비밀번호 찾기 (이메일 우선 / 휴대폰 우선, 이메일+SMS 2단계 인증)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard
    title="비밀번호 찾기"
    :description="STEP_DESCRIPTIONS[step]"
    :submit-label="step === 'reset' ? '변경' : '다음'"
    :submitting="loading"
    :show-submit="step !== 'done'"
    @submit="onNext"
  >
    <label v-if="step === 'username'" class="sq-auth-field">
      <span class="sq-auth-field__label">아이디</span>
      <input
        v-model="username"
        class="form-control sq-auth-field__input"
        type="text"
        autocomplete="username"
      />
    </label>

    <label v-else-if="step === 'email'" class="sq-auth-field">
      <span class="sq-auth-field__label">가입 시 등록한 이메일</span>
      <input
        v-model="email"
        class="form-control sq-auth-field__input"
        type="email"
        autocomplete="email"
      />
    </label>

    <label v-else-if="step === 'emailCode'" class="sq-auth-field">
      <span class="sq-auth-field__label">이메일 인증코드</span>
      <input
        v-model="emailCode"
        class="form-control sq-auth-field__input"
        type="text"
        inputmode="numeric"
        autocomplete="one-time-code"
      />
    </label>

    <label v-else-if="step === 'phone'" class="sq-auth-field">
      <span class="sq-auth-field__label">가입 시 등록한 휴대폰 번호</span>
      <input
        v-model="phone"
        class="form-control sq-auth-field__input"
        type="tel"
        autocomplete="tel"
      />
    </label>

    <label v-else-if="step === 'smsCode'" class="sq-auth-field">
      <span class="sq-auth-field__label">SMS 인증코드</span>
      <input
        v-model="smsCode"
        class="form-control sq-auth-field__input"
        type="text"
        inputmode="numeric"
        autocomplete="one-time-code"
      />
    </label>

    <template v-else-if="step === 'reset'">
      <label class="sq-auth-field">
        <span class="sq-auth-field__label">새 비밀번호 (8자 이상)</span>
        <input
          v-model="newPassword"
          class="form-control sq-auth-field__input"
          type="password"
          autocomplete="new-password"
        />
      </label>
      <label class="sq-auth-field">
        <span class="sq-auth-field__label">새 비밀번호 확인</span>
        <input
          v-model="confirmPassword"
          class="form-control sq-auth-field__input"
          type="password"
          autocomplete="new-password"
        />
      </label>
    </template>

    <p v-if="noticeMessage" class="sq-find-pw-notice">{{ noticeMessage }}</p>
    <p v-if="errorMessage" class="sq-find-pw-error">{{ errorMessage }}</p>

    <div v-if="step === 'done'" class="sq-find-pw-done">
      <router-link class="sq-auth-link" to="/login">로그인하기</router-link>
    </div>

    <template v-if="canSwitchMethod" #aside>
      <router-link class="sq-auth-link" :to="isPhone ? '/find-password' : '/find-password/phone'">
        {{ isPhone ? "이메일로 찾기" : "휴대폰으로 찾기" }}
      </router-link>
    </template>

    <template #footer>
      <router-link class="sq-auth-link" to="/find-id">아이디 찾기</router-link>
      <router-link class="sq-auth-link" to="/login">로그인으로 돌아가기</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import AuthCard from "@/components/auth/AuthCard.vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const props = defineProps({
  // 라우트 props 로 전달: "email"(/find-password) | "phone"(/find-password/phone)
  method: {
    type: String,
    default: "email",
  },
});

// 인증 채널 순서만 다르고 이메일+SMS 2단계 인증은 두 경로 모두 필수
const STEP_ORDERS = {
  email: ["username", "email", "emailCode", "phone", "smsCode", "reset", "done"],
  phone: ["username", "phone", "smsCode", "email", "emailCode", "reset", "done"],
};

const STEP_DESCRIPTIONS = {
  username: "아이디를 입력해 주세요.",
  email: "가입 시 등록한 이메일을 입력해 주세요.",
  emailCode: "이메일로 받은 인증코드를 입력해 주세요.",
  phone: "가입 시 등록한 휴대폰 번호를 입력해 주세요.",
  smsCode: "SMS로 받은 인증코드를 입력해 주세요.",
  reset: "새 비밀번호를 입력해 주세요.",
  done: "비밀번호가 변경되었습니다.",
};

const step = ref("username");
const username = ref("");
const email = ref("");
const phone = ref("");
const emailCode = ref("");
const smsCode = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const noticeMessage = ref("");
const errorMessage = ref("");

const isPhone = computed(() => props.method === "phone");
const stepOrder = computed(() => STEP_ORDERS[isPhone.value ? "phone" : "email"]);
// 첫 인증코드 발송 전까지만 이메일↔휴대폰 방식 전환 링크 노출
const canSwitchMethod = computed(() => stepOrder.value.indexOf(step.value) <= 1);

// 같은 컴포넌트로 이메일↔휴대폰 라우트 전환 시 입력 상태 초기화
watch(
  () => props.method,
  () => {
    step.value = "username";
    username.value = "";
    email.value = "";
    phone.value = "";
    emailCode.value = "";
    smsCode.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
    noticeMessage.value = "";
    errorMessage.value = "";
  },
);

const handlers = {
  username: checkUsername,
  email: sendEmailCode,
  emailCode: submitEmailCode,
  phone: sendSmsCode,
  smsCode: submitSmsCode,
  reset: confirmReset,
};

function goNext() {
  const order = stepOrder.value;
  step.value = order[order.indexOf(step.value) + 1];
}

// 두 번째 인증코드 단계인지 (두 코드를 모아 verify-codes 호출)
function isLastCodeStep() {
  return stepOrder.value.indexOf(step.value) === stepOrder.value.indexOf("reset") - 1;
}

function onNext() {
  noticeMessage.value = "";
  errorMessage.value = "";
  return handlers[step.value]();
}

// 공통 요청 래퍼: 로딩 표시 + 실패 시 카드 내 에러 표시
async function request(url, body, fallbackMessage) {
  loading.value = true;
  try {
    const { data } = await client.post(url, body);
    return data;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, fallbackMessage);
    return null;
  } finally {
    loading.value = false;
  }
}

function checkUsername() {
  if (!username.value.trim()) {
    errorMessage.value = "아이디를 입력해 주세요.";
    return;
  }
  goNext();
}

async function sendEmailCode() {
  if (!email.value.trim()) {
    errorMessage.value = "이메일을 입력해 주세요.";
    return;
  }
  const data = await request(
    "/auth/reset-password/send-email-code",
    { username: username.value, email: email.value },
    "요청 처리 중 오류가 발생했습니다.",
  );
  if (data) {
    noticeMessage.value = data.message;
    goNext();
  }
}

async function sendSmsCode() {
  if (!phone.value.trim()) {
    errorMessage.value = "휴대폰 번호를 입력해 주세요.";
    return;
  }
  const data = await request(
    "/auth/reset-password/send-sms-code",
    { username: username.value, phone: phone.value },
    "요청 처리 중 오류가 발생했습니다.",
  );
  if (data) {
    noticeMessage.value = data.message;
    goNext();
  }
}

function submitEmailCode() {
  if (!emailCode.value.trim()) {
    errorMessage.value = "이메일 인증코드를 입력해 주세요.";
    return;
  }
  return isLastCodeStep() ? verifyCodes() : goNext();
}

function submitSmsCode() {
  if (!smsCode.value.trim()) {
    errorMessage.value = "SMS 인증코드를 입력해 주세요.";
    return;
  }
  return isLastCodeStep() ? verifyCodes() : goNext();
}

// 백엔드는 두 코드를 한 번에 검증 → 두 번째 코드 입력 시점에 호출
async function verifyCodes() {
  const data = await request(
    "/auth/reset-password/verify-codes",
    { username: username.value, email_code: emailCode.value, sms_code: smsCode.value },
    "인증에 실패했습니다.",
  );
  if (data) {
    goNext();
    return;
  }
  // 어느 코드가 틀렸는지 응답으로 구분 불가 → 두 코드 모두 다시 입력
  emailCode.value = "";
  smsCode.value = "";
  step.value = isPhone.value ? "smsCode" : "emailCode";
}

async function confirmReset() {
  if (newPassword.value.length < 8) {
    errorMessage.value = "새 비밀번호는 8자 이상이어야 합니다.";
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = "새 비밀번호가 일치하지 않습니다.";
    return;
  }
  const data = await request(
    "/auth/reset-password/confirm",
    { username: username.value, new_password: newPassword.value },
    "비밀번호 변경에 실패했습니다.",
  );
  if (data) {
    goNext();
  }
}
</script>

<style scoped>
.sq-find-pw-notice {
  margin: 0;
  font-size: var(--sq-auth-message-size);
  color: var(--sq-auth-text-desc);
}

.sq-find-pw-error {
  margin: 0;
  font-size: var(--sq-auth-message-size);
  color: var(--sq-auth-text-error);
}

.sq-find-pw-done {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sq-auth-field-gap);
}
</style>
