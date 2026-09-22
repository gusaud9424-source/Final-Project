<!--
  SecuQuest — 브랜드 마크(방패 + "S")
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <svg
    class="sq-brand-mark"
    width="40"
    height="48"
    viewBox="0 0 40 48"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="SecuQuest 로고"
  >
    <path
      d="M20 2 L36 8 L34 28 C34 38 27 44 20 46 C13 44 6 38 6 28 L4 8 Z"
      fill="currentColor"
    />
    <text
      x="20"
      y="27"
      font-family="Pretendard, -apple-system, sans-serif"
      font-size="20"
      font-weight="700"
      text-anchor="middle"
      dominant-baseline="middle"
    >
      S
    </text>
  </svg>
</template>

<style scoped>
.sq-brand-mark {
  color: var(--sq-color-accent);
}

.sq-brand-mark text {
  fill: var(--sq-color-on-accent);
}
</style>
