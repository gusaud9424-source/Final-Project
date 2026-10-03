<!--
  SecuQuest — 헤더 보물상자 (미수령 보상 목록 · 클릭 수령)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-chest">
    <button
      type="button"
      class="sq-chest__button"
      :aria-label="`보물상자 (미수령 보상 ${rewardStore.count}개)`"
      @click="openModal"
    >
      <i class="bi bi-gift-fill" aria-hidden="true"></i>
      <span v-if="rewardStore.count" class="sq-chest__badge">{{ rewardStore.count }}</span>
    </button>

    <Teleport to="body">
      <div v-if="showModal" class="sq-chest-modal" @click.self="closeModal">
        <div class="sq-chest-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="sq-chest-title">
          <div class="sq-chest-modal__header">
            <h2 id="sq-chest-title" class="sq-chest-modal__title">보물상자</h2>
            <button type="button" class="sq-chest-modal__close" aria-label="닫기" @click="closeModal">
              <i class="bi bi-x-lg" aria-hidden="true"></i>
            </button>
          </div>

          <p v-if="loading" class="sq-chest-modal__empty">불러오는 중…</p>
          <p v-else-if="!rewardStore.count" class="sq-chest-modal__empty">받을 보상이 없습니다.</p>
          <ul v-else class="sq-chest-modal__list">
            <li v-for="item in rewardStore.items" :key="item.id">
              <button
                type="button"
                class="sq-chest-item"
                :disabled="rewardStore.claiming"
                @click="handleClaim(item.id)"
              >
                <i
                  class="sq-chest-item__icon bi"
                  :class="item.type === 'xp' ? 'bi-stars' : 'bi-coin sq-chest-item__icon--point'"
                  aria-hidden="true"
                ></i>
                <span class="sq-chest-item__amount">
                  +{{ item.amount }} {{ item.type === "xp" ? "XP" : "P" }}
                </span>
                <span class="sq-chest-item__reason">{{ item.reason }}</span>
                <span class="sq-chest-item__action">받기</span>
              </button>
            </li>
          </ul>

          <p v-if="errorMessage" class="sq-chest-modal__error">{{ errorMessage }}</p>

          <button
            type="button"
            class="sq-chest-modal__claim-all"
            :disabled="!rewardStore.count || rewardStore.claiming"
            @click="handleClaimAll"
          >
            모두 받기
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { useRewardStore } from "@/stores/reward";
import { getErrorMessage } from "@/api/errors";

const rewardStore = useRewardStore();
const showModal = ref(false);
const loading = ref(false);
const errorMessage = ref("");

async function refresh() {
  try {
    await rewardStore.fetchPending();
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "보상 목록을 불러오지 못했습니다.");
  }
}

async function openModal() {
  showModal.value = true;
  errorMessage.value = "";
  loading.value = true;
  await refresh();
  loading.value = false;
}

function closeModal() {
  showModal.value = false;
}

async function handleClaim(id) {
  errorMessage.value = "";
  try {
    await rewardStore.claim(id);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "보상 수령에 실패했습니다.");
    // 이미 수령된 항목 등 서버 상태와 어긋난 경우 목록 재동기화
    await refresh();
  }
}

async function handleClaimAll() {
  errorMessage.value = "";
  try {
    await rewardStore.claimAll();
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "보상 수령에 실패했습니다.");
    await refresh();
  }
}

function handleKeydown(event) {
  if (event.key === "Escape" && showModal.value) closeModal();
}

onMounted(() => {
  refresh();
  document.addEventListener("keydown", handleKeydown);
});
onUnmounted(() => document.removeEventListener("keydown", handleKeydown));
</script>

<style scoped>
.sq-chest {
  position: relative;
}

.sq-chest__button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-color-accent);
  font-size: 24px;
  cursor: pointer;
}

.sq-chest__button:hover {
  color: var(--sq-color-accent-hover);
}

.sq-chest__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--sq-badge-dday-bg);
  color: var(--sq-badge-dday-text);
  font-size: 12px;
  font-weight: 700;
  line-height: 20px;
  text-align: center;
}

/* 모달 */
.sq-chest-modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: color-mix(in srgb, var(--sq-text-main) 40%, transparent);
  font-family: var(--sq-font-family);
  z-index: 1050;
}

.sq-chest-modal__dialog {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-card-radius);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow-hover);
}

.sq-chest-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sq-chest-modal__title {
  margin: 0;
  font-size: 18px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-chest-modal__close {
  border: none;
  background: transparent;
  color: var(--sq-text-sub);
  font-size: 16px;
  cursor: pointer;
}

.sq-chest-modal__empty {
  margin: 0;
  padding: 24px 0;
  font-size: 14px;
  text-align: center;
  color: var(--sq-text-sub);
}

.sq-chest-modal__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.sq-chest-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  font-family: var(--sq-font-family);
  text-align: left;
  cursor: pointer;
}

.sq-chest-item:hover:not(:disabled) {
  background: var(--sq-color-accent-subtle);
}

.sq-chest-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-chest-item__icon {
  font-size: 20px;
  color: var(--sq-color-accent);
}

.sq-chest-item__icon--point {
  font-size: 28px;
}

.sq-chest-item__amount {
  font-size: 15px;
  font-weight: 700;
  color: var(--sq-text-main);
  white-space: nowrap;
}

.sq-chest-item__reason {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: var(--sq-text-sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sq-chest-item__action {
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-color-accent);
}

.sq-chest-modal__error {
  margin: 0;
  font-size: 12px;
  color: var(--sq-badge-absent-text);
}

.sq-chest-modal__claim-all {
  padding: 10px 14px;
  border: none;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.sq-chest-modal__claim-all:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
