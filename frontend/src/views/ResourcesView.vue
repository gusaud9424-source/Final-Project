<!--
  SecuQuest — 자료실 (취약점별 학습 문서 내려받기)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-resources">
    <section class="sq-resources__header">
      <h1 class="sq-resources__title">자료실</h1>
      <p class="sq-resources__subtitle">
        취약점별 학습 문서를 내려받아 읽어 보세요. 개념 · 피해 · 방어 · 실습 방법 · 미션 수행 가이드를 한 문서에 정리했습니다.
      </p>
    </section>

    <section class="sq-resources__card">
      <ul class="sq-resources__list">
        <li v-for="course in courses" :key="course.id" class="sq-resources__item">
          <span class="sq-badge" :class="`sq-badge--${DIFFICULTY_TONE[course.difficulty] || 'success'}`">
            {{ course.difficulty }}
          </span>
          <div class="sq-resources__info">
            <p class="sq-resources__name">{{ course.title }}</p>
            <p class="sq-resources__desc">{{ course.desc }}</p>
          </div>
          <button
            type="button"
            class="sq-resources__download"
            :aria-label="`${course.title} 학습 문서 내려받기`"
            @click="downloadResourceDoc(course)"
          >
            <i class="bi bi-file-earmark-arrow-down" aria-hidden="true"></i>
            문서 내려받기
          </button>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useEnrollStore } from "@/stores/enroll";
import { downloadResourceDoc } from "@/utils/resourceDoc";

const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };

const enrollStore = useEnrollStore();
// 난이도 순서(초급 → 중급 → 고급)는 enroll 스토어 정의 순서를 그대로 따른다
const courses = computed(() => enrollStore.items);
</script>

<style scoped>
.sq-resources {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
  padding: 24px var(--sq-page-padding-x);
  font-family: var(--sq-font-family);
}

.sq-resources__header,
.sq-resources__card {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-card-radius);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-resources__title {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-resources__subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-resources__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-resources__item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 4px;
  border-bottom: 1px solid var(--sq-card-border);
}

.sq-resources__item:last-child {
  border-bottom: none;
}

.sq-resources__info {
  flex: 1;
  min-width: 0;
}

.sq-resources__name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-resources__desc {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

/* 오른쪽 끝 내려받기 버튼 */
.sq-resources__download {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--sq-color-danger);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-danger);
  color: var(--sq-color-on-accent);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.sq-resources__download:hover {
  border-color: var(--sq-color-danger-hover);
  background: var(--sq-color-danger-hover);
}

.sq-badge {
  flex-shrink: 0;
  padding: 3px 10px;
  border-radius: var(--sq-radius-none);
  font-size: 12px;
  font-weight: 700;
}

.sq-badge--success {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-badge--warning {
  background: var(--sq-badge-dday-bg);
  color: var(--sq-badge-dday-text);
}

.sq-badge--danger {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

@media (max-width: 640px) {
  .sq-resources__item {
    flex-wrap: wrap;
  }
}
</style>
