import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes = [
  { path: "/", redirect: "/dashboard" },
  {
    path: "/login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true, showHeader: false },
  },
  {
    path: "/find-id",
    component: () => import("@/views/FindIdView.vue"),
    meta: { public: true, showHeader: false },
  },
  {
    path: "/find-password",
    component: () => import("@/views/FindPasswordView.vue"),
    meta: { public: true, showHeader: false },
  },
  { path: "/dashboard", component: () => import("@/views/DashboardView.vue") },
  { path: "/dashboard/courses/:slug", component: () => import("@/views/CourseDetailView.vue") },
  { path: "/chapters", component: () => import("@/views/ChapterSelectView.vue") },
  { path: "/chapters/:id", component: () => import("@/views/ChapterDetailView.vue") },
  { path: "/enroll", component: () => import("@/views/EnrollView.vue") },
  {
    path: "/admin",
    component: () => import("@/views/AdminView.vue"),
    meta: { requiresAdmin: true },
  },
  { path: "/resources", component: () => import("@/views/ResourcesView.vue") },
  { path: "/:pathMatch(.*)*", component: () => import("@/views/NotFoundView.vue") },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  if (!authStore.initialized) {
    await authStore.fetchMe();
  }

  if (!to.meta.public && !authStore.isAuthenticated) {
    return "/login";
  }
  if (to.path === "/login" && authStore.isAuthenticated) {
    return "/dashboard";
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return "/dashboard";
  }
  return true;
});

export default router;
