<template>
  <AppHeader />
  <main class="sq-main">
    <router-view />
  </main>
</template>

<script setup>
import AppHeader from "@/components/layout/AppHeader.vue";
</script>

<style scoped>
.sq-main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px var(--sq-page-padding-x);
}
</style>
