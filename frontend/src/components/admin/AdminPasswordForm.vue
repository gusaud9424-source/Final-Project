<!--
  SecuQuest — 관리자 비밀번호 변경
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <form class="sq-admin-pw" novalidate @submit.prevent="submit">
    <h2 class="sq-admin-pw__title">비밀번호 변경</h2>
    <p class="sq-admin-pw__desc">현재 비밀번호를 확인한 뒤 새 비밀번호(8자 이상)로 변경합니다.</p>

    <label class="sq-admin-pw__label" for="sq-admin-pw-current">현재 비밀번호</label>
    <input
      id="sq-admin-pw-current"
      v-model="form.current"
      type="password"
      class="sq-admin-pw__input"
      autocomplete="current-password"
      required
    />

    <label class="sq-admin-pw__label" for="sq-admin-pw-new">새 비밀번호</label>
    <input
      id="sq-admin-pw-new"
      v-model="form.next"
      type="password"
      class="sq-admin-pw__input"
      autocomplete="new-password"
      minlength="8"
      required
    />

    <label class="sq-admin-pw__label" for="sq-admin-pw-confirm">새 비밀번호 확인</label>
    <input
      id="sq-admin-pw-confirm"
      v-model="form.confirm"
      type="password"
      class="sq-admin-pw__input"
      autocomplete="new-password"
      required
    />

    <p v-if="errorMessage" class="sq-admin-pw__error" role="alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="sq-admin-pw__success" role="status">{{ successMessage }}</p>

    <button type="submit" class="sq-admin-pw__btn" :disabled="submitting">
      {{ submitting ? "변경 중..." : "비밀번호 변경" }}
    </button>
  </form>
</template>

<script setup>
import { reactive, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const MIN_LENGTH = 8;

const form = reactive({ current: "", next: "", confirm: "" });
const submitting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

// 클라이언트 1차 검증 (최종 검증은 서버)
function validate() {
  if (!form.current || !form.next || !form.confirm) return "모든 항목을 입력하세요.";
  if (form.next.length < MIN_LENGTH) return `새 비밀번호는 ${MIN_LENGTH}자 이상이어야 합니다.`;
  if (form.next !== form.confirm) return "새 비밀번호 확인이 일치하지 않습니다.";
  if (form.next === form.current) return "새 비밀번호가 현재 비밀번호와 같습니다.";
  return "";
}

async function submit() {
  errorMessage.value = "";
  successMessage.value = "";
  const invalid = validate();
  if (invalid) {
    errorMessage.value = invalid;
    return;
  }

  submitting.value = true;
  try {
    const { data } = await client.post("/admin/password", {
      current_password: form.current,
      new_password: form.next,
    });
    successMessage.value = data.message || "비밀번호가 변경되었습니다.";
    form.current = "";
    form.next = "";
    form.confirm = "";
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "비밀번호 변경에 실패했습니다.");
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.sq-admin-pw {
  display: flex;
  flex-direction: column;
  max-width: 480px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-admin-pw__title {
  margin: 0;
  font-size: 18px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-admin-pw__desc {
  margin: 6px 0 20px;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-admin-pw__label {
  margin: 12px 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-text-main);
}

.sq-admin-pw__input {
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-size: 14px;
}

.sq-admin-pw__input:focus {
  outline: none;
  border-color: var(--sq-color-accent);
}

.sq-admin-pw__error {
  margin: 14px 0 0;
  font-size: 13px;
  color: var(--sq-badge-absent-text);
}

.sq-admin-pw__success {
  margin: 14px 0 0;
  font-size: 13px;
  color: var(--sq-badge-submitted-text);
}

.sq-admin-pw__btn {
  margin-top: 20px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.sq-admin-pw__btn:hover:not(:disabled) {
  background: var(--sq-color-accent-hover);
}

.sq-admin-pw__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
