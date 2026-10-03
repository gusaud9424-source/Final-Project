<!--
  SecuQuest — 미션 보상 슬롯
  - 미션(방어 퀴즈) 보상만 이 자리에서 수령한다.
  - 실습 보상은 헤더 보물상자에서 받는다(여기서는 안내만).
  - 개념 학습은 보상이 없고, 완료하면 "보상 완료"로 표시한다.
  © 2026 5팀_Security Learning Platform
-->
<template>
  <!-- 보상 없는 미션 (개념 학습) -->
  <div v-if="state.status === 'none'" class="sq-reward" :class="taskCompleted ? 'sq-reward--claimed' : 'sq-reward--none'">
    <i class="bi" :class="taskCompleted ? 'bi-check-circle-fill' : 'bi-dash-circle'" aria-hidden="true"></i>
    <span class="sq-reward__label">{{ taskCompleted ? "보상 완료" : "보상 없음" }}</span>
  </div>

  <!-- 아직 미달성: 받을 보상 미리보기 -->
  <div v-else-if="state.status === 'locked'" class="sq-reward sq-reward--locked">
    <i class="bi bi-gift" aria-hidden="true"></i>
    <span class="sq-reward__label">미션 완료 시 지급</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }}
      </li>
    </ul>
  </div>

  <!-- 수령 가능: 미션(방어 퀴즈)만 여기서 받는다 -->
  <button
    v-else-if="state.status === 'pending' && claimable"
    type="button"
    class="sq-reward sq-reward--pending"
    :disabled="busy"
    @click="$emit('claim')"
  >
    <i class="bi bi-gift-fill" aria-hidden="true"></i>
    <span class="sq-reward__label">보상 받기</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }} +{{ item.amount }}
      </li>
    </ul>
  </button>

  <!-- 수령 대기지만 보물상자에서 받는 보상 (실습) -->
  <div v-else-if="state.status === 'pending'" class="sq-reward sq-reward--chest">
    <i class="bi bi-gift-fill" aria-hidden="true"></i>
    <span class="sq-reward__label">보물상자에서 받기</span>
    <span class="sq-reward__hint">상단 보물상자 아이콘</span>
  </div>

  <!-- 수령 완료 -->
  <div v-else class="sq-reward sq-reward--claimed">
    <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
    <span class="sq-reward__label">수령 완료</span>
    <ul class="sq-reward__items">
      <li v-for="(item, i) in state.items" :key="i">
        <i class="bi" :class="iconOf(item.type)" aria-hidden="true"></i>
        {{ labelOf(item.type) }} +{{ item.amount }}
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  state: { type: Object, required: true },
  claimable: { type: Boolean, default: false },
  taskCompleted: { type: Boolean, default: false },
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

.sq-reward__hint {
  font-size: 12px;
  color: var(--sq-text-sub);
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

.sq-reward--none {
  color: var(--sq-text-sub);
}

.sq-reward--locked {
  color: var(--sq-text-sub);
  border-style: dashed;
}

.sq-reward--chest {
  color: var(--sq-color-accent);
  border-color: var(--sq-color-accent);
  border-style: dashed;
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
