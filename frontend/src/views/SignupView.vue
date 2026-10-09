<!--
  SecuQuest — 회원가입
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="회원가입">
    <form class="sq-auth-form" novalidate @submit.prevent="onSubmit">
      <label class="sq-auth-label" for="su-username">아이디</label>
      <input id="su-username" v-model="form.username" class="sq-auth-input" type="text" autocomplete="username" maxlength="20" />
      <span class="sq-auth-hint">영문·숫자·밑줄(_) 4~20자</span>

      <label class="sq-auth-label" for="su-password">비밀번호</label>
      <input id="su-password" v-model="form.password" class="sq-auth-input" type="password" autocomplete="new-password" maxlength="64" />
      <span class="sq-auth-hint">8~64자, 영문과 숫자를 모두 포함</span>

      <label class="sq-auth-label" for="su-password-confirm">비밀번호 확인</label>
      <input id="su-password-confirm" v-model="form.passwordConfirm" class="sq-auth-input" type="password" autocomplete="new-password" maxlength="64" />

      <label class="sq-auth-label" for="su-name">이름</label>
      <input id="su-name" v-model="form.name" class="sq-auth-input" type="text" autocomplete="name" maxlength="30" />

      <label class="sq-auth-label" for="su-email">이메일</label>
      <input id="su-email" v-model="form.email" class="sq-auth-input" type="email" autocomplete="email" maxlength="120" />
      <span class="sq-auth-hint">아이디 찾기·비밀번호 재설정 인증코드를 받는 주소</span>

      <label class="sq-auth-label" for="su-phone">휴대폰 번호</label>
      <input
        id="su-phone"
        v-model="form.phone"
        class="sq-auth-input"
        type="tel"
        inputmode="numeric"
        autocomplete="tel"
        maxlength="13"
        placeholder="01012345678"
      />
      <span class="sq-auth-hint">아이디 찾기·비밀번호 재설정 SMS 인증에 사용</span>

      <p v-if="errorMessage" class="sq-auth-error" role="alert">{{ errorMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="loading">
        {{ loading ? "가입 중..." : "가입하기" }}
      </button>
    </form>

    <template #links>
      <span>이미 계정이 있나요?</span>
      <router-link to="/login">로그인</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import AuthCard from "@/components/auth/AuthCard.vue";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: "",
  password: "",
  passwordConfirm: "",
  name: "",
  email: "",
  phone: "",
});
const loading = ref(false);
const errorMessage = ref("");

// 화면 1차 검사: 사용자에게 빨리 알려주는 용도 (최종 판단은 항상 서버 auth.py 의 _validate_signup)
function validate() {
  if (Object.values(form).some((value) => !value.trim())) return "모든 항목을 입력해 주세요.";
  if (!/^[A-Za-z0-9_]{4,20}$/.test(form.username.trim())) return "아이디는 영문·숫자·밑줄(_) 4~20자로 입력하세요.";
  if (form.password.length < 8 || form.password.length > 64) return "비밀번호는 8~64자로 입력하세요.";
  if (!/[A-Za-z]/.test(form.password) || !/[0-9]/.test(form.password)) {
    return "비밀번호에는 영문과 숫자가 모두 들어가야 합니다.";
  }
  if (form.password !== form.passwordConfirm) return "비밀번호가 일치하지 않습니다.";
  if (!/^01[0-9]{8,9}$/.test(form.phone.replace(/\D/g, ""))) {
    return "휴대폰 번호는 숫자 10~11자리(예: 01012345678)로 입력하세요.";
  }
  return "";
}

async function onSubmit() {
  if (loading.value) return;
  errorMessage.value = validate();
  if (errorMessage.value) return;

  loading.value = true;
  const result = await authStore.signup({
    username: form.username.trim(),
    password: form.password,
    name: form.name.trim(),
    email: form.email.trim(),
    phone: form.phone,
  });
  loading.value = false;

  if (!result.success) {
    errorMessage.value = result.message;
    return;
  }
  alert(result.message);
  router.push("/login");
}
</script>
