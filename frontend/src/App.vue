<template>
  <AppHeader v-if="route.meta.showHeader !== false" />
  <main class="sq-main">
    <router-view />
  </main>
  <AppFooter v-if="route.meta.showHeader !== false" />
</template>

<script setup>
import { useRoute } from "vue-router";
import AppHeader from "@/components/layout/AppHeader.vue";
import AppFooter from "@/components/layout/AppFooter.vue";

const route = useRoute();
</script>

<style scoped>
.sq-main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px var(--sq-page-padding-x);
}
</style>
