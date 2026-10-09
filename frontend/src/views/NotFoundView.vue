<!--
  SecuQuest — 404 페이지 (없는 주소 안내 + 돌아갈 길 제공)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-notfound">
    <section class="sq-notfound__card" aria-labelledby="sq-notfound-title">
      <BrandMark class="sq-notfound__mark" />
      <p class="sq-notfound__code" aria-hidden="true">404</p>
      <h1 id="sq-notfound-title" class="sq-notfound__title">페이지를 찾을 수 없습니다</h1>
      <p class="sq-notfound__desc">
        주소가 잘못 입력되었거나, 페이지가 이동 또는 삭제되었을 수 있습니다.
      </p>
      <!-- 텍스트 보간({{ }})으로만 출력 → 주소에 태그를 넣어도 HTML 로 해석되지 않음 -->
      <p class="sq-notfound__path">
        <span class="sq-notfound__path-label">요청한 주소</span>
        <code class="sq-notfound__path-value">{{ requestedPath }}</code>
      </p>

      <div class="sq-notfound__actions">
        <router-link class="sq-notfound__btn sq-notfound__btn--primary" to="/dashboard">
          <i class="bi bi-house-door" aria-hidden="true"></i>
          학습 대시보드로 이동
        </router-link>
        <button type="button" class="sq-notfound__btn sq-notfound__btn--ghost" @click="goBack">
          <i class="bi bi-arrow-left" aria-hidden="true"></i>
          이전 페이지
        </button>
      </div>

      <nav class="sq-notfound__links" aria-label="자주 찾는 메뉴">
        <router-link to="/enroll">수강신청</router-link>
        <router-link to="/chapters">학습 진도</router-link>
        <router-link to="/resources">자료실</router-link>
        <router-link to="/mypage">마이페이지</router-link>
      </nav>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import BrandMark from "@/components/brand/BrandMark.vue";

const MAX_PATH_LENGTH = 80;

const route = useRoute();
const router = useRouter();

// 긴 주소는 화면이 깨지지 않게 줄여서 표시
const requestedPath = computed(() => {
  const path = route.fullPath;
  return path.length > MAX_PATH_LENGTH ? `${path.slice(0, MAX_PATH_LENGTH)}…` : path;
});

function goBack() {
  // 바로 이 주소로 들어온 경우(이전 기록 없음)는 대시보드로
  if (window.history.state?.back) {
    router.back();
  } else {
    router.push("/dashboard");
  }
}
</script>

<style scoped>
.sq-notfound {
  display: flex;
  justify-content: center;
  padding: 48px 0;
  font-family: var(--sq-font-family);
}

.sq-notfound__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 560px;
  padding: 40px var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-card-radius);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
  text-align: center;
}

.sq-notfound__mark {
  margin-bottom: 12px;
}

.sq-notfound__code {
  margin: 0;
  font-size: 72px;
  font-weight: var(--sq-font-weight-heading);
  line-height: 1;
  color: var(--sq-color-accent);
  letter-spacing: 2px;
}

.sq-notfound__title {
  margin: 16px 0 8px;
  font-size: 24px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-notfound__desc {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-notfound__path {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 100%;
  margin: 20px 0 0;
  padding: 12px 16px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-badge-round-bg);
}

.sq-notfound__path-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--sq-text-sub);
}

.sq-notfound__path-value {
  max-width: 100%;
  font-size: 13px;
  color: var(--sq-text-main);
  word-break: break-all;
}

.sq-notfound__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 24px;
}

.sq-notfound__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  border-radius: var(--sq-radius-none);
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}

.sq-notfound__btn--primary {
  border: 1px solid var(--sq-color-accent);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
}

.sq-notfound__btn--primary:hover {
  background: var(--sq-color-accent-hover);
}

.sq-notfound__btn--ghost {
  border: 1px solid var(--sq-color-accent);
  background: transparent;
  color: var(--sq-color-accent);
  font-family: var(--sq-font-family);
}

.sq-notfound__btn--ghost:hover {
  background: var(--sq-color-accent-subtle);
}

.sq-notfound__links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--sq-card-border);
  width: 100%;
}

.sq-notfound__links a {
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-text-link);
  text-decoration: none;
}

.sq-notfound__links a:hover {
  text-decoration: underline;
}
</style>
