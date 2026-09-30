<!--
  SecuQuest — 로그인
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-login-page">
    <div class="sq-login-card">
      <h1 class="sq-login-title">SecuQuest 로그인</h1>

      <div class="sq-login-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          class="sq-login-tab"
          :class="{ 'sq-login-tab--active': role === 'student' }"
          :aria-selected="role === 'student'"
          @click="role = 'student'"
        >
          일반사용자 로그인
        </button>
        <button
          type="button"
          role="tab"
          class="sq-login-tab"
          :class="{ 'sq-login-tab--active': role === 'admin' }"
          :aria-selected="role === 'admin'"
          @click="role = 'admin'"
        >
          관리자 로그인
        </button>
      </div>

      <form class="sq-login-form" @submit.prevent="onSubmit">
        <label class="sq-login-label" for="username">아이디</label>
        <input
          id="username"
          v-model="username"
          class="sq-login-input"
          type="text"
          autocomplete="username"
          required
        />

        <label class="sq-login-label" for="password">비밀번호</label>
        <input
          id="password"
          v-model="password"
          class="sq-login-input"
          type="password"
          autocomplete="current-password"
          required
        />

        <p v-if="errorMessage" class="sq-login-error">{{ errorMessage }}</p>

        <button type="submit" class="sq-login-submit" :disabled="submitting">
          {{ submitting ? "로그인 중..." : "로그인" }}
        </button>
      </form>

      <div class="sq-login-links">
        <router-link to="/find-id">아이디 찾기</router-link>
        <span aria-hidden="true">·</span>
        <router-link to="/find-password">비밀번호 찾기</router-link>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import AppFooter from "@/components/layout/AppFooter.vue";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const role = ref("student");
const username = ref("");
const password = ref("");
const errorMessage = ref("");
const submitting = ref(false);

async function onSubmit() {
  errorMessage.value = "";
  submitting.value = true;
  const result = await authStore.login(username.value, password.value, role.value);
  submitting.value = false;

  if (result.success) {
    router.push("/dashboard");
  } else {
    errorMessage.value = result.message;
  }
}
</script>

<style scoped>
/* AuthCard 개편 전 로그인 스타일을 그대로 이관 (로그인 화면 외형 유지) */
.sq-login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 24px;
}

.sq-login-card {
  width: 100%;
  max-width: 400px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-login-title {
  font-size: 22px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
  margin: 0 0 20px;
  text-align: center;
}

.sq-login-tabs {
  display: flex;
  gap: 4px;
  padding: 6px;
  background: var(--sq-badge-round-bg);
  border-radius: var(--sq-radius-none);
  margin-bottom: 20px;
}

.sq-login-tab {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sq-text-sub);
  cursor: pointer;
  border-radius: var(--sq-radius-none);
  font-family: var(--sq-font-family);
}

.sq-login-tab--active {
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
}

.sq-login-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sq-login-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-text-sub);
  margin-top: 10px;
}

.sq-login-input {
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 14px;
  font-family: var(--sq-font-family);
  color: var(--sq-text-main);
}

.sq-login-error {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--sq-badge-absent-text);
}

.sq-login-submit {
  margin-top: 16px;
  padding: 12px 20px;
  border: none;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--sq-font-family);
}

.sq-login-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-login-links {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 13px;
}

.sq-login-links a {
  color: var(--sq-text-link);
  text-decoration: none;
}
</style>
