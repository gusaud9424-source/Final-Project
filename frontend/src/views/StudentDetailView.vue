<!--
  SecuQuest — 관리자용 학생 개인 현황 (요약 카드 · 진도 도넛 · 과목별 진도 · 출석 · 학습 추이 · 활동)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-student">
    <router-link to="/dashboard" class="sq-student__back">
      <i class="bi bi-arrow-left" aria-hidden="true"></i> 전체 학생 현황
    </router-link>

    <p v-if="loading" class="sq-student__status">불러오는 중...</p>
    <p v-else-if="errorMessage" class="sq-student__error" role="alert">{{ errorMessage }}</p>

    <template v-else>
      <!-- 프로필 -->
      <section class="sq-card sq-profile-card">
        <div class="sq-profile-card__avatar" aria-hidden="true">{{ profile.name.slice(0, 1) }}</div>
        <div class="sq-profile-card__info">
          <h1 class="sq-profile-card__name">
            {{ profile.name }}
            <span class="sq-profile-card__id">{{ profile.username }}</span>
          </h1>
          <ul class="sq-profile-card__meta">
            <li><i class="bi bi-envelope" aria-hidden="true"></i> {{ profile.email }}</li>
            <li><i class="bi bi-phone" aria-hidden="true"></i> {{ maskPhone(profile.phone) }}</li>
            <li><i class="bi bi-person-badge" aria-hidden="true"></i> 닉네임 {{ profile.nickname || "-" }}</li>
            <li><i class="bi bi-calendar-plus" aria-hidden="true"></i> 가입 {{ formatDate(profile.createdAt) }}</li>
          </ul>
        </div>
        <div class="sq-profile-card__badges">
          <span class="sq-status" :class="`sq-status--${STATUS_TONE[profile.status]}`">{{ profile.status }}</span>
          <span class="sq-level">Lv.{{ summary.level }}</span>
        </div>
      </section>

      <!-- 요약 카드 (8개, 동일 형식) -->
      <section class="sq-stat-grid" aria-label="학습 요약">
        <article v-for="card in statCards" :key="card.key" class="sq-card sq-stat">
          <div class="sq-stat__head">
            <span class="sq-stat__label">{{ card.label }}</span>
            <i class="bi sq-stat__icon" :class="card.icon" aria-hidden="true"></i>
          </div>
          <span class="sq-stat__value" :class="{ 'sq-stat__value--danger': card.danger }">{{ card.value }}</span>
          <div
            v-if="card.bar !== undefined"
            class="sq-bar"
            role="progressbar"
            :aria-valuenow="card.bar"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="card.label"
          >
            <div class="sq-bar__fill" :style="{ width: card.bar + '%' }"></div>
          </div>
          <span class="sq-stat__sub">{{ card.sub }}</span>
        </article>
      </section>

      <!-- 진도 그래프 -->
      <section class="sq-chart-grid sq-chart-grid--progress">
        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">전체 진도</h2>
          <DonutChart
            :segments="[{ key: 'done', value: summary.completedSteps, tone: 'accent' }]"
            :total="summary.totalSteps || 1"
            :center="`${summary.percent}%`"
            :sub="`${summary.completedSteps}/${summary.totalSteps} 단계`"
            :aria-label="`전체 진도 ${summary.percent}%`"
          />
          <p class="sq-panel__foot">수강 {{ summary.enrolledCourses }}과목 기준</p>
        </article>

        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">과목별 진도율</h2>
          <ul class="sq-course-bars">
            <li v-for="course in courses" :key="course.slug" class="sq-course-bar">
              <span class="sq-course-bar__name">
                <span class="sq-badge" :class="`sq-badge--${DIFFICULTY_TONE[course.difficulty]}`">{{ course.difficulty }}</span>
                {{ course.title }}
              </span>
              <template v-if="course.enrolled">
                <div class="sq-bar">
                  <div class="sq-bar__fill" :style="{ width: course.percent + '%' }"></div>
                </div>
                <span class="sq-course-bar__value">{{ course.percent }}%</span>
              </template>
              <template v-else>
                <span class="sq-course-bar__none">미수강</span>
                <span></span>
              </template>
            </li>
          </ul>
        </article>

        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">단계별 완료</h2>
          <DonutChart
            :segments="stepSegments"
            :total="stepTotals.enrolled * 3 || 1"
            :center="`${summary.completedSteps}`"
            sub="완료 단계"
            aria-label="단계별 완료 수"
          />
          <ul class="sq-legend">
            <li v-for="seg in stepSegments" :key="seg.key">
              <span class="sq-legend__dot" :class="`sq-legend__dot--${seg.tone}`"></span>
              {{ seg.label }} {{ seg.value }}/{{ stepTotals.enrolled }}
            </li>
          </ul>
        </article>
      </section>

      <!-- 출석 · 학습 추이 · 포인트 경로 -->
      <section class="sq-chart-grid sq-chart-grid--middle">
        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">출석 체크판</h2>
          <ol class="sq-attendance">
            <li
              v-for="day in attendance"
              :key="day.day"
              class="sq-attendance__cell"
              :class="{
                'sq-attendance__cell--done': day.state === 'claimed',
                'sq-attendance__cell--bonus': day.bonus,
              }"
              :title="day.state === 'claimed' ? `${day.day}일차 +${day.amount}P` : `${day.day}일차 미출석`"
            >
              <span class="sq-attendance__day">{{ day.day }}</span>
              <span v-if="day.state === 'claimed'" class="sq-attendance__amount">+{{ day.amount }}</span>
              <i v-else-if="day.bonus" class="bi bi-star" aria-hidden="true"></i>
            </li>
          </ol>
          <p class="sq-panel__foot">
            {{ summary.attendanceDays }}/{{ summary.attendanceBoardDays }}일 출석 · 출석 포인트 {{ attendancePoints.toLocaleString() }}P
          </p>
        </article>

        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">주간 학습 활동 <span class="sq-panel__hint">(완료 단계 수)</span></h2>
          <svg class="sq-trend" viewBox="0 0 320 140" role="img" :aria-label="trendLabel">
            <line x1="24" y1="112" x2="312" y2="112" class="sq-trend__axis" />
            <g v-for="(w, i) in weeklyBars" :key="w.weekStart">
              <rect
                :x="w.x"
                :y="w.y"
                :width="w.width"
                :height="w.height"
                rx="3"
                class="sq-trend__bar"
                :class="{ 'sq-trend__bar--current': i === weeklyBars.length - 1 }"
              />
              <text v-if="w.count" :x="w.x + w.width / 2" :y="w.y - 4" text-anchor="middle" class="sq-trend__value">{{ w.count }}</text>
              <text :x="w.x + w.width / 2" y="128" text-anchor="middle" class="sq-trend__label">{{ w.label }}</text>
            </g>
          </svg>
          <p class="sq-panel__foot">최근 {{ weekly.length }}주 · 이번 주 {{ weekly.at(-1)?.count ?? 0 }}단계</p>
        </article>

        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">포인트 획득 경로</h2>
          <template v-if="pointSegments.length">
            <DonutChart
              :segments="pointSegments"
              :center="earnedPoints.toLocaleString()"
              sub="누적 적립 P"
              aria-label="포인트 획득 경로"
            />
            <ul class="sq-legend">
              <li v-for="seg in pointSegments" :key="seg.key">
                <span class="sq-legend__dot" :class="`sq-legend__dot--${seg.tone}`"></span>
                {{ seg.label }} {{ seg.value.toLocaleString() }}P
              </li>
            </ul>
          </template>
          <p v-else class="sq-student__status">적립된 포인트가 없습니다.</p>
        </article>
      </section>

      <!-- 단계 완료 날짜 · 최근 활동 -->
      <section class="sq-chart-grid sq-chart-grid--bottom">
        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">과목별 단계 완료 날짜</h2>
          <p v-if="!enrolledCourses.length" class="sq-student__status">수강 중인 과목이 없습니다.</p>
          <div v-else class="sq-table-wrap">
            <table class="sq-table">
              <thead>
                <tr>
                  <th>과목</th>
                  <th>수강 시작</th>
                  <th v-for="key in STEP_KEYS" :key="key">{{ STEP_LABELS[key] }}</th>
                  <th>진도</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="course in enrolledCourses" :key="course.slug">
                  <td>
                    <span class="sq-badge" :class="`sq-badge--${DIFFICULTY_TONE[course.difficulty]}`">{{ course.difficulty }}</span>
                    {{ course.title }}
                  </td>
                  <td>{{ formatDate(course.enrolledAt) }}</td>
                  <td v-for="key in STEP_KEYS" :key="key">
                    <span v-if="course.steps[key]" class="sq-step-done">
                      <i class="bi bi-check-circle-fill" aria-hidden="true"></i> {{ formatDate(course.steps[key]) }}
                    </span>
                    <span v-else class="sq-muted">미완료</span>
                  </td>
                  <td class="sq-table__percent">{{ course.percent }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="sq-card sq-panel">
          <h2 class="sq-panel__title">최근 활동</h2>
          <p v-if="!recent.length" class="sq-student__status">활동 기록이 없습니다.</p>
          <ol v-else class="sq-timeline">
            <li v-for="(ev, i) in recent" :key="i" class="sq-timeline__item">
              <i class="bi sq-timeline__icon" :class="EVENT_ICON[ev.type]" aria-hidden="true"></i>
              <span class="sq-timeline__text">{{ ev.text }}</span>
              <span class="sq-timeline__time">{{ formatDateTime(ev.at) }}</span>
            </li>
          </ol>
        </article>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import DonutChart from "@/components/admin/DonutChart.vue";

const STEP_KEYS = ["concept", "practice", "defense"];
const STEP_LABELS = { concept: "개념 학습", practice: "실습 성공", defense: "퀴즈 통과" };
const STEP_TONES = { concept: "success", practice: "accent", defense: "warning" };
const STATUS_TONE = { 진행중: "progress", 정체: "stalled", 완료: "done", 미시작: "none" };
const DIFFICULTY_TONE = { 초급: "success", 중급: "warning", 고급: "danger" };
const SOURCE_TONES = ["accent", "success", "warning", "danger", "muted"];
const EVENT_ICON = { step: "bi-check2-circle", point: "bi-coin", xp: "bi-stars" };

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const data = ref(null);

const profile = computed(() => data.value?.profile ?? {});
const summary = computed(() => data.value?.summary ?? {});
const courses = computed(() => data.value?.courses ?? []);
const stepTotals = computed(() => data.value?.stepTotals ?? { enrolled: 0 });
const attendance = computed(() => data.value?.attendance ?? []);
const weekly = computed(() => data.value?.weekly ?? []);
const recent = computed(() => data.value?.recent ?? []);
const enrolledCourses = computed(() => courses.value.filter((c) => c.enrolled));

const attendancePoints = computed(() =>
  attendance.value.filter((d) => d.state === "claimed").reduce((sum, d) => sum + (d.amount || 0), 0)
);

// 요약 카드 8개 — 모두 [라벨 · 아이콘 · 값 · (진행바) · 보조문구] 형식
const statCards = computed(() => {
  const s = summary.value;
  const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
  return [
    {
      key: "percent", label: "전체 진도율", icon: "bi-graph-up-arrow",
      value: `${s.percent}%`, bar: s.percent, sub: `단계 ${s.completedSteps}/${s.totalSteps} 완료`,
    },
    {
      key: "points", label: "보유 포인트", icon: "bi-coin",
      value: `${(s.points ?? 0).toLocaleString()}P`, sub: `미수령 보상 ${s.pendingRewards}건`,
    },
    {
      key: "attendance", label: "출석일", icon: "bi-calendar-check",
      value: `${s.attendanceDays} / ${s.attendanceBoardDays}일`,
      bar: pct(s.attendanceDays, s.attendanceBoardDays), sub: `출석 포인트 ${attendancePoints.value.toLocaleString()}P`,
    },
    {
      key: "courses", label: "완료 과목", icon: "bi-trophy",
      value: `${s.completedCourses} / ${s.enrolledCourses}`,
      bar: pct(s.completedCourses, s.enrolledCourses), sub: `수강 ${s.enrolledCourses} · 전체 ${s.totalCourses}과목`,
    },
    {
      key: "level", label: "레벨 · 경험치", icon: "bi-stars",
      value: `Lv.${s.level}`,
      bar: s.xpForNextLevel ? pct(s.currentXp, s.xpForNextLevel) : 100,
      sub: s.xpForNextLevel ? `${s.currentXp}/${s.xpForNextLevel} XP · 누적 ${s.totalXp}` : `최고 레벨 · 누적 ${s.totalXp} XP`,
    },
    {
      key: "practice", label: "실습 성공", icon: "bi-terminal",
      value: `${s.practiceSuccess} / ${s.enrolledCourses}`,
      bar: pct(s.practiceSuccess, s.enrolledCourses), sub: "수강 과목 중 실습 성공",
    },
    {
      key: "quiz", label: "퀴즈 통과", icon: "bi-patch-check",
      value: `${s.quizPassed} / ${s.enrolledCourses}`,
      bar: pct(s.quizPassed, s.enrolledCourses), sub: "수강 과목 중 퀴즈 통과",
    },
    {
      key: "activity", label: "학습한 날", icon: "bi-clock-history",
      value: `${s.learningDays}일`,
      sub: `마지막 활동 ${relativeDate(s.lastActivity)}`,
      danger: profile.value.status === "정체",
    },
  ];
});

const stepSegments = computed(() =>
  STEP_KEYS.map((key) => ({ key, label: STEP_LABELS[key], value: stepTotals.value[key] || 0, tone: STEP_TONES[key] }))
);

const pointSegments = computed(() =>
  (data.value?.pointsBySource ?? []).map((p, i) => ({
    key: p.source,
    label: p.label,
    value: p.amount,
    tone: SOURCE_TONES[i % SOURCE_TONES.length],
  }))
);
const earnedPoints = computed(() => pointSegments.value.reduce((sum, p) => sum + p.value, 0));

// 주간 막대 그래프 좌표 계산 (SVG 320x140, 막대 영역 높이 90)
const weeklyBars = computed(() => {
  const list = weekly.value;
  if (!list.length) return [];
  const max = Math.max(1, ...list.map((w) => w.count));
  const slot = 288 / list.length;
  const width = Math.min(26, slot * 0.6);
  return list.map((w, i) => {
    const height = Math.round((w.count / max) * 90);
    const [, m, d] = w.weekStart.split("-");
    return {
      ...w,
      x: 24 + slot * i + (slot - width) / 2,
      y: 112 - height,
      width,
      height: Math.max(height, w.count ? 2 : 0),
      label: `${Number(m)}/${Number(d)}`,
    };
  });
});
const trendLabel = computed(() => weekly.value.map((w) => `${w.weekStart} ${w.count}단계`).join(", "));

function maskPhone(phone) {
  if (!phone) return "-";
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 10) return phone;
  return `${digits.slice(0, 3)}-****-${digits.slice(-4)}`;
}

function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function formatDateTime(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function relativeDate(iso) {
  if (!iso) return "없음";
  const start = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((start(new Date()) - start(new Date(iso))) / 86400000);
  if (days <= 0) return "오늘";
  if (days === 1) return "어제";
  return `${days}일 전`;
}

async function load() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const res = await client.get(`/admin/students/${encodeURIComponent(route.params.id)}`);
    data.value = res.data;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "학생 정보를 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => route.params.id, (id) => id && load());
</script>

<style scoped>
.sq-student {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-student__back {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--sq-text-link);
  text-decoration: none;
}

.sq-student__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-student__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

/* 카드 공통 */
.sq-card {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
  min-width: 0;
}

/* 프로필 */
.sq-profile-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sq-profile-card__avatar {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 22px;
  font-weight: 700;
}

.sq-profile-card__info {
  flex: 1;
  min-width: 0;
}

.sq-profile-card__name {
  margin: 0;
  font-size: 24px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-profile-card__id {
  margin-left: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--sq-text-sub);
}

.sq-profile-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin: 6px 0 0;
  padding: 0;
  list-style: none;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-profile-card__badges {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.sq-level {
  padding: 3px 10px;
  border-radius: var(--sq-radius-none);
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
  font-size: 12px;
  font-weight: 700;
}

.sq-status {
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

/* 요약 카드 */
.sq-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sq-card-gap);
}

.sq-stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sq-stat__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sq-stat__label {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-stat__icon {
  font-size: 18px;
  color: var(--sq-color-accent);
}

.sq-stat__value {
  font-size: 26px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-stat__value--danger {
  color: var(--sq-badge-absent-text);
}

.sq-stat__sub {
  font-size: 12px;
  color: var(--sq-text-sub);
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

/* 그래프 영역 */
.sq-chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--sq-card-gap);
}

.sq-chart-grid--progress {
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.4fr) minmax(0, 0.8fr);
}

.sq-chart-grid--bottom {
  grid-template-columns: minmax(0, 1.8fr) minmax(0, 1fr);
}

.sq-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sq-panel__title {
  margin: 0;
  font-size: 16px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-panel__hint {
  font-size: 12px;
  font-weight: 500;
  color: var(--sq-text-sub);
}

.sq-panel__foot {
  margin: auto 0 0;
  font-size: 12px;
  color: var(--sq-text-sub);
  text-align: center;
}

/* 난이도 배지 */
.sq-badge {
  display: inline-flex;
  padding: 2px 7px;
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

/* 과목별 막대 */
.sq-course-bars {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-course-bar {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) 40px;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--sq-text-main);
}

.sq-course-bar__name {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sq-course-bar__value {
  font-weight: 700;
  text-align: right;
}

.sq-course-bar__none {
  font-size: 12px;
  color: var(--sq-text-sub);
}

/* 범례 */
.sq-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px 12px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
  color: var(--sq-text-sub);
}

.sq-legend__dot {
  display: inline-block;
  width: 9px;
  height: 9px;
  margin-right: 3px;
  border-radius: 2px;
}

.sq-legend__dot--accent {
  background: var(--sq-color-accent);
}

.sq-legend__dot--success {
  background: var(--sq-badge-submitted-text);
}

.sq-legend__dot--warning {
  background: var(--sq-badge-dday-text);
}

.sq-legend__dot--danger {
  background: var(--sq-badge-absent-text);
}

.sq-legend__dot--muted {
  background: var(--sq-text-sub);
}

/* 출석 체크판 */
.sq-attendance {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-attendance__cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  font-size: 11px;
  color: var(--sq-text-sub);
}

.sq-attendance__cell--bonus {
  border-color: var(--sq-badge-dday-text);
}

.sq-attendance__cell--done {
  border-color: var(--sq-color-accent);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
}

.sq-attendance__day {
  font-weight: 700;
}

.sq-attendance__amount {
  font-size: 10px;
}

/* 주간 추이 */
.sq-trend {
  width: 100%;
  height: auto;
}

.sq-trend__axis {
  stroke: var(--sq-card-border);
}

.sq-trend__bar {
  fill: var(--sq-color-accent-subtle);
}

.sq-trend__bar--current {
  fill: var(--sq-color-accent);
}

.sq-trend__value {
  font-size: 11px;
  font-weight: 700;
  fill: var(--sq-text-main);
}

.sq-trend__label {
  font-size: 10px;
  fill: var(--sq-text-sub);
}

/* 단계 완료 표 */
.sq-table-wrap {
  overflow-x: auto;
}

.sq-table {
  width: 100%;
  border-collapse: collapse;
}

.sq-table th,
.sq-table td {
  padding: 9px 8px;
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

.sq-table__percent {
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-step-done {
  color: var(--sq-badge-submitted-text);
  font-weight: 600;
}

.sq-muted {
  color: var(--sq-text-sub);
}

/* 최근 활동 */
.sq-timeline {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}

.sq-timeline__item {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 13px;
}

.sq-timeline__item:last-child {
  border-bottom: none;
}

.sq-timeline__icon {
  color: var(--sq-color-accent);
}

.sq-timeline__text {
  color: var(--sq-text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sq-timeline__time {
  font-size: 12px;
  color: var(--sq-text-sub);
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .sq-bar__fill {
    transition: none;
  }
}

/* 반응형 */
@media (max-width: 1100px) {
  .sq-chart-grid,
  .sq-chart-grid--progress,
  .sq-chart-grid--bottom {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  /* 2열일 때 빈칸이 생기지 않도록 넓은 항목을 한 줄 전체로 배치 */
  .sq-chart-grid--progress > :nth-child(2) {
    grid-column: 1 / -1;
    order: -1;
  }

  .sq-chart-grid--middle > :nth-child(3) {
    grid-column: 1 / -1;
  }

  .sq-chart-grid--bottom > * {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .sq-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sq-chart-grid,
  .sq-chart-grid--progress,
  .sq-chart-grid--bottom {
    grid-template-columns: minmax(0, 1fr);
  }

  .sq-profile-card {
    flex-wrap: wrap;
  }

  .sq-course-bar {
    grid-template-columns: minmax(0, 1fr) 40px;
  }

  .sq-course-bar .sq-bar {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}
</style>
