<!--
  SecuQuest — 로그인 출석 체크판 (14일 2줄, 포인트만 랜덤 지급)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <Teleport to="body">
    <div class="sq-att" @click.self="$emit('close')">
      <div class="sq-att__dialog" role="dialog" aria-modal="true" aria-labelledby="sq-att-title">
        <div class="sq-att__header">
          <h2 id="sq-att-title" class="sq-att__title">출석 체크</h2>
          <button type="button" class="sq-att__close" aria-label="닫기" @click="$emit('close')">
            <i class="bi bi-x-lg" aria-hidden="true"></i>
          </button>
        </div>

        <p class="sq-att__desc">
          매일 접속하고 출석하면 포인트를 받아요. 14일까지 모으면 완료!
          <span class="sq-att__balance">보유 포인트 {{ points }}P</span>
        </p>

        <p v-if="loading" class="sq-att__status">불러오는 중...</p>
        <p v-else-if="errorMessage" class="sq-att__error">{{ errorMessage }}</p>

        <template v-else>
          <div class="sq-att__grid">
            <div
              v-for="d in days"
              :key="d.day"
              class="sq-att__cell"
              :class="[`sq-att__cell--${d.state}`, { 'sq-att__cell--bonus': d.bonus }]"
            >
              <span class="sq-att__day">{{ d.day }}일차</span>
              <span class="sq-att__icon">
                <i v-if="d.state === 'claimed'" class="bi bi-check-circle-fill" aria-hidden="true"></i>
                <i v-else-if="d.bonus" class="bi bi-gem" aria-hidden="true"></i>
                <i v-else class="bi bi-coin" aria-hidden="true"></i>
              </span>
              <span class="sq-att__amount">
                <template v-if="d.state === 'claimed'">+{{ d.amount }}P</template>
                <template v-else-if="d.bonus">보너스</template>
                <template v-else>포인트</template>
              </span>
            </div>
          </div>

          <div class="sq-att__actions">
            <button
              type="button"
              class="sq-att__claim"
              :disabled="!canClaimToday || claiming"
              @click="claim"
            >
              {{ claimLabel }}
            </button>
          </div>

          <p v-if="justClaimed" class="sq-att__result">
            🎉 {{ justClaimed.day }}일차 출석 완료! 포인트 +{{ justClaimed.amount }}P 적립
          </p>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useProfileStore } from "@/stores/profile";

const emit = defineEmits(["close", "claimed"]);
const profileStore = useProfileStore();

const loading = ref(true);
const errorMessage = ref("");
const days = ref([]);
const canClaimToday = ref(false);
const completed = ref(0);
const claimedToday = ref(false);
const points = ref(0);
const claiming = ref(false);
const justClaimed = ref(null);

const claimLabel = computed(() => {
  if (completed.value >= 14) return "14일 출석 완료";
  if (claimedToday.value) return "오늘 출석 완료";
  if (canClaimToday.value) return "오늘 출석하고 포인트 받기";
  return "출석 불가";
});

function applyBoard(data) {
  days.value = data.days;
  canClaimToday.value = data.canClaimToday;
  completed.value = data.completed;
  claimedToday.value = data.claimedToday;
  points.value = data.points;
  profileStore.points = data.points;
}

async function load() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await client.get("/attendance");
    applyBoard(data);
  } catch (err) {
    errorMessage.value = getErrorMessage(err, "출석 정보를 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
}

async function claim() {
  if (!canClaimToday.value || claiming.value) return;
  claiming.value = true;
  errorMessage.value = "";
  try {
    const { data } = await client.post("/attendance/claim");
    justClaimed.value = { day: data.day, amount: data.amount };
    applyBoard(data.board);
    emit("claimed", data);
  } catch (err) {
    errorMessage.value = getErrorMessage(err, "출석에 실패했습니다.");
    await load();
  } finally {
    claiming.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.sq-att {
  position: fixed;
  inset: 0;
  background: rgba(26, 29, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.sq-att__dialog {
  width: 100%;
  max-width: 640px;
  background: var(--sq-bg-card);
  border: 1px solid var(--sq-card-border);
  box-shadow: var(--sq-card-shadow-hover);
  padding: 20px 22px;
  max-height: 90vh;
  overflow-y: auto;
}

.sq-att__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.sq-att__title {
  margin: 0;
  font-size: 20px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-att__close {
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  color: var(--sq-text-sub);
}

.sq-att__desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--sq-text-sub);
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
}

.sq-att__balance {
  font-weight: 700;
  color: var(--sq-color-accent);
}

.sq-att__status,
.sq-att__error {
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-att__error {
  color: var(--sq-badge-absent-text);
}

/* 2줄 × 7칸 */
.sq-att__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.sq-att__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 4px;
  border: 1px solid var(--sq-card-border);
  background: var(--sq-bg-card);
  text-align: center;
}

.sq-att__day {
  font-size: 11px;
  font-weight: 700;
  color: var(--sq-text-sub);
}

.sq-att__icon {
  font-size: 20px;
  color: var(--sq-color-accent);
}

.sq-att__amount {
  font-size: 11px;
  color: var(--sq-text-main);
}

.sq-att__cell--claimed {
  background: var(--sq-badge-submitted-bg);
  border-color: var(--sq-badge-submitted-text);
}

.sq-att__cell--claimed .sq-att__icon,
.sq-att__cell--claimed .sq-att__amount {
  color: var(--sq-badge-submitted-text);
}

.sq-att__cell--claimable {
  border-color: var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
  box-shadow: 0 0 0 2px var(--sq-color-accent-subtle);
}

.sq-att__cell--locked {
  opacity: 0.55;
}

.sq-att__cell--bonus {
  background: var(--sq-badge-dday-bg);
  border-color: var(--sq-badge-dday-text);
}

.sq-att__cell--bonus .sq-att__icon {
  color: var(--sq-badge-dday-text);
}

.sq-att__cell--bonus.sq-att__cell--claimed {
  background: var(--sq-badge-submitted-bg);
  border-color: var(--sq-badge-submitted-text);
}

.sq-att__actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.sq-att__claim {
  padding: 12px 28px;
  border: none;
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}

.sq-att__claim:hover:not(:disabled) {
  background: var(--sq-color-accent-hover);
}

.sq-att__claim:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.sq-att__result {
  margin: 12px 0 0;
  text-align: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--sq-color-accent);
}
</style>
