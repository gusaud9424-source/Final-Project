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

    <div ref="profileWrapRef" class="sq-header__profile-wrap">
      <div
        class="sq-header__user"
        role="button"
        tabindex="0"
        @click="toggleProfile"
        @keydown.enter="toggleProfile"
      >
        <span class="sq-header__avatar" aria-hidden="true">{{ avatarInitial }}</span>
        <div class="sq-header__user-info">
          <span class="sq-header__user-name">{{ authStore.user?.name }}</span>
          <span class="sq-header__user-email">{{ authStore.user?.email }}</span>
        </div>
        <button
          type="button"
          class="sq-header__logout"
          aria-label="로그아웃"
          @click.stop="handleLogout"
        >
          로그아웃
        </button>
      </div>

      <div v-if="showProfile" class="sq-header__profile-panel" @click.stop>
        <p class="sq-profile__level">Lv.{{ profileStore.level }}</p>
        <div class="sq-progress-bar" role="progressbar" :aria-valuenow="xpPercent" aria-valuemin="0" aria-valuemax="100">
          <div class="sq-progress-bar__fill" :style="{ width: xpPercent + '%' }"></div>
        </div>
        <p class="sq-profile__xp">
          {{ profileStore.currentXp }} / {{ profileStore.xpForNextLevel ?? "MAX" }} XP
        </p>
        <p class="sq-profile__points">보유 포인트 {{ profileStore.points }}P</p>

        <form class="sq-profile__form" @submit.prevent="saveNickname">
          <label class="sq-profile__label" for="sq-nickname-input">닉네임</label>
          <input
            id="sq-nickname-input"
            v-model="nicknameInput"
            class="sq-profile__input"
            type="text"
            maxlength="20"
            placeholder="닉네임"
          />
          <button type="submit" class="sq-profile__save" :disabled="nicknameSaving">
            {{ nicknameSaving ? "저장 중..." : "변경" }}
          </button>
        </form>
        <p v-if="nicknameError" class="sq-profile__error">{{ nicknameError }}</p>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import BrandMark from "@/components/brand/BrandMark.vue";
import { useAuthStore } from "@/stores/auth";
import { useProfileStore } from "@/stores/profile";
import { getErrorMessage } from "@/api/errors";

const authStore = useAuthStore();
const profileStore = useProfileStore();
const router = useRouter();
const route = useRoute();

const avatarInitial = computed(() => authStore.user?.name?.slice(0, 1) || "SQ");
const isDashboardActive = computed(() => route.path.startsWith("/dashboard"));

const profileWrapRef = ref(null);
const showProfile = ref(false);
const nicknameInput = ref("");
const nicknameSaving = ref(false);
const nicknameError = ref("");

const xpPercent = computed(() => {
  if (!profileStore.xpForNextLevel) return 100;
  return Math.round((profileStore.currentXp / profileStore.xpForNextLevel) * 100);
});

async function toggleProfile() {
  showProfile.value = !showProfile.value;
  if (showProfile.value) {
    nicknameError.value = "";
    if (!profileStore.loaded) await profileStore.fetchProfile();
    nicknameInput.value = profileStore.nickname;
  }
}

async function saveNickname() {
  nicknameSaving.value = true;
  nicknameError.value = "";
  try {
    await profileStore.updateNickname(nicknameInput.value);
  } catch (error) {
    nicknameError.value = getErrorMessage(error, "닉네임 변경에 실패했습니다.");
  } finally {
    nicknameSaving.value = false;
  }
}

function handleOutsideClick(event) {
  if (showProfile.value && profileWrapRef.value && !profileWrapRef.value.contains(event.target)) {
    showProfile.value = false;
  }
}

onMounted(() => document.addEventListener("click", handleOutsideClick));
onUnmounted(() => document.removeEventListener("click", handleOutsideClick));

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

/* 프로필 드롭다운 */
.sq-header__profile-wrap {
  position: relative;
}

.sq-header__profile-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow-hover);
  z-index: 10;
}

.sq-profile__level {
  margin: 0;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

/* 진행 바: 999px 라운드는 대시보드·과목 상세와 동일하게 예외 유지 */
.sq-progress-bar {
  height: 8px;
  border-radius: 999px;
  background: var(--sq-card-border);
  overflow: hidden;
}

.sq-progress-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: var(--sq-color-accent);
}

.sq-profile__xp,
.sq-profile__points {
  margin: 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-profile__form {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.sq-profile__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--sq-text-sub);
}

.sq-profile__input {
  padding: 8px 10px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 14px;
  font-family: var(--sq-font-family);
}

.sq-profile__save {
  margin-top: 4px;
  padding: 8px 12px;
  border: none;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.sq-profile__save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-profile__error {
  margin: 0;
  font-size: 12px;
  color: var(--sq-badge-absent-text);
}
</style>
