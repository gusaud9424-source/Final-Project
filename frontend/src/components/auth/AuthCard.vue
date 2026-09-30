<!--
  SecuQuest — 아이디 찾기/비밀번호 찾기/회원가입 공용 카드 레이아웃
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform

  사용법:
    <AuthCard title="..." description="..." @submit="...">
      <label class="sq-auth-field">
        <span class="sq-auth-field__label">라벨</span>
        <input v-model="x" class="form-control sq-auth-field__input" />
      </label>
      <template #aside><router-link class="sq-auth-link" to="...">좌측 링크</router-link></template>
      <template #footer><router-link class="sq-auth-link" to="...">하단 링크</router-link></template>
    </AuthCard>
-->
<template>
  <div class="sq-auth-page">
    <router-link to="/login" class="sq-auth-logo" aria-label="SecuQuest 로그인으로 이동">
      <BrandMark />
      <span class="sq-auth-logo__text">SecuQuest</span>
    </router-link>

    <section class="sq-auth-card">
      <h1 class="sq-auth-card__title">{{ title }}</h1>
      <p v-if="description" class="sq-auth-card__desc">
        {{ description }}
        <i class="bi bi-question-circle sq-auth-card__help" aria-hidden="true"></i>
      </p>

      <form class="sq-auth-card__form" novalidate @submit.prevent="emit('submit')">
        <div class="sq-auth-card__fields">
          <slot />
        </div>

        <div
          v-if="showSubmit"
          class="sq-auth-card__actions"
          :class="{ 'sq-auth-card__actions--block': blockSubmit }"
        >
          <div v-if="$slots.aside && !blockSubmit" class="sq-auth-card__aside">
            <slot name="aside" />
          </div>
          <button type="submit" class="sq-auth-card__submit" :disabled="submitting">
            {{ submitLabel }}
          </button>
        </div>
      </form>

      <div v-if="$slots.footer" class="sq-auth-card__footer">
        <slot name="footer" />
      </div>
    </section>

    <AppFooter />
  </div>
</template>

<script setup>
import BrandMark from "@/components/brand/BrandMark.vue";
import AppFooter from "@/components/layout/AppFooter.vue";

defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: "",
  },
  submitLabel: {
    type: String,
    default: "다음",
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  // true 면 좌측 링크 없이 버튼을 카드 폭 가득 표시 (회원가입)
  blockSubmit: {
    type: Boolean,
    default: false,
  },
  // false 면 버튼 줄 숨김 (결과 표시 단계)
  showSubmit: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(["submit"]);
</script>

<style scoped>
/* 전역 그라데이션 배경을 덮는 흰 전체 화면 (App.vue 의 main 폭 제한 밖으로) */
.sq-auth-page {
  position: fixed;
  inset: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sq-auth-page-top) var(--sq-auth-page-gutter) 0;
  background: var(--sq-auth-bg-page);
  font-family: var(--sq-font-family);
}

/* ─── 로고 ─── */
.sq-auth-logo {
  display: inline-flex;
  align-items: center;
  gap: var(--sq-auth-logo-gap);
  margin-bottom: var(--sq-auth-logo-bottom);
  color: var(--sq-color-accent);
  text-decoration: none;
}

.sq-auth-logo .sq-brand-mark {
  width: auto;
  height: 40px;
}

.sq-auth-logo__text {
  font-size: 34px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.5px;
}

/* ─── 카드 ─── */
.sq-auth-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: var(--sq-auth-card-width);
  min-height: var(--sq-auth-card-min-height);
  padding: var(--sq-auth-card-padding-top) var(--sq-auth-card-padding-x)
    var(--sq-auth-card-padding-bottom);
  border: 1px solid var(--sq-auth-card-border);
  border-radius: var(--sq-radius-auth-card);
  background: var(--sq-auth-bg-page);
  box-shadow: none;
}

.sq-auth-card__title {
  margin: 0 0 var(--sq-auth-title-bottom);
  font-size: 26px;
  font-weight: 700;
  line-height: 1.3;
  color: var(--sq-auth-text-title);
}

.sq-auth-card__desc {
  display: flex;
  align-items: center;
  gap: var(--sq-auth-desc-gap);
  margin: 0;
  font-size: 18px;
  line-height: 1.4;
  color: var(--sq-auth-text-desc);
}

.sq-auth-card__help {
  font-size: 18px;
  line-height: 1;
}

.sq-auth-card__fields {
  display: flex;
  flex-direction: column;
  gap: var(--sq-auth-field-gap);
  margin-top: var(--sq-auth-fields-top);
}

/* ─── 입력박스 (슬롯 콘텐츠, Bootstrap form-control 덮어쓰기) ─── */
:slotted(.sq-auth-field) {
  position: relative;
  display: block;
  height: var(--sq-auth-input-height);
  margin: 0;
}

:slotted(.sq-auth-field__label) {
  position: absolute;
  top: var(--sq-auth-label-top);
  left: var(--sq-auth-input-padding-x);
  font-size: 14px;
  line-height: 1.2;
  color: var(--sq-auth-text-sub);
  pointer-events: none;
}

:slotted(.sq-auth-field__input) {
  width: 100%;
  height: 100%;
  padding: var(--sq-auth-input-padding-top) var(--sq-auth-input-padding-x)
    var(--sq-auth-input-padding-bottom);
  border: var(--sq-auth-input-border-width) solid var(--sq-color-accent);
  border-radius: var(--sq-radius-auth-input);
  background: var(--sq-auth-bg-page);
  font-family: var(--sq-font-family);
  font-size: 17px;
  color: var(--sq-auth-text-title);
  box-shadow: none;
}

:slotted(.sq-auth-field__input:focus) {
  border-color: var(--sq-color-accent);
  box-shadow: none;
  outline: none;
}

/* ─── 버튼 줄 ─── */
.sq-auth-card__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sq-auth-actions-gap);
  margin-top: var(--sq-auth-actions-top);
}

.sq-auth-card__aside {
  display: flex;
  align-items: center;
  gap: var(--sq-auth-actions-gap);
}

.sq-auth-card__submit {
  flex-shrink: 0;
  width: var(--sq-auth-button-width);
  height: var(--sq-auth-button-height);
  margin-left: auto;
  border: none;
  border-radius: var(--sq-radius-auth-button);
  background: var(--sq-color-accent);
  color: var(--sq-color-on-accent);
  font-family: var(--sq-font-family);
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
}

.sq-auth-card__submit:hover {
  background: var(--sq-color-accent-hover);
}

.sq-auth-card__submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sq-auth-card__actions--block .sq-auth-card__submit {
  width: 100%;
  margin-left: 0;
}

/* ─── 하단 링크 ─── */
.sq-auth-card__footer {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sq-auth-footer-gap);
  margin-top: auto;
  padding-top: var(--sq-auth-footer-top);
}

:slotted(.sq-auth-link) {
  font-size: 17px;
  color: var(--sq-auth-text-sub);
  text-decoration: underline;
  text-underline-offset: 5px;
}

:slotted(.sq-auth-link:hover) {
  color: var(--sq-auth-text-desc);
}

/* ─── 모바일 ─── */
@media (max-width: 575.98px) {
  .sq-auth-page {
    padding-top: var(--sq-auth-page-top-mobile);
  }

  .sq-auth-logo {
    margin-bottom: var(--sq-auth-logo-bottom-mobile);
  }

  .sq-auth-card {
    min-height: 0;
    padding: var(--sq-auth-card-padding-y-mobile) var(--sq-auth-card-padding-x-mobile);
  }
}
</style>
