import { defineStore } from "pinia";
import { ref, computed } from "vue";
import client, { resetCsrfToken } from "@/api/client";

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const initialized = ref(false);

  const isAuthenticated = computed(() => !!user.value);
  const isAdmin = computed(() => user.value?.role === "admin");

  async function fetchMe() {
    try {
      const { data } = await client.get("/auth/me");
      user.value = data;
    } catch {
      user.value = null;
    } finally {
      initialized.value = true;
    }
  }

  async function login(username, password, role) {
    try {
      const { data } = await client.post("/auth/login", { username, password, role });
      user.value = data;
      resetCsrfToken();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || "로그인에 실패했습니다.",
      };
    }
  }

  async function logout() {
    try {
      await client.post("/auth/logout");
    } finally {
      user.value = null;
      resetCsrfToken();
    }
  }

  return { user, initialized, isAuthenticated, isAdmin, fetchMe, login, logout };
});
