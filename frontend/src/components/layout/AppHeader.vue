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
      <router-link class="sq-tab" to="/chapters">학습 진도</router-link>
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

    <div class="sq-header__actions">
      <RewardChest />

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

          <!-- 닉네임 등 회원정보 변경은 마이페이지에서 처리 -->
          <router-link class="sq-profile__mypage" to="/mypage" @click="showProfile = false">
            <i class="bi bi-person-gear" aria-hidden="true"></i>
            마이페이지 · 회원정보 변경
          </router-link>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import BrandMark from "@/components/brand/BrandMark.vue";
import RewardChest from "@/components/layout/RewardChest.vue";
import { useAuthStore } from "@/stores/auth";
import { useProfileStore } from "@/stores/profile";
import { useRewardStore } from "@/stores/reward";

const authStore = useAuthStore();
const profileStore = useProfileStore();
const rewardStore = useRewardStore();
const router = useRouter();
const route = useRoute();

const avatarInitial = computed(() => authStore.user?.name?.slice(0, 1) || "SQ");
const isDashboardActive = computed(() => route.path.startsWith("/dashboard"));

const profileWrapRef = ref(null);
const showProfile = ref(false);

const xpPercent = computed(() => {
  if (!profileStore.xpForNextLevel) return 100;
  return Math.round((profileStore.currentXp / profileStore.xpForNextLevel) * 100);
});

async function toggleProfile() {
  showProfile.value = !showProfile.value;
  if (showProfile.value && !profileStore.loaded) {
    await profileStore.fetchProfile();
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
  // 다른 계정 로그인 시 이전 사용자의 미수령 목록이 남지 않도록 초기화
  rewardStore.reset();
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

/* 보물상자 + 프로필 묶음 */
.sq-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
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






.sq-profile__mypage {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 4px;
  padding: 8px 12px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  color: var(--sq-color-accent);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.sq-profile__mypage:hover {
  background: var(--sq-color-accent-subtle);
}


/* ── 좁은 화면 (태블릿 · 휴대폰): 데스크톱(1100px 이상) 레이아웃은 그대로 ── */
@media (max-width: 1100px) {
  .sq-header {
    flex-wrap: wrap;
    height: auto;
    padding-top: 10px;
    padding-bottom: 10px;
    row-gap: 10px;
  }

  /* 메뉴는 둘째 줄 전체 폭, 넘치면 가로 스크롤 */
  .sq-header__nav {
    order: 3;
    flex: 1 1 100%;
    justify-content: flex-start;
    overflow-x: auto;
  }

  .sq-tab {
    padding: 8px 16px;
  }
}

@media (max-width: 600px) {
  .sq-header__user-info {
    display: none;
  }

  .sq-header__logout {
    margin-left: 4px;
  }

  .sq-tab {
    padding: 8px 12px;
    font-size: 14px;
  }

  .sq-header__profile-panel {
    width: min(240px, calc(100vw - 32px));
  }
}
</style>
