<!--
  SecuQuest — 과목 상세 (스텁, Phase 3에서 구현 예정)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-view-stub">
    <router-link to="/dashboard">← 내 강의실로 돌아가기</router-link>
    <h2>CourseDetailView (stub) — 과목 slug: {{ $route.params.slug }}</h2>
    <p>경로: {{ $route.fullPath }}</p>
  </div>
</template>

<script setup></script>
