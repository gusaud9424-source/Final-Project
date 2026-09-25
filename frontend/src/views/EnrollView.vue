<!--
  SecuQuest — 수강신청 페이지
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-enroll">
    <!-- 과목 헤더 카드 -->
    <section class="sq-enroll__header">
      <h1 class="sq-enroll__title">수강신청</h1>
      <p class="sq-enroll__subtitle">OWASP 기반 6대 취약점 · 8개 모듈</p>

      <ul class="sq-chip-row">
        <li class="sq-chip">
          <i class="bi bi-bar-chart-steps" aria-hidden="true"></i>
          난이도 3단계
        </li>
        <li class="sq-chip">
          <i class="bi bi-collection" aria-hidden="true"></i>
          총 8개 모듈
        </li>
        <li class="sq-chip">
          <i class="bi bi-box" aria-hidden="true"></i>
          환경: Docker Sandbox
        </li>
        <li class="sq-chip">
          <i class="bi bi-check-circle" aria-hidden="true"></i>
          수강 중 {{ enrolledCount }}/{{ totalCount }}
        </li>
      </ul>
    </section>

    <!-- 강의 목록 -->
    <section class="sq-enroll__body">
      <div v-for="group in groupedByDifficulty" :key="group.difficulty" class="sq-diff-group">
        <h2 class="sq-diff-group__title">{{ group.difficulty }}</h2>

        <div class="sq-lecture-list">
          <template v-for="row in group.rows" :key="row.id">
            <!-- 단일 실습 행 -->
            <article v-if="!row.isGroup" class="sq-lecture-row">
              <button
                type="button"
                class="sq-lecture-row__main"
                :aria-expanded="expanded.has(row.id)"
                @click="toggleExpand(row.id)"
              >
                <span class="sq-badge" :class="`sq-badge--${difficultyTone(row.difficulty)}`">
                  {{ row.difficulty }}
                </span>
                <span class="sq-lecture-row__text">
                  <span class="sq-lecture-row__name">{{ row.title }}</span>
                  <span class="sq-lecture-row__desc">{{ row.desc }}</span>
                </span>
                <i
                  class="bi sq-lecture-row__chevron"
                  :class="expanded.has(row.id) ? 'bi-chevron-up' : 'bi-chevron-down'"
                  aria-hidden="true"
                ></i>
              </button>
              <button type="button" class="sq-btn-enroll" @click.stop="handleEnroll(row)">
                {{ row.enrolled ? "이어하기" : "수강" }}
              </button>

              <div v-if="expanded.has(row.id)" class="sq-lecture-detail">
                <p><strong>설명</strong> {{ row.detail.summary }}</p>
                <p><strong>공격 예시</strong> {{ row.detail.exploit }}</p>
                <p><strong>방어 방법</strong> {{ row.detail.defense }}</p>
              </div>
            </article>

            <!-- XSS 상위 그룹 행 -->
            <article v-else class="sq-lecture-row">
              <button
                type="button"
                class="sq-lecture-row__main"
                :aria-expanded="expanded.has(row.groupId)"
                @click="toggleExpand(row.groupId)"
              >
                <span class="sq-badge" :class="`sq-badge--${difficultyTone(row.difficulty)}`">
                  {{ row.difficulty }}
                </span>
                <span class="sq-lecture-row__text">
                  <span class="sq-lecture-row__name">{{ row.title }}</span>
                  <span class="sq-lecture-row__desc">{{ row.desc }}</span>
                </span>
                <i
                  class="bi sq-lecture-row__chevron"
                  :class="expanded.has(row.groupId) ? 'bi-chevron-up' : 'bi-chevron-down'"
                  aria-hidden="true"
                ></i>
              </button>

              <div v-if="expanded.has(row.groupId)" class="sq-lecture-subrows">
                <div v-for="child in row.children" :key="child.id" class="sq-lecture-subrow">
                  <button
                    type="button"
                    class="sq-lecture-row__main sq-lecture-row__main--sub"
                    :aria-expanded="expanded.has(child.id)"
                    @click="toggleExpand(child.id)"
                  >
                    <span class="sq-lecture-row__text">
                      <span class="sq-lecture-row__name">{{ child.title }}</span>
                      <span class="sq-lecture-row__desc">{{ child.desc }}</span>
                    </span>
                    <i
                      class="bi sq-lecture-row__chevron"
                      :class="expanded.has(child.id) ? 'bi-chevron-up' : 'bi-chevron-down'"
                      aria-hidden="true"
                    ></i>
                  </button>
                  <button type="button" class="sq-btn-enroll" @click.stop="handleEnroll(child)">
                    {{ child.enrolled ? "이어하기" : "수강" }}
                  </button>

                  <div v-if="expanded.has(child.id)" class="sq-lecture-detail">
                    <p><strong>설명</strong> {{ child.detail.summary }}</p>
                    <p><strong>공격 예시</strong> {{ child.detail.exploit }}</p>
                    <p><strong>방어 방법</strong> {{ child.detail.defense }}</p>
                  </div>
                </div>
              </div>
            </article>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { useRouter } from "vue-router";
import { useEnrollStore } from "@/stores/enroll";

const router = useRouter();
const enrollStore = useEnrollStore();

const enrolledCount = computed(() => enrollStore.items.filter((i) => i.enrolled).length);
const totalCount = computed(() => enrollStore.items.length);

const expanded = reactive(new Set());
function toggleExpand(id) {
  if (expanded.has(id)) {
    expanded.delete(id);
  } else {
    expanded.add(id);
  }
}

const DIFFICULTY_ORDER = ["초급", "중급", "고급"];
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };
function difficultyTone(difficulty) {
  return DIFFICULTY_TONE[difficulty] || "success";
}

const groupedByDifficulty = computed(() => {
  return DIFFICULTY_ORDER.map((difficulty) => {
    const items = enrollStore.items.filter((i) => i.difficulty === difficulty);

    const rows = [];
    const xssItems = items.filter((i) => i.category === "xss");
    const restItems = items.filter((i) => i.category !== "xss");

    restItems.forEach((item) => rows.push(item));

    if (xssItems.length) {
      rows.unshift({
        isGroup: true,
        groupId: `${difficulty}-xss`,
        difficulty,
        title: "XSS",
        desc: "반사·DOM·저장형 3가지 유형으로 나뉘는 스크립트 삽입 취약점",
        children: xssItems,
      });
    }

    return { difficulty, rows };
  }).filter((group) => group.rows.length);
});

function handleEnroll(item) {
  enrollStore.enroll(item.id);
  router.push(item.route);
}
</script>

<style scoped>
.sq-enroll {
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--sq-page-padding-x) var(--sq-page-padding-x) 48px;
  font-family: var(--sq-font-family);
  color: var(--sq-text-body);
}

/* 과목 헤더 카드 */
.sq-enroll__header {
  padding: var(--sq-card-padding);
  background: var(--sq-bg-card);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
}

.sq-enroll__title {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-enroll__subtitle {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
  border-radius: var(--sq-radius-none);
  font-size: 13px;
  font-weight: 600;
}

/* 본문 */
.sq-enroll__body {
  margin-top: var(--sq-card-gap);
}

.sq-diff-group + .sq-diff-group {
  margin-top: 28px;
}

.sq-diff-group__title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-lecture-list {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-lecture-row {
  background: var(--sq-bg-card);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  box-shadow: var(--sq-card-shadow);
  padding: var(--sq-card-padding);
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.sq-lecture-row__main {
  flex: 1 1 320px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: none;
  background: transparent;
  padding: 0;
  text-align: left;
  cursor: pointer;
  color: inherit;
  min-width: 0;
}

.sq-lecture-row__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.sq-lecture-row__name {
  font-size: 15px;
  font-weight: 700;
  color: var(--sq-text-main);
}

.sq-lecture-row__desc {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-lecture-row__chevron {
  margin-left: auto;
  color: var(--sq-text-sub);
  flex-shrink: 0;
}

.sq-btn-enroll {
  flex-shrink: 0;
  padding: 8px 20px;
  border: none;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.sq-btn-enroll:hover {
  background: var(--sq-color-accent-hover);
}

.sq-lecture-detail {
  flex-basis: 100%;
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid var(--sq-card-border);
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-lecture-detail strong {
  color: var(--sq-text-main);
  margin-right: 6px;
}

.sq-lecture-subrows {
  flex-basis: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 24px;
  border-left: 2px solid var(--sq-card-border);
}

.sq-lecture-subrow {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.sq-lecture-row__main--sub {
  flex: 1 1 260px;
}

/* 난이도 배지 (초=success 계열 / 중=warning 계열 / 고=danger 계열) */
.sq-badge {
  flex-shrink: 0;
  padding: 4px 10px;
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

/* 다크모드 */
@media (prefers-color-scheme: dark) {
  .sq-enroll {
    color: var(--sq-text-body);
  }
}

/* 반응형 */
@media (max-width: 768px) {
  .sq-enroll {
    padding: 20px 16px 40px;
  }

  .sq-lecture-row {
    flex-direction: column;
    align-items: stretch;
  }

  .sq-btn-enroll {
    align-self: flex-start;
  }

  .sq-lecture-subrows {
    padding-left: 12px;
  }
}
</style>
