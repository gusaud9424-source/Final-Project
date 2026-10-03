<!--
  SecuQuest — 관리자 회원관리 (목록 · 검색 · 임시 비밀번호 발급 · 삭제)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-members">
    <div class="sq-members__toolbar">
      <form class="sq-members__search" role="search" @submit.prevent="fetchUsers">
        <i class="bi bi-search" aria-hidden="true"></i>
        <input
          v-model="keyword"
          type="search"
          class="sq-members__search-input"
          placeholder="아이디 · 이름 · 이메일 검색"
          aria-label="회원 검색"
        />
        <button type="submit" class="sq-members__btn">검색</button>
      </form>
      <span class="sq-members__count">총 {{ users.length }}명</span>
    </div>

    <!-- 임시 비밀번호 발급 결과 (한 번만 표시) -->
    <div v-if="issued" class="sq-members__notice" role="status">
      <div>
        <strong>{{ issued.name }}({{ issued.username }})</strong> 님의 임시 비밀번호:
        <code class="sq-members__temp">{{ issued.tempPassword }}</code>
        <p class="sq-members__notice-sub">이 창을 닫으면 다시 볼 수 없습니다. 회원에게 전달 후 비밀번호 찾기로 변경하도록 안내하세요.</p>
      </div>
      <div class="sq-members__notice-actions">
        <button type="button" class="sq-members__btn sq-members__btn--outline" @click="copyTemp">
          <i class="bi bi-clipboard" aria-hidden="true"></i> {{ copied ? "복사됨" : "복사" }}
        </button>
        <button type="button" class="sq-members__icon-btn" aria-label="닫기" @click="issued = null">
          <i class="bi bi-x-lg" aria-hidden="true"></i>
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="sq-members__error" role="alert">{{ errorMessage }}</p>
    <p v-if="loading" class="sq-members__status">불러오는 중...</p>
    <p v-else-if="!users.length" class="sq-members__status">
      {{ searched ? "검색 결과가 없습니다." : "가입한 학생이 없습니다." }}
    </p>

    <div v-else class="sq-members__table-wrap">
      <table class="sq-members__table">
        <thead>
          <tr>
            <th>아이디</th>
            <th>이름</th>
            <th>닉네임</th>
            <th>이메일</th>
            <th>휴대폰</th>
            <th>수강</th>
            <th>포인트</th>
            <th>가입일</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.name }}</td>
            <td>{{ user.nickname || "-" }}</td>
            <td>{{ user.email }}</td>
            <td>{{ maskPhone(user.phone) }}</td>
            <td>{{ user.courseCount }}과목</td>
            <td>{{ user.points.toLocaleString() }}P</td>
            <td>{{ formatDate(user.createdAt) }}</td>
            <td>
              <div class="sq-members__actions">
                <button
                  type="button"
                  class="sq-members__btn sq-members__btn--outline"
                  :disabled="pending.has(user.id)"
                  @click="resetPassword(user)"
                >
                  임시 비밀번호
                </button>
                <button
                  type="button"
                  class="sq-members__btn sq-members__btn--danger"
                  :disabled="pending.has(user.id)"
                  @click="deleteUser(user)"
                >
                  삭제
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const users = ref([]);
const keyword = ref("");
const searched = ref(false);
const loading = ref(true);
const errorMessage = ref("");
const pending = reactive(new Set());
// 발급된 임시 비밀번호 { name, username, tempPassword }
const issued = ref(null);
const copied = ref(false);

async function fetchUsers() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const q = keyword.value.trim();
    const { data } = await client.get("/admin/users", { params: q ? { q } : {} });
    users.value = data.users;
    searched.value = Boolean(q);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "회원 목록을 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
}

async function resetPassword(user) {
  if (pending.has(user.id)) return;
  if (!window.confirm(`'${user.name}(${user.username})' 회원의 비밀번호를 임시 비밀번호로 초기화할까요?`)) return;

  errorMessage.value = "";
  pending.add(user.id);
  try {
    const { data } = await client.post(`/admin/users/${user.id}/reset-password`);
    issued.value = { name: user.name, username: user.username, tempPassword: data.tempPassword };
    copied.value = false;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "임시 비밀번호 발급에 실패했습니다.");
  } finally {
    pending.delete(user.id);
  }
}

async function deleteUser(user) {
  if (pending.has(user.id)) return;
  const ok = window.confirm(
    `'${user.name}(${user.username})' 회원을 삭제할까요?\n수강·진도·포인트 등 모든 기록이 함께 삭제되며 되돌릴 수 없습니다.`
  );
  if (!ok) return;

  errorMessage.value = "";
  pending.add(user.id);
  try {
    await client.delete(`/admin/users/${user.id}`);
    users.value = users.value.filter((u) => u.id !== user.id);
    if (issued.value?.username === user.username) issued.value = null;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "회원 삭제에 실패했습니다.");
  } finally {
    pending.delete(user.id);
  }
}

async function copyTemp() {
  try {
    await navigator.clipboard.writeText(issued.value.tempPassword);
    copied.value = true;
  } catch {
    copied.value = false;
  }
}

// 휴대폰 번호 가운데 자리 마스킹 (화면 노출 최소화)
function maskPhone(phone) {
  if (!phone) return "-";
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 10) return phone;
  return `${digits.slice(0, 3)}-****-${digits.slice(-4)}`;
}

function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

onMounted(fetchUsers);
</script>

<style scoped>
.sq-members {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-members__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.sq-members__search {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 360px;
  max-width: 480px;
  color: var(--sq-text-sub);
}

.sq-members__search-input {
  flex: 1;
  min-width: 0;
  padding: 9px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-size: 14px;
}

.sq-members__search-input:focus {
  outline: none;
  border-color: var(--sq-color-accent);
}

.sq-members__count {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-members__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}

.sq-members__btn:hover:not(:disabled) {
  background: var(--sq-color-accent-hover);
  border-color: var(--sq-color-accent-hover);
}

.sq-members__btn--outline {
  background: transparent;
  color: var(--sq-color-accent);
}

.sq-members__btn--outline:hover:not(:disabled) {
  background: var(--sq-color-accent-subtle);
  border-color: var(--sq-color-accent);
}

.sq-members__btn--danger {
  border-color: var(--sq-card-border);
  background: var(--sq-bg-card);
  color: var(--sq-text-sub);
}

.sq-members__btn--danger:hover:not(:disabled) {
  background: var(--sq-badge-absent-bg);
  border-color: var(--sq-badge-absent-text);
  color: var(--sq-badge-absent-text);
}

.sq-members__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-members__icon-btn {
  padding: 6px 8px;
  border: none;
  background: transparent;
  color: var(--sq-text-sub);
  cursor: pointer;
}

.sq-members__notice {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--sq-color-accent);
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent-subtle);
  font-size: 14px;
  color: var(--sq-text-main);
}

.sq-members__notice-sub {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-members__notice-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.sq-members__temp {
  padding: 2px 8px;
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-color-accent);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.sq-members__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-members__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

.sq-members__table-wrap {
  overflow-x: auto;
}

.sq-members__table {
  width: 100%;
  border-collapse: collapse;
}

.sq-members__table th,
.sq-members__table td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 14px;
  color: var(--sq-text-main);
  white-space: nowrap;
}

.sq-members__table th {
  font-size: 13px;
  color: var(--sq-text-sub);
  font-weight: 600;
}

.sq-members__actions {
  display: flex;
  gap: 6px;
}

@media (max-width: 768px) {
  .sq-members__notice {
    flex-direction: column;
  }
}
</style>
