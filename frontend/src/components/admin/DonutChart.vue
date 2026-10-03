<!--
  SecuQuest — 도넛 차트 (SVG, 외부 라이브러리 없음)
  © 2026 5팀_Security Learning Platform
-->
<template>
  <figure class="sq-donut" :style="{ width: size + 'px' }">
    <svg :viewBox="`0 0 ${box} ${box}`" :width="size" :height="size" role="img" :aria-label="ariaLabel">
      <!-- 배경 트랙 -->
      <circle :cx="c" :cy="c" :r="r" fill="none" class="sq-donut__track" :stroke-width="thickness" />
      <!-- 조각 -->
      <circle
        v-for="seg in arcs"
        :key="seg.key"
        :cx="c"
        :cy="c"
        :r="r"
        fill="none"
        :class="`sq-donut__seg sq-donut__seg--${seg.tone}`"
        :stroke-width="thickness"
        :stroke-dasharray="`${seg.length} ${circumference}`"
        :stroke-dashoffset="-seg.offset"
        :transform="`rotate(-90 ${c} ${c})`"
      />
      <text :x="c" :y="sub ? c - 2 : c + 6" text-anchor="middle" class="sq-donut__center">{{ center }}</text>
      <text v-if="sub" :x="c" :y="c + 16" text-anchor="middle" class="sq-donut__sub">{{ sub }}</text>
    </svg>
  </figure>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  // [{ key, value, tone }] — tone: accent | success | warning | danger | muted
  segments: { type: Array, required: true },
  // 조각 합계의 기준값 (생략 시 조각 합계 = 100%)
  total: { type: Number, default: null },
  center: { type: String, default: "" },
  sub: { type: String, default: "" },
  size: { type: Number, default: 140 },
  thickness: { type: Number, default: 14 },
  ariaLabel: { type: String, default: "" },
});

const box = 120;
const c = box / 2;
const r = computed(() => c - props.thickness / 2 - 2);
const circumference = computed(() => 2 * Math.PI * r.value);

const arcs = computed(() => {
  const sum = props.segments.reduce((acc, s) => acc + Math.max(0, s.value), 0);
  const base = props.total ?? sum;
  if (!base) return [];
  let offset = 0;
  return props.segments
    .filter((s) => s.value > 0)
    .map((s) => {
      const length = (s.value / base) * circumference.value;
      const arc = { key: s.key, tone: s.tone || "accent", length, offset };
      offset += length;
      return arc;
    });
});
</script>

<style scoped>
.sq-donut {
  margin: 0 auto;
}

.sq-donut__track {
  stroke: var(--sq-card-border);
}

.sq-donut__seg {
  transition: stroke-dasharray 400ms ease;
}

.sq-donut__seg--accent {
  stroke: var(--sq-color-accent);
}

.sq-donut__seg--success {
  stroke: var(--sq-badge-submitted-text);
}

.sq-donut__seg--warning {
  stroke: var(--sq-badge-dday-text);
}

.sq-donut__seg--danger {
  stroke: var(--sq-badge-absent-text);
}

.sq-donut__seg--muted {
  stroke: var(--sq-text-sub);
}

.sq-donut__center {
  font-size: 22px;
  font-weight: 700;
  fill: var(--sq-text-main);
}

.sq-donut__sub {
  font-size: 11px;
  fill: var(--sq-text-sub);
}

@media (prefers-reduced-motion: reduce) {
  .sq-donut__seg {
    transition: none;
  }
}
</style>
