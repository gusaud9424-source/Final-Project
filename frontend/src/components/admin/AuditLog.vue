<!--
  SecuQuest — 관리자 감사 로그 (DB 보관된 관리자 · 계정 보안 작업 기록 조회)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-audit">
    <div class="sq-audit__toolbar">
      <form class="sq-audit__search" role="search" @submit.prevent="search">
        <select v-model="action" class="sq-audit__select" aria-label="동작 선택" @change="search">
          <option value="">전체 동작</option>
          <option v-for="a in actions" :key="a.key" :value="a.key">{{ a.label }}</option>
        </select>
        <input
          v-model="keyword"
          type="search"
          class="sq-audit__input"
          placeholder="아이디 검색 (행위자 · 대상)"
          aria-label="아이디 검색"
          maxlength="80"
        />
        <button type="submit" class="sq-audit__btn">검색</button>
      </form>
      <span class="sq-audit__count">총 {{ total }}건</span>
    </div>

    <p class="sq-audit__hint">
      <i class="bi bi-shield-check" aria-hidden="true"></i>
      서버 로그와 별도로 DB 에 보관됩니다. 회원이 삭제돼도 기록은 남고, 개인정보 값(이메일 · 번호 · 비밀번호)은 저장하지 않습니다.
    </p>

    <p v-if="errorMessage" class="sq-audit__error" role="alert">{{ errorMessage }}</p>
    <p v-if="loading" class="sq-audit__status">불러오는 중...</p>
    <p v-else-if="!items.length" class="sq-audit__status">기록이 없습니다.</p>

    <div v-else class="sq-audit__table-wrap">
      <table class="sq-audit__table">
        <thead>
          <tr>
            <th>일시</th>
            <th>행위자</th>
            <th>동작</th>
            <th>대상</th>
            <th>상세</th>
            <th>IP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.createdAt }}</td>
            <td>
              {{ item.actor || "-" }}
              <span v-if="item.actorRole === 'admin'" class="sq-audit__role">관리자</span>
            </td>
            <td>
              <span class="sq-audit__action" :class="{ 'sq-audit__action--danger': item.action === 'delete_user' }">
                {{ item.actionLabel }}
              </span>
            </td>
            <td>{{ item.target || "-" }}</td>
            <td>{{ formatDetail(item.detail) }}</td>
            <td class="sq-audit__ip">{{ item.ip || "-" }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="totalPages > 1" class="sq-audit__pager">
      <button type="button" class="sq-audit__btn sq-audit__btn--outline" :disabled="page <= 1 || loading" @click="go(page - 1)">
        이전
      </button>
      <span class="sq-audit__page">{{ page }} / {{ totalPages }}</span>
      <button
        type="button"
        class="sq-audit__btn sq-audit__btn--outline"
        :disabled="page >= totalPages || loading"
        @click="go(page + 1)"
      >
        다음
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

// 상세(detail) 값을 읽기 쉬운 한국어로
const FIELD_LABELS = { name: "이름", nickname: "닉네임", email: "이메일", phone: "휴대폰" };
const VIA_LABELS = { email: "이메일 인증", sms: "휴대폰 인증" };

const items = ref([]);
const actions = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(50);
const action = ref("");
const keyword = ref("");
const loading = ref(false);
const errorMessage = ref("");

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

function formatDetail(detail) {
  if (!detail) return "-";
  if (detail.startsWith("fields=")) {
    return detail
      .slice(7)
      .split(",")
      .map((f) => FIELD_LABELS[f] || f)
      .join(" · ");
  }
  if (detail.startsWith("via=")) return VIA_LABELS[detail.slice(4)] || detail;
  return detail;
}

async function fetchLogs() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await client.get("/admin/audit-logs", {
      params: { page: page.value, action: action.value || undefined, q: keyword.value.trim() || undefined },
    });
    items.value = data.items;
    actions.value = data.actions;
    total.value = data.total;
    pageSize.value = data.pageSize;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "감사 로그를 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
}

function search() {
  page.value = 1;
  fetchLogs();
}

function go(next) {
  page.value = next;
  fetchLogs();
}

onMounted(fetchLogs);
</script>

<style scoped>
.sq-audit {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-audit__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.sq-audit__search {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 480px;
  max-width: 640px;
}

.sq-audit__select,
.sq-audit__input {
  padding: 9px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-size: 14px;
  font-family: var(--sq-font-family);
}

.sq-audit__input {
  flex: 1;
  min-width: 0;
}

.sq-audit__select:focus,
.sq-audit__input:focus {
  outline: none;
  border-color: var(--sq-color-accent);
}

.sq-audit__count,
.sq-audit__page {
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-audit__hint {
  margin: 0;
  padding: 10px 12px;
  background: var(--sq-color-accent-subtle);
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-audit__btn {
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

.sq-audit__btn:hover:not(:disabled) {
  background: var(--sq-color-accent-hover);
  border-color: var(--sq-color-accent-hover);
}

.sq-audit__btn--outline {
  background: transparent;
  color: var(--sq-color-accent);
}

.sq-audit__btn--outline:hover:not(:disabled) {
  background: var(--sq-color-accent-subtle);
  border-color: var(--sq-color-accent);
}

.sq-audit__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-audit__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-audit__error {
  margin: 0;
  font-size: 13px;
  color: var(--sq-badge-absent-text);
}

.sq-audit__table-wrap {
  overflow-x: auto;
}

.sq-audit__table {
  width: 100%;
  border-collapse: collapse;
}

.sq-audit__table th,
.sq-audit__table td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 14px;
  color: var(--sq-text-main);
  white-space: nowrap;
}

.sq-audit__table th {
  font-size: 13px;
  color: var(--sq-text-sub);
  font-weight: 600;
}

.sq-audit__role {
  margin-left: 4px;
  padding: 2px 6px;
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
  font-size: 11px;
  font-weight: 600;
}

.sq-audit__action {
  padding: 3px 8px;
  background: var(--sq-badge-submitted-bg);
  color: var(--sq-badge-submitted-text);
  font-size: 12px;
  font-weight: 600;
}

.sq-audit__action--danger {
  background: var(--sq-badge-absent-bg);
  color: var(--sq-badge-absent-text);
}

.sq-audit__ip {
  font-family: monospace;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-audit__pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
</style>
