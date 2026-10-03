<!--
  SecuQuest — 아이디 찾기 (이메일 / 휴대폰)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard
    title="아이디 찾기"
    :description="description"
    :submitting="loading"
    :show-submit="step !== 'done'"
    @submit="onNext"
  >
    <label v-if="step === 'target'" class="sq-auth-field">
      <span class="sq-auth-field__label">{{ isPhone ? "가입 시 등록한 휴대폰 번호" : "가입 시 등록한 이메일" }}</span>
      <input
        v-model="target"
        class="form-control sq-auth-field__input"
        :type="isPhone ? 'tel' : 'email'"
        :autocomplete="isPhone ? 'tel' : 'email'"
      />
    </label>

    <label v-else-if="step === 'code'" class="sq-auth-field">
      <span class="sq-auth-field__label">인증코드</span>
      <input
        v-model="code"
        class="form-control sq-auth-field__input"
        type="text"
        inputmode="numeric"
        autocomplete="one-time-code"
      />
    </label>

    <!-- 이메일(실제 API) 경로 전용 카드 내 메시지 -->
    <p v-if="noticeMessage" class="sq-find-id-notice">{{ noticeMessage }}</p>
    <p v-if="errorMessage" class="sq-find-id-error">{{ errorMessage }}</p>

    <div v-if="step === 'done'" class="sq-find-id-done">
      <p class="sq-find-id-result">
        회원님의 아이디는 <strong>{{ foundUsername }}</strong> 입니다.
      </p>
      <router-link class="sq-auth-link" to="/login">로그인하기</router-link>
    </div>

    <template v-if="step === 'target'" #aside>
      <router-link class="sq-auth-link" :to="isPhone ? '/find-id' : '/find-id/phone'">
        {{ isPhone ? "이메일로 찾기" : "휴대폰으로 찾기" }}
      </router-link>
    </template>

    <template #footer>
      <router-link class="sq-auth-link" to="/find-password">비밀번호 찾기</router-link>
      <router-link class="sq-auth-link" to="/signup">회원가입</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import AuthCard from "@/components/auth/AuthCard.vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useAuthStore } from "@/stores/auth";

const props = defineProps({
  // 라우트 props 로 전달: "email"(/find-id) | "phone"(/find-id/phone)
  method: {
    type: String,
    default: "email",
  },
});

const authStore = useAuthStore();

const step = ref("target"); // target → code → done(이메일 경로만)
const target = ref("");
const code = ref("");
const loading = ref(false);
const noticeMessage = ref("");
const errorMessage = ref("");
const foundUsername = ref("");

const isPhone = computed(() => props.method === "phone");
const description = computed(() => {
  if (step.value === "done") {
    return "아이디 찾기가 완료되었습니다.";
  }
  if (step.value === "target") {
    return isPhone.value ? "휴대폰 번호를 입력해 주세요." : "이메일을 입력해 주세요.";
  }
  return isPhone.value
    ? "휴대폰으로 받은 인증코드를 입력해 주세요."
    : "이메일로 받은 인증코드를 입력해 주세요.";
});

// 같은 컴포넌트로 이메일↔휴대폰 라우트 전환 시 입력 상태 초기화
watch(
  () => props.method,
  () => {
    step.value = "target";
    target.value = "";
    code.value = "";
    noticeMessage.value = "";
    errorMessage.value = "";
    foundUsername.value = "";
  },
);

// 휴대폰 mock 은 alert, 이메일(실제 API)은 카드 안에 표시
function showError(message) {
  if (isPhone.value) {
    alert(message);
  } else {
    errorMessage.value = message;
  }
}

function onNext() {
  noticeMessage.value = "";
  errorMessage.value = "";
  return step.value === "target" ? sendCode() : verifyCode();
}

async function sendCode() {
  if (!target.value.trim()) {
    showError(isPhone.value ? "휴대폰 번호를 입력해 주세요." : "이메일을 입력해 주세요.");
    return;
  }

  loading.value = true;
  try {
    if (isPhone.value) {
      const result = await authStore.sendFindIdPhoneCode(target.value);
      alert(result.message);
    } else {
      const { data } = await client.post("/auth/find-id/send-code", { email: target.value });
      noticeMessage.value = data.message;
    }
    step.value = "code";
  } catch (error) {
    showError(getErrorMessage(error, "요청 처리 중 오류가 발생했습니다."));
  } finally {
    loading.value = false;
  }
}

async function verifyCode() {
  if (!code.value.trim()) {
    showError("인증코드를 입력해 주세요.");
    return;
  }

  loading.value = true;
  try {
    if (isPhone.value) {
      const result = await authStore.verifyFindIdPhoneCode(target.value, code.value);
      alert(result.message);
      // mock 은 결과가 없으므로 처음 단계로 복귀
      step.value = "target";
      code.value = "";
    } else {
      const { data } = await client.post("/auth/find-id/verify", {
        email: target.value,
        code: code.value,
      });
      foundUsername.value = data.username;
      step.value = "done";
    }
  } catch (error) {
    showError(getErrorMessage(error, "인증에 실패했습니다."));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.sq-find-id-notice,
.sq-find-id-result {
  margin: 0;
  font-size: var(--sq-auth-message-size);
  color: var(--sq-auth-text-desc);
}

.sq-find-id-error {
  margin: 0;
  font-size: var(--sq-auth-message-size);
  color: var(--sq-auth-text-error);
}

.sq-find-id-done {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sq-auth-field-gap);
}
</style>
