<!--
  SecuQuest — 미션 보상 슬롯 (개념·미션 보상은 여기서 수령, 실습 보상은 보물상자 안내)
  © 2026 5팀_Security Learning Platform
-->
<template>
  <!-- 아직 미달성: 받을 보상 미리보기 -->
  <div v-if="state.status === 'locked'" class="sq-reward sq-reward--locked">
    <i class="bi bi-gift" aria-hidden="true"></i>
    <span class="sq-reward__label">미션 완료 시 지급</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }} {{ item.min }}~{{ item.max }}
      </li>
    </ul>
  </div>

  <!-- 수령 대기 · 보물상자 수령 대상(실습 성공 보상): 미션 탭에서는 안내만 -->
  <div v-else-if="state.status === 'pending' && state.claimAt === 'chest'" class="sq-reward sq-reward--chest">
    <i class="bi bi-gift-fill" aria-hidden="true"></i>
    <span class="sq-reward__label">보물상자에서 받기</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }} +{{ item.amount }}
      </li>
    </ul>
  </div>

  <!-- 수령 가능: 미션 탭에서 받기 -->
  <button
    v-else-if="state.status === 'pending'"
    type="button"
    class="sq-reward sq-reward--pending"
    :disabled="busy"
    @click="$emit('claim')"
  >
    <span class="sq-reward__flag">받을 수 있어요!</span>
    <i class="bi bi-gift-fill" aria-hidden="true"></i>
    <span class="sq-reward__label">보상 받기</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }} +{{ item.amount }}
      </li>
    </ul>
  </button>

  <!-- 수령 완료 -->
  <div v-else-if="state.status === 'claimed'" class="sq-reward sq-reward--claimed">
    <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
    <span class="sq-reward__label">수령 완료</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }} +{{ item.amount }}
      </li>
    </ul>
  </div>

  <!-- 보상 정보 없음 (예외) -->
  <div v-else class="sq-reward sq-reward--locked">
    <i class="bi bi-gift" aria-hidden="true"></i>
    <span class="sq-reward__label">미션 완료 시 지급</span>
  </div>
</template>

<script setup>
defineProps({
  state: { type: Object, required: true },
  busy: { type: Boolean, default: false },
});
defineEmits(["claim"]);

function iconOf(type) {
  return type === "xp" ? "bi-stars" : "bi-coin";
}
function labelOf(type) {
  return type === "xp" ? "경험치" : "포인트";
}
</script>

<style scoped>
.sq-reward {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 10px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  text-align: center;
  font: inherit;
}

.sq-reward > .bi {
  font-size: 24px;
}

.sq-reward__label {
  font-size: 13px;
  font-weight: 700;
}

.sq-reward__items {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: var(--sq-text-sub);
}

.sq-reward__flag {
  position: absolute;
  top: -9px;
  padding: 2px 8px;
  border-radius: var(--sq-radius-none);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-size: 11px;
  font-weight: 700;
}

.sq-reward--locked {
  color: var(--sq-text-sub);
  border-style: dashed;
}

/* 보물상자 수령 대상: 미션 탭에서는 클릭 없이 안내만 */
.sq-reward--chest {
  border-color: var(--sq-color-accent);
  color: var(--sq-color-accent);
}

.sq-reward--pending {
  border-color: var(--sq-color-accent);
  background: var(--sq-color-accent-subtle);
  color: var(--sq-color-accent);
  cursor: pointer;
}

.sq-reward--pending:hover:not(:disabled) {
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
}

.sq-reward--pending:hover:not(:disabled) .sq-reward__items {
  color: var(--sq-color-on-accent);
}

.sq-reward--pending:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-reward--claimed {
  border-color: var(--sq-badge-submitted-text);
  color: var(--sq-badge-submitted-text);
}
</style>
