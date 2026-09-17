<!--
  SecuQuest — 상단 헤더 및 메인 내비게이션
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <header class="sq-header">
    <div class="sq-header__brand">
      <span class="sq-header__title">SecuQuest</span>
    </div>

    <nav class="sq-header__nav" aria-label="주요 메뉴">
      <router-link class="sq-tab" to="/chapters">챕터 선택</router-link>
      <router-link class="sq-tab" to="/dashboard">학습 대시보드</router-link>
      <router-link v-if="isAdmin" class="sq-tab" to="/admin">관리자</router-link>
      <router-link class="sq-tab" to="/resources">자료실</router-link>
    </nav>

    <div class="sq-header__user">
      <span class="sq-header__avatar" aria-hidden="true">SQ</span>
      <!-- TODO: src/assets/brand/secuquest-mark.svg 준비되면 <img> 로 교체 -->
      <div class="sq-header__user-info">
        <span class="sq-header__user-name">홍길동</span>
        <span class="sq-header__user-email">hong@secuquest.dev</span>
      </div>
      <button
        type="button"
        class="sq-header__logout"
        aria-label="로그아웃"
        @click="handleLogout"
      >
        로그아웃
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref } from "vue";

const isAdmin = ref(false);

function handleLogout() {
  console.log("logout");
  // TODO: authStore.logout() 연결
}
</script>

<style scoped>
.sq-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  height: 72px;
  padding: 0 var(--sq-page-padding-x);
  background: var(--sq-bg-header);
  border-bottom: 1px solid var(--sq-card-border);
  font-family: var(--sq-font-family);
}

.sq-header__brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
  white-space: nowrap;
}

.sq-header__title {
  font-size: 20px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-header__nav {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px;
  background: var(--sq-badge-round-bg);
  flex: 1;
  justify-content: center;
}

.sq-tab {
  padding: 10px 24px;
  font-size: 15px;
  font-weight: 600;
  color: var(--sq-text-sub);
  text-decoration: none;
  white-space: nowrap;
}

.sq-tab.router-link-active {
  background: var(--sq-color-accent);
  color: #fff;
}

.sq-header__user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--sq-card-border);
  background: var(--sq-bg-card);
  white-space: nowrap;
}

.sq-header__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--sq-color-accent);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.sq-header__user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.3;
}

.sq-header__user-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-header__user-email {
  font-size: 12px;
  color: var(--sq-text-sub);
}

.sq-header__logout {
  margin-left: 16px;
  padding: 8px 14px;
  border: none;
  background: var(--sq-card-border);
  color: var(--sq-text-sub);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
</style>
