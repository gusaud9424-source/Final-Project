<!--
  SecuQuest — 회원가입
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="회원가입" submit-label="가입하기" block-submit :submitting="loading" @submit="onSubmit">
    <label class="sq-auth-field">
      <span class="sq-auth-field__label">아이디</span>
      <input v-model="form.username" class="form-control sq-auth-field__input" type="text" autocomplete="username" />
    </label>
    <label class="sq-auth-field">
      <span class="sq-auth-field__label">비밀번호</span>
      <input v-model="form.password" class="form-control sq-auth-field__input" type="password" autocomplete="new-password" />
    </label>
    <label class="sq-auth-field">
      <span class="sq-auth-field__label">비밀번호 확인</span>
      <input v-model="form.passwordConfirm" class="form-control sq-auth-field__input" type="password" autocomplete="new-password" />
    </label>
    <label class="sq-auth-field">
      <span class="sq-auth-field__label">이메일</span>
      <input v-model="form.email" class="form-control sq-auth-field__input" type="email" autocomplete="email" />
    </label>

    <template #footer>
      <router-link class="sq-auth-link" to="/login">이미 계정이 있나요? 로그인</router-link>
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
  email: "",
});
const loading = ref(false);

async function onSubmit() {
  // 최소 검증: 빈값, 비밀번호 확인 일치
  if (Object.values(form).some((value) => !value.trim())) {
    alert("모든 항목을 입력해 주세요.");
    return;
  }
  if (form.password !== form.passwordConfirm) {
    alert("비밀번호가 일치하지 않습니다.");
    return;
  }

  loading.value = true;
  const result = await authStore.signup({ username: form.username, password: form.password, email: form.email });
  loading.value = false;

  alert(result.message);
  if (result.success) {
    router.push("/login");
  }
}
</script>
