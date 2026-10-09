<!--
  SecuQuest — 관리자용 전체 학생 현황 (요약 · 과목별 진도 · 단계별 진행 · 학생별 진도)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-overview">
    <p v-if="loading" class="sq-overview__status">불러오는 중...</p>
    <p v-else-if="errorMessage" class="sq-overview__error" role="alert">{{ errorMessage }}</p>

    <template v-else>
      <!-- 1. 요약 카드 -->
      <section class="sq-kpi-row" aria-label="학습 현황 요약">
        <div class="sq-kpi">
          <span class="sq-kpi__label">전체 수강생</span>
          <span class="sq-kpi__value">{{ summary.totalStudents }}명</span>
        </div>
        <div class="sq-kpi">
          <span class="sq-kpi__label">평균 진도율</span>
          <span class="sq-kpi__value">{{ summary.avgPercent }}%</span>
        </div>
        <div class="sq-kpi">
          <span class="sq-kpi__label">최근 7일 학습</span>
          <span class="sq-kpi__value">{{ summary.activeLast7 }}명</span>
        </div>
        <div class="sq-kpi">
          <span class="sq-kpi__label">정체 학생 ({{ summary.stallDays }}일 이상 활동 없음)</span>
          <span class="sq-kpi__value" :class="{ 'sq-kpi__value--danger': summary.stalled }">
            {{ summary.stalled }}명
          </span>
        </div>
      </section>

      <div class="sq-overview__grid">
        <!-- 2. 과목별 평균 진도율 -->
        <section class="sq-panel">
          <h2 class="sq-panel__title">과목별 평균 진도율</h2>
          <ul class="sq-course-stats">
            <li v-for="course in courses" :key="course.slug" class="sq-course-stat">
              <span class="sq-course-stat__name">
                <span class="sq-badge" :class="`sq-badge--${difficultyTone(course.difficulty)}`">
                  {{ course.difficulty }}
                </span>
                {{ course.title }}
              </span>
              <div
                class="sq-bar"
                role="progressbar"
                :aria-valuenow="course.avgPercent"
                aria-valuemin="0"
                aria-valuemax="100"
                :aria-label="`${course.title} 평균 진도율`"
              >
                <div class="sq-bar__fill" :style="{ width: course.avgPercent + '%' }"></div>
              </div>
              <span class="sq-course-stat__value">{{ course.avgPercent }}%</span>
              <span class="sq-course-stat__meta">
                수강 {{ course.enrolled }} · 완료 {{ course.completedCount }}
              </span>
            </li>
          </ul>
        </section>

        <!-- 3. 단계별 진행 인원 -->
        <section class="sq-panel">
          <h2 class="sq-panel__title">실습 레벨별 통과율 (전체 수강 건)</h2>
          <p v-if="!funnel.total" class="sq-overview__status">수강 기록이 없습니다.</p>
          <template v-else>
            <ul class="sq-funnel">
              <li v-for="step in funnel.steps" :key="step.key" class="sq-funnel__step">
                <div class="sq-funnel__head">
                  <span>{{ STEP_LABELS[step.key] }}</span>
                  <span>{{ step.count }}/{{ funnel.total }} · {{ step.percent }}%</span>
                </div>
                <div class="sq-bar">
                  <div class="sq-bar__fill" :style="{ width: step.percent + '%' }"></div>
                </div>
              </li>
            </ul>
            <p v-if="biggestDrop" class="sq-funnel__alert">
              <i class="bi bi-exclamation-triangle" aria-hidden="true"></i>
              {{ biggestDrop.label }} 레벨에서 이탈 {{ biggestDrop.drop }}%p
            </p>
          </template>
        </section>
      </div>

      <!-- 4. 학생별 진도 -->
      <section class="sq-panel">
        <div class="sq-panel__toolbar">
          <h2 class="sq-panel__title sq-panel__title--inline">학생별 진도</h2>
          <div class="sq-panel__controls">
            <input
              v-model="keyword"
              type="search"
              class="sq-input"
              placeholder="이름 · 아이디 검색"
              aria-label="학생 검색"
            />
            <select v-model="statusFilter" class="sq-input" aria-label="상태 필터">
              <option value="">상태: 전체</option>
              <option v-for="s in STATUS_LIST" :key="s" :value="s">{{ s }}</option>
            </select>
            <button type="button" class="sq-btn-outline" @click="downloadCsv">
              <i class="bi bi-download" aria-hidden="true"></i> CSV
            </button>
          </div>
        </div>

        <p v-if="!filteredStudents.length" class="sq-overview__status">조건에 맞는 학생이 없습니다.</p>

        <div v-else class="sq-table-wrap">
          <table class="sq-table">
            <thead>
              <tr>
                <th>
                  <button type="button" class="sq-sort" @click="setSort('name')">학생 {{ sortMark("name") }}</button>
                </th>
                <th v-for="course in courses" :key="course.slug" :title="course.title">
                  {{ shortLabel(course.slug) }}
                </th>
                <th>
                  <button type="button" class="sq-sort" @click="setSort('percent')">전체 {{ sortMark("percent") }}</button>
                </th>
                <th>
                  <button type="button" class="sq-sort" @click="setSort('lastActivity')">마지막 활동 {{ sortMark("lastActivity") }}</button>
                </th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="student in filteredStudents" :key="student.id">
                <tr
                  class="sq-table__row"
                  :class="{ 'sq-table__row--open': openId === student.id }"
                  tabindex="0"
                  :aria-expanded="openId === student.id"
                  @click="toggle(student.id)"
                  @keydown.enter="toggle(student.id)"
                >
                  <td>
                    <router-link
                      :to="`/admin/students/${student.id}`"
                      class="sq-table__name"
                      :title="`${student.name} 학생 현황 페이지`"
                      @click.stop
                    >
                      {{ student.name }}
                    </router-link>
                    <span class="sq-table__sub">{{ student.username }}</span>
                  </td>
                  <td v-for="course in courses" :key="course.slug" class="sq-table__cell">
                    <span v-if="student.courses[course.slug]" :class="cellClass(student.courses[course.slug].percent)">
                      {{ student.courses[course.slug].percent }}%
                    </span>
                    <span v-else class="sq-table__none">-</span>
                  </td>
                  <td class="sq-table__total">{{ student.percent }}%</td>
                  <td>{{ relativeDate(student.lastActivity) }}</td>
                  <td>
                    <span class="sq-status" :class="`sq-status--${STATUS_TONE[student.status]}`">
                      {{ student.status }}
                    </span>
                  </td>
                </tr>

                <!-- 5. 학생 상세 (행 클릭 시 펼침) -->
                <tr v-if="openId === student.id" class="sq-detail-row">
                  <td :colspan="courses.length + 4">
                    <div class="sq-detail">
                      <div class="sq-detail__meta">
                        <span><i class="bi bi-envelope" aria-hidden="true"></i> {{ student.email }}</span>
                        <span><i class="bi bi-coin" aria-hidden="true"></i> {{ student.points.toLocaleString() }}P</span>
                        <span><i class="bi bi-calendar-check" aria-hidden="true"></i> 출석 {{ student.attendanceDays }}일</span>
                        <span><i class="bi bi-list-check" aria-hidden="true"></i> 실습 레벨 {{ student.completedSteps }}/{{ student.totalSteps }}</span>
                      </div>
                      <p v-if="!student.courseCount" class="sq-overview__status">수강 중인 과목이 없습니다.</p>
                      <table v-else class="sq-detail__table">
                        <thead>
                          <tr>
                            <th>과목</th>
                            <th v-for="key in STEP_KEYS" :key="key">{{ STEP_LABELS[key] }}</th>
                            <th>진도</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="course in enrolledCourses(student)" :key="course.slug">
                            <td>{{ course.title }}</td>
                            <td v-for="key in STEP_KEYS" :key="key">
                              <span v-if="student.courses[course.slug].steps[key]" class="sq-step-done">
                                <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
                                {{ formatDate(student.courses[course.slug].steps[key]) }}
                              </span>
                              <span v-else class="sq-table__none">미완료</span>
                            </td>
                            <td>{{ student.courses[course.slug].percent }}%</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

// 진도율 기준: 실습 레벨 (백엔드 PROGRESS_KEYS)
const STEP_KEYS = ["tier_low", "tier_medium", "tier_high", "tier_impossible"];
const STEP_LABELS = { tier_low: "하", tier_medium: "중", tier_high: "상", tier_impossible: "안전" };
const STATUS_LIST = ["진행중", "정체", "완료", "미시작"];
const STATUS_TONE = { 진행중: "progress", 정체: "stalled", 완료: "done", 미시작: "none" };
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };
// 표 열 이름용 약칭
const SHORT_LABELS = {
  "command-injection": "CMD",
  "xss-reflected": "XSS-R",
  "xss-dom": "XSS-D",
  "xss-stored": "XSS-S",
  "sql-injection": "SQLi",
  csrf: "CSRF",
  "file-upload": "Upload",
  "sql-injection-blind": "Blind",
};

const loading = ref(true);
const errorMessage = ref("");
const summary = ref({ totalStudents: 0, avgPercent: 0, activeLast7: 0, stalled: 0, stallDays: 7 });
const courses = ref([]);
const funnel = ref({ total: 0, steps: [] });
const students = ref([]);

const keyword = ref("");
const statusFilter = ref("");
const sortKey = ref("name");
const sortDir = ref("asc");
const openId = ref(null);

function difficultyTone(difficulty) {
  return DIFFICULTY_TONE[difficulty] || "success";
}

function shortLabel(slug) {
  return SHORT_LABELS[slug] || slug;
}

// 진도율 구간별 셀 색
function cellClass(percent) {
  if (percent >= 100) return "sq-cell sq-cell--done";
  if (percent > 0) return "sq-cell sq-cell--progress";
  return "sq-cell sq-cell--zero";
}

// 인접 단계 간 가장 큰 감소폭
const biggestDrop = computed(() => {
  const steps = funnel.value.steps;
  let best = null;
  for (let i = 1; i < steps.length; i += 1) {
    const drop = steps[i - 1].percent - steps[i].percent;
    if (drop > 0 && (!best || drop > best.drop)) best = { label: STEP_LABELS[steps[i].key], drop };
  }
  return best;
});

const filteredStudents = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  const list = students.value.filter((s) => {
    if (statusFilter.value && s.status !== statusFilter.value) return false;
    if (!q) return true;
    return s.name.toLowerCase().includes(q) || s.username.toLowerCase().includes(q);
  });
  const dir = sortDir.value === "asc" ? 1 : -1;
  return [...list].sort((a, b) => {
    if (sortKey.value === "percent") return (a.percent - b.percent) * dir;
    if (sortKey.value === "lastActivity") return ((a.lastActivity || "") > (b.lastActivity || "") ? 1 : -1) * dir;
    return a.name.localeCompare(b.name, "ko") * dir;
  });
});

function setSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = key;
    sortDir.value = key === "name" ? "asc" : "desc";
  }
}

function sortMark(key) {
  if (sortKey.value !== key) return "";
  return sortDir.value === "asc" ? "▲" : "▼";
}

function toggle(id) {
  openId.value = openId.value === id ? null : id;
}

function enrolledCourses(student) {
  return courses.value.filter((c) => student.courses[c.slug]);
}

function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// 오늘 / 어제 / N일 전
function relativeDate(iso) {
  if (!iso) return "-";
  const start = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((start(new Date()) - start(new Date(iso))) / 86400000);
  if (days <= 0) return "오늘";
  if (days === 1) return "어제";
  return `${days}일 전`;
}

// 현재 필터 결과를 CSV로 저장 (엑셀 한글 깨짐 방지용 BOM 포함)
function downloadCsv() {
  const header = ["이름", "아이디", "이메일", ...courses.value.map((c) => c.title), "전체 진도율", "마지막 활동", "상태", "포인트", "출석일"];
  const rows = filteredStudents.value.map((s) => [
    s.name,
    s.username,
    s.email,
    ...courses.value.map((c) => (s.courses[c.slug] ? `${s.courses[c.slug].percent}%` : "-")),
    `${s.percent}%`,
    formatDate(s.lastActivity),
    s.status,
    s.points,
    s.attendanceDays,
  ]);
  const escape = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const csv = [header, ...rows].map((r) => r.map(escape).join(",")).join("\r\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `secuquest_학생진도_${formatDate(new Date().toISOString())}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(async () => {
  try {
    const { data } = await client.get("/admin/progress");
    summary.value = data.summary;
    courses.value = data.courses;
    funnel.value = data.funnel;
    students.value = data.students;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "학생 현황을 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.sq-overview {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-overview__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-overview__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

/* 요약 카드 */
.sq-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sq-card-gap);
}

.sq-kpi {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-kpi__label {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-kpi__value {
  font-size: 26px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-kpi__value--danger {
  color: var(--sq-badge-absent-text);
}

/* 패널 공통 */
.sq-overview__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: var(--sq-card-gap);
}

.sq-panel {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
  min-width: 0;
}

.sq-panel__title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-panel__title--inline {
  margin: 0;
}

.sq-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.sq-panel__controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sq-input {
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-size: 13px;
}

.sq-input:focus {
  outline: none;
  border-color: var(--sq-color-accent);
}

.sq-btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: transparent;
  color: var(--sq-color-accent);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.sq-btn-outline:hover {
  background: var(--sq-color-accent-subtle);
}

/* 진행 바 */
.sq-bar {
  height: 8px;
  border-radius: 999px;
  background: var(--sq-card-border);
  overflow: hidden;
}

.sq-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: var(--sq-color-accent);
  transition: width 300ms ease;
}

/* 난이도 배지 */
.sq-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--sq-radius-none);
  font-size: 11px;
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

/* 과목별 진도 */
.sq-course-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-course-stat {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr) 40px 110px;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--sq-text-main);
}

.sq-course-stat__name {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sq-course-stat__value {
  font-weight: 700;
  text-align: right;
}

.sq-course-stat__meta {
  font-size: 12px;
  color: var(--sq-text-sub);
}

/* 단계별 진행 */
.sq-funnel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-funnel__head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--sq-text-main);
}

.sq-funnel__alert {
  margin: 16px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-badge-absent-text);
}

/* 학생 표 */
.sq-table-wrap {
  overflow-x: auto;
}

.sq-table {
  width: 100%;
  border-collapse: collapse;
}

.sq-table th,
.sq-table td {
  padding: 10px 8px;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 13px;
  color: var(--sq-text-main);
  text-align: left;
  white-space: nowrap;
}

.sq-table th {
  font-size: 12px;
  font-weight: 600;
  color: var(--sq-text-sub);
}

.sq-sort {
  padding: 0;
  border: none;
  background: none;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.sq-table__row {
  cursor: pointer;
}

.sq-table__row:hover,
.sq-table__row--open {
  background: var(--sq-color-accent-subtle);
}

.sq-table__row:focus-visible {
  outline: 2px solid var(--sq-color-accent);
  outline-offset: -2px;
}

.sq-table__name {
  display: block;
  font-weight: 600;
  color: var(--sq-text-link);
  text-decoration: none;
}

.sq-table__name:hover {
  text-decoration: underline;
}

.sq-table__sub {
  font-size: 12px;
  color: var(--sq-text-sub);
}

.sq-table__total {
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-table__none {
  color: var(--sq-text-sub);
}

.sq-cell {
  display: inline-block;
  min-width: 44px;
  padding: 2px 6px;
  border-radius: var(--sq-radius-none);
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.sq-cell--done {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-cell--progress {
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
}

.sq-cell--zero {
  background: var(--sq-card-border);
  color: var(--sq-text-sub);
}

/* 상태 배지 */
.sq-status {
  display: inline-flex;
  padding: 3px 10px;
  border-radius: var(--sq-radius-none);
  font-size: 12px;
  font-weight: 700;
}

.sq-status--progress {
  background: var(--sq-color-accent-subtle);
  color: var(--sq-color-accent);
}

.sq-status--stalled {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

.sq-status--done {
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
}

.sq-status--none {
  background: var(--sq-card-border);
  color: var(--sq-text-sub);
}

/* 학생 상세 */
.sq-detail-row > td {
  padding: 0;
  background: var(--sq-bg-page);
}

.sq-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}

.sq-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-detail__table {
  width: 100%;
  border-collapse: collapse;
  background: var(--sq-bg-card);
}

.sq-detail__table th,
.sq-detail__table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 13px;
  text-align: left;
}

.sq-step-done {
  color: var(--sq-badge-submitted-text);
  font-weight: 600;
}

@media (prefers-reduced-motion: reduce) {
  .sq-bar__fill {
    transition: none;
  }
}

/* 반응형 */
@media (max-width: 992px) {
  .sq-overview__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 768px) {
  .sq-kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sq-course-stat {
    grid-template-columns: minmax(0, 1fr) 40px;
  }

  .sq-course-stat .sq-bar,
  .sq-course-stat__meta {
    grid-column: 1 / -1;
  }
}
</style>
