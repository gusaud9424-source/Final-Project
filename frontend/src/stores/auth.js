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

  // 회원가입 mock (UI First: 백엔드 signup API 연동 전까지 사용)
  async function signup({ username }) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return { success: true, message: `${username} 님, 회원가입이 완료되었습니다. (mock)` };
  }

  // 휴대폰 아이디 찾기 mock (백엔드 find-id SMS API 미구현)
  async function sendFindIdPhoneCode(phone) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return { success: true, message: `${phone} 으로 인증코드를 발송했습니다. (mock)` };
  }

  // eslint-disable-next-line no-unused-vars -- 실제 API 연동 시 사용할 인자
  async function verifyFindIdPhoneCode(phone, code) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return { success: true, message: "휴대폰 아이디 찾기는 백엔드 연동 전입니다. (mock)" };
  }

  return {
    user,
    initialized,
    isAuthenticated,
    isAdmin,
    fetchMe,
    login,
    logout,
    signup,
    sendFindIdPhoneCode,
    verifyFindIdPhoneCode,
  };
});
