import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/dashboard",       component: () => import("@/views/DashboardView.vue") },
  { path: "/chapters",        component: () => import("@/views/ChapterSelectView.vue") },
  { path: "/chapters/:id",    component: () => import("@/views/ChapterDetailView.vue") },
  { path: "/admin",           component: () => import("@/views/AdminView.vue") },
  { path: "/resources",       component: () => import("@/views/ResourcesView.vue") },
  { path: "/:pathMatch(.*)*", component: () => import("@/views/NotFoundView.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
