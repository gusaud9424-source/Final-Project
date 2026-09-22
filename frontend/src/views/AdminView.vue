<!--
  SecuQuest — 관리자
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-admin">
    <div class="sq-admin__head">
      <h1 class="sq-admin__title">관리자</h1>
      <p class="sq-admin__subtitle">전체 학생의 챕터별 진도를 확인하세요.</p>
    </div>

    <StudentsOverview />
  </div>
</template>

<script setup>
import StudentsOverview from "@/components/dashboard/StudentsOverview.vue";
</script>

<style scoped>
.sq-admin {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-admin__title {
  font-size: 32px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
  margin: 0;
}

.sq-admin__subtitle {
  font-size: 14px;
  color: var(--sq-text-sub);
  margin: 6px 0 0;
}
</style>
