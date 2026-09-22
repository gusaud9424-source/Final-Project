<!--
  SecuQuest — 로그인
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="SecuQuest 로그인">
    <div class="sq-auth-tabs" role="tablist">
      <button
        type="button"
        role="tab"
        class="sq-auth-tab"
        :class="{ 'sq-auth-tab--active': role === 'student' }"
        :aria-selected="role === 'student'"
        @click="role = 'student'"
      >
        일반사용자 로그인
      </button>
      <button
        type="button"
        role="tab"
        class="sq-auth-tab"
        :class="{ 'sq-auth-tab--active': role === 'admin' }"
        :aria-selected="role === 'admin'"
        @click="role = 'admin'"
      >
        관리자 로그인
      </button>
    </div>

    <form class="sq-auth-form" @submit.prevent="onSubmit">
      <label class="sq-auth-label" for="username">아이디</label>
      <input
        id="username"
        v-model="username"
        class="sq-auth-input"
        type="text"
        autocomplete="username"
        required
      />

      <label class="sq-auth-label" for="password">비밀번호</label>
      <input
        id="password"
        v-model="password"
        class="sq-auth-input"
        type="password"
        autocomplete="current-password"
        required
      />

      <p v-if="errorMessage" class="sq-auth-error">{{ errorMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="submitting">
        {{ submitting ? "로그인 중..." : "로그인" }}
      </button>
    </form>

    <template #links>
      <router-link to="/find-id">아이디 찾기</router-link>
      <span aria-hidden="true">·</span>
      <router-link to="/find-password">비밀번호 찾기</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import AuthCard from "@/components/auth/AuthCard.vue";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const role = ref("student");
const username = ref("");
const password = ref("");
const errorMessage = ref("");
const submitting = ref(false);

async function onSubmit() {
  errorMessage.value = "";
  submitting.value = true;
  const result = await authStore.login(username.value, password.value, role.value);
  submitting.value = false;

  if (result.success) {
    router.push("/dashboard");
  } else {
    errorMessage.value = result.message;
  }
}
</script>
