<!--
  SecuQuest — 상단 헤더 및 메인 내비게이션
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <header class="sq-header">
    <router-link class="sq-header__brand" to="/dashboard">
      <BrandMark class="sq-header__mark" />
      <span class="sq-header__title">SecuQuest</span>
    </router-link>

    <nav class="sq-header__nav" aria-label="주요 메뉴">
      <router-link class="sq-tab" to="/enroll">수강신청</router-link>
      <router-link class="sq-tab" to="/chapters">챕터 선택</router-link>
      <router-link
        class="sq-tab"
        :class="{ 'router-link-active': isDashboardActive }"
        to="/dashboard"
      >
        학습 대시보드
      </router-link>
      <router-link v-if="authStore.isAdmin" class="sq-tab" to="/admin">관리자</router-link>
      <router-link class="sq-tab" to="/resources">자료실</router-link>
    </nav>

    <div class="sq-header__user">
      <span class="sq-header__avatar" aria-hidden="true">{{ avatarInitial }}</span>
      <div class="sq-header__user-info">
        <span class="sq-header__user-name">{{ authStore.user?.name }}</span>
        <span class="sq-header__user-email">{{ authStore.user?.email }}</span>
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
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import BrandMark from "@/components/brand/BrandMark.vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const avatarInitial = computed(() => authStore.user?.name?.slice(0, 1) || "SQ");
const isDashboardActive = computed(() => route.path.startsWith("/dashboard"));

async function handleLogout() {
  await authStore.logout();
  router.push("/login");
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
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  text-decoration: none;
}

.sq-header__mark {
  flex-shrink: 0;
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
  color: var(--sq-color-on-accent);
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
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
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
