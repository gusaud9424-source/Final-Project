<!--
  SecuQuest — 로그인/아이디 찾기/비밀번호 찾기 공용 카드 레이아웃
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-auth-page">
    <div class="sq-auth-card">
      <h1 class="sq-auth-title">{{ title }}</h1>
      <slot />
      <div v-if="$slots.links" class="sq-auth-links">
        <slot name="links" />
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup>
import AppFooter from "@/components/layout/AppFooter.vue";

defineProps({
  title: {
    type: String,
    required: true,
  },
});
</script>

<style>
.sq-auth-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 24px;
}

.sq-auth-card {
  width: 100%;
  max-width: 400px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-auth-title {
  font-size: 22px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
  margin: 0 0 20px;
  text-align: center;
}

.sq-auth-tabs {
  display: flex;
  gap: 4px;
  padding: 6px;
  background: var(--sq-badge-round-bg);
  border-radius: var(--sq-radius-none);
  margin-bottom: 20px;
}

.sq-auth-tab {
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

.sq-auth-tab--active {
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
}

.sq-auth-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sq-auth-form + .sq-auth-form {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--sq-card-border);
}

.sq-auth-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-text-sub);
  margin-top: 10px;
}

.sq-auth-input {
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 14px;
  font-family: var(--sq-font-family);
  color: var(--sq-text-main);
}

.sq-auth-notice {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-auth-error {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--sq-badge-absent-text);
}

.sq-auth-submit {
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

.sq-auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-auth-links {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 13px;
}

.sq-auth-links a {
  color: var(--sq-text-link);
  text-decoration: none;
}
</style>
