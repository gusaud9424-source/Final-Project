<!--
  SecuQuest — 비밀번호 찾기 (이메일 / 휴대폰) : 아이디 찾기와 같은 구성
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="비밀번호 찾기">
    <!-- 인증 방식 탭: 주소(/find-password, /find-password/phone)로 구분 -->
    <div class="sq-auth-tabs" role="tablist">
      <router-link
        to="/find-password"
        replace
        role="tab"
        class="sq-auth-tab"
        :class="{ 'sq-auth-tab--active': !isPhone }"
        :aria-selected="!isPhone"
      >
        이메일로 찾기
      </router-link>
      <router-link
        to="/find-password/phone"
        replace
        role="tab"
        class="sq-auth-tab"
        :class="{ 'sq-auth-tab--active': isPhone }"
        :aria-selected="isPhone"
      >
        휴대폰으로 찾기
      </router-link>
    </div>

    <!-- 1단계: 아이디 + (이메일 | 휴대폰) → 인증코드 발송 -->
    <form class="sq-auth-form" @submit.prevent="onSendCode">
      <label class="sq-auth-label" for="username">아이디</label>
      <input id="username" v-model="username" class="sq-auth-input" type="text" autocomplete="username" required />

      <template v-if="isPhone">
        <label class="sq-auth-label" for="phone">휴대폰 번호</label>
        <input
          id="phone"
          v-model="phone"
          class="sq-auth-input"
          type="tel"
          inputmode="numeric"
          autocomplete="tel"
          placeholder="01012345678"
          required
        />
        <span class="sq-auth-hint">가입한 아이디·휴대폰 번호로 SMS 인증코드를 보냅니다.</span>
      </template>
      <template v-else>
        <label class="sq-auth-label" for="email">이메일</label>
        <input id="email" v-model="email" class="sq-auth-input" type="email" autocomplete="email" required />
        <span class="sq-auth-hint">가입한 아이디·이메일로 인증코드를 보냅니다.</span>
      </template>

      <p v-if="sendError" class="sq-auth-error">{{ sendError }}</p>
      <p v-if="sendMessage" class="sq-auth-notice">{{ sendMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="sending">
        {{ sending ? "발송 중..." : isPhone ? "SMS 인증코드 발송" : "이메일 인증코드 발송" }}
      </button>
    </form>

    <!-- 2단계: 인증코드 확인 -->
    <form class="sq-auth-form" @submit.prevent="onVerify">
      <label class="sq-auth-label" for="code">인증코드</label>
      <input id="code" v-model="code" class="sq-auth-input" type="text" inputmode="numeric" required />

      <p v-if="verifyError" class="sq-auth-error">{{ verifyError }}</p>
      <p v-if="verified" class="sq-auth-result">인증이 완료되었습니다. 아래에서 새 비밀번호를 설정하세요.</p>

      <button type="submit" class="sq-auth-submit" :disabled="verifying || verified">
        {{ verifying ? "확인 중..." : verified ? "인증 완료" : "확인" }}
      </button>
    </form>

    <!-- 3단계: 인증 후에만 새 비밀번호 입력 -->
    <form v-if="verified" class="sq-auth-form" @submit.prevent="onConfirm">
      <label class="sq-auth-label" for="new-password">새 비밀번호</label>
      <input
        id="new-password"
        v-model="newPassword"
        class="sq-auth-input"
        type="password"
        autocomplete="new-password"
        maxlength="64"
        required
      />
      <span class="sq-auth-hint">8~64자, 영문과 숫자를 모두 포함</span>

      <label class="sq-auth-label" for="confirm-password">새 비밀번호 확인</label>
      <input
        id="confirm-password"
        v-model="confirmPassword"
        class="sq-auth-input"
        type="password"
        autocomplete="new-password"
        maxlength="64"
        required
      />

      <p v-if="confirmError" class="sq-auth-error">{{ confirmError }}</p>
      <p v-if="confirmMessage" class="sq-auth-result">{{ confirmMessage }} 잠시 후 로그인 화면으로 이동합니다.</p>

      <button type="submit" class="sq-auth-submit" :disabled="confirming || !!confirmMessage">
        {{ confirming ? "변경 중..." : "비밀번호 변경" }}
      </button>
    </form>

    <template #links>
      <router-link to="/login">로그인</router-link>
      <span aria-hidden="true">·</span>
      <router-link to="/find-id">아이디 찾기</router-link>
      <span aria-hidden="true">·</span>
      <router-link to="/signup">회원가입</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AuthCard from "@/components/auth/AuthCard.vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

// 라우터에서 /find-password/phone 이면 method="phone" 이 넘어옴
const props = defineProps({
  method: { type: String, default: "email" },
});
const isPhone = computed(() => props.method === "phone");

const router = useRouter();

const username = ref("");
const email = ref("");
const phone = ref("");
const code = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const sending = ref(false);
const verifying = ref(false);
const confirming = ref(false);
const sendMessage = ref("");
const sendError = ref("");
const verifyError = ref("");
const verified = ref(false);
const confirmError = ref("");
const confirmMessage = ref("");

// 탭을 바꾸면 인증을 처음부터 다시 (다른 방식으로 받은 코드와 섞이지 않게)
watch(isPhone, () => {
  code.value = "";
  sendMessage.value = "";
  sendError.value = "";
  verifyError.value = "";
  verified.value = false;
  confirmError.value = "";
});

async function onSendCode() {
  sending.value = true;
  sendMessage.value = "";
  sendError.value = "";
  try {
    const { data } = isPhone.value
      ? await client.post("/auth/reset-password/send-sms-code", { username: username.value, phone: phone.value })
      : await client.post("/auth/reset-password/send-email-code", { username: username.value, email: email.value });
    sendMessage.value = data.message;
  } catch (error) {
    sendError.value = getErrorMessage(error, "요청 처리 중 오류가 발생했습니다.");
  } finally {
    sending.value = false;
  }
}

async function onVerify() {
  verifying.value = true;
  verifyError.value = "";
  try {
    await client.post("/auth/reset-password/verify-code", {
      username: username.value,
      method: isPhone.value ? "sms" : "email",
      code: code.value,
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
  const pw = newPassword.value;
  if (pw.length < 8 || pw.length > 64 || !/[A-Za-z]/.test(pw) || !/[0-9]/.test(pw)) {
    confirmError.value = "비밀번호는 8~64자, 영문과 숫자를 모두 포함해야 합니다.";
    return;
  }
  if (pw !== confirmPassword.value) {
    confirmError.value = "새 비밀번호가 일치하지 않습니다.";
    return;
  }

  confirming.value = true;
  try {
    const { data } = await client.post("/auth/reset-password/confirm", {
      username: username.value,
      new_password: pw,
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
