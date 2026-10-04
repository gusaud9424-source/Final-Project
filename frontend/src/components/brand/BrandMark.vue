<template>
  <!-- CSS3 로고형 방패 프레임 + 헤더 타이틀과 동일한 폰트(Pretendard)의 S 컷아웃 -->
  <svg class="sq-brand-mark" width="42" height="48" viewBox="30 0 452 512" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SecuQuest 로고">
    <defs>
      <!-- 마스크: 흰색=보임, 검정=투명(S 글자 부분을 뚫어 배경이 보이게 함) -->
      <mask :id="maskId" maskUnits="userSpaceOnUse" x="30" y="0" width="452" height="512">
        <rect x="30" y="0" width="452" height="512" fill="white" />
        <text
          class="sq-brand-mark__letter"
          x="256"
          y="372"
          text-anchor="middle"
          fill="black"
        >S</text>
      </mask>
    </defs>
    <path
      fill="currentColor"
      :mask="`url(#${maskId})`"
      d="M71 460 L30 0 L482 0 L441 460 L256 512 Z"
    />
  </svg>
</template>

<script setup>
import { useId } from "vue";

// 인스턴스마다 고유한 마스크 id (같은 페이지에 여러 개 렌더링되어도 충돌 방지)
const maskId = `sq-brand-mask-${useId()}`;
</script>

<style scoped>
.sq-brand-mark {
  color: var(--sq-color-accent);
}

/* 헤더 타이틀(SecuQuest)과 동일한 폰트 · 굵기 */
.sq-brand-mark__letter {
  font-family: var(--sq-font-family);
  font-weight: 700;
  font-size: 360px;
}
</style>
