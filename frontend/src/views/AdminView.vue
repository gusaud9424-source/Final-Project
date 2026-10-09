<!--
  SecuQuest — 관리자 (회원관리 · 학생 진도 · 비밀번호 변경)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-admin">
    <div class="sq-admin__head">
      <h1 class="sq-admin__title">관리자</h1>
      <p class="sq-admin__subtitle">{{ activeTab.desc }}</p>
    </div>

    <div class="sq-admin__tabs" role="tablist" aria-label="관리자 메뉴">
      <button
        v-for="tab in TABS"
        :id="`sq-admin-tab-${tab.key}`"
        :key="tab.key"
        type="button"
        role="tab"
        class="sq-admin__tab"
        :class="{ 'sq-admin__tab--active': active === tab.key }"
        :aria-selected="active === tab.key"
        :aria-controls="`sq-admin-panel-${tab.key}`"
        @click="active = tab.key"
      >
        <i class="bi" :class="tab.icon" aria-hidden="true"></i>
        {{ tab.label }}
      </button>
    </div>

    <section
      :id="`sq-admin-panel-${active}`"
      role="tabpanel"
      :aria-labelledby="`sq-admin-tab-${active}`"
    >
      <MemberManagement v-if="active === 'members'" />
      <StudentsOverview v-else-if="active === 'progress'" />
      <AuditLog v-else-if="active === 'audit'" />
      <AdminPasswordForm v-else-if="active === 'password'" />
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import MemberManagement from "@/components/admin/MemberManagement.vue";
import AdminPasswordForm from "@/components/admin/AdminPasswordForm.vue";
import AuditLog from "@/components/admin/AuditLog.vue";
import StudentsOverview from "@/components/dashboard/StudentsOverview.vue";

const TABS = [
  { key: "members", label: "회원관리", icon: "bi-people", desc: "학생 계정을 조회하고 임시 비밀번호 발급 · 삭제를 관리하세요." },
  { key: "progress", label: "학생 진도", icon: "bi-bar-chart-line", desc: "전체 학생의 과목별 진도를 확인하세요." },
  { key: "audit", label: "감사 로그", icon: "bi-journal-text", desc: "관리자 작업과 계정 보안 변경 기록을 확인하세요. (DB 보관)" },
  { key: "password", label: "비밀번호 변경", icon: "bi-key", desc: "관리자 계정의 비밀번호를 변경하세요." },
];

const active = ref("members");
const activeTab = computed(() => TABS.find((t) => t.key === active.value));
</script>

<style scoped>
.sq-admin {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
}

.sq-admin__title {
  font-size: 32px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
  margin: 0;
}

.sq-admin__subtitle {
  font-size: 14px;
  color: var(--sq-text-sub);
  margin: 6px 0 0;
}

.sq-admin__tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--sq-card-border);
}

.sq-admin__tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  margin-bottom: -1px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--sq-text-sub);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.sq-admin__tab:hover {
  color: var(--sq-text-main);
}

.sq-admin__tab--active {
  border-bottom-color: var(--sq-color-accent);
  color: var(--sq-color-accent);
}

@media (max-width: 768px) {
  .sq-admin__tabs {
    overflow-x: auto;
  }

  .sq-admin__tab {
    white-space: nowrap;
  }
}

/* 휴대폰 폭: 탭이 넘치면 가로 스크롤 */
@media (max-width: 600px) {
  .sq-admin__tabs {
    overflow-x: auto;
  }

  .sq-admin__tab {
    white-space: nowrap;
  }
}
</style>
