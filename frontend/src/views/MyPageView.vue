<!--
  SecuQuest — 마이페이지 (회원정보 조회 · 수정 · 비밀번호 변경)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-mypage">
    <section class="sq-mypage__card sq-mypage__header">
      <h1 class="sq-mypage__title">마이페이지</h1>
      <p class="sq-mypage__subtitle">회원정보를 확인하고 이름 · 닉네임 · 연락처 · 비밀번호를 변경할 수 있습니다.</p>
    </section>

    <p v-if="loadError" class="sq-mypage__error" role="alert">{{ loadError }}</p>

    <div v-else class="sq-mypage__grid">
      <!-- 계정 요약 (수정 불가 항목) -->
      <section class="sq-mypage__card">
        <h2 class="sq-mypage__section-title">계정 정보</h2>
        <dl class="sq-mypage__summary">
          <div class="sq-mypage__row">
            <dt>아이디</dt>
            <dd>{{ account.username }}</dd>
          </div>
          <div class="sq-mypage__row">
            <dt>구분</dt>
            <dd>{{ account.role === "admin" ? "관리자" : "학생" }}</dd>
          </div>
          <div class="sq-mypage__row">
            <dt>가입일</dt>
            <dd>{{ joinedAt }}</dd>
          </div>
          <div class="sq-mypage__row">
            <dt>레벨</dt>
            <dd>Lv.{{ profileStore.level }} ({{ profileStore.totalXp }} XP)</dd>
          </div>
          <div class="sq-mypage__row">
            <dt>보유 포인트</dt>
            <dd>{{ profileStore.points }}P</dd>
          </div>
        </dl>
        <p class="sq-mypage__hint">아이디는 변경할 수 없습니다.</p>
      </section>

      <!-- 회원정보 수정 -->
      <form class="sq-mypage__card sq-mypage__form" novalidate @submit.prevent="saveAccount">
        <h2 class="sq-mypage__section-title">회원정보 수정</h2>

        <label class="sq-mypage__label" for="sq-my-name">이름</label>
        <input id="sq-my-name" v-model="infoForm.name" class="sq-mypage__input" type="text" maxlength="30" autocomplete="name" />

        <label class="sq-mypage__label" for="sq-my-nickname">닉네임 (선택)</label>
        <input
          id="sq-my-nickname"
          v-model="infoForm.nickname"
          class="sq-mypage__input"
          type="text"
          maxlength="20"
          placeholder="한글 · 영문 · 숫자 · 밑줄 2~20자"
        />

        <label class="sq-mypage__label" for="sq-my-email">이메일</label>
        <input id="sq-my-email" v-model="infoForm.email" class="sq-mypage__input" type="email" maxlength="120" autocomplete="email" />

        <label class="sq-mypage__label" for="sq-my-phone">휴대폰 번호</label>
        <input
          id="sq-my-phone"
          v-model="infoForm.phone"
          class="sq-mypage__input"
          type="tel"
          inputmode="numeric"
          maxlength="13"
          placeholder="01012345678"
          autocomplete="tel"
        />

        <label class="sq-mypage__label" for="sq-my-info-password">현재 비밀번호 (본인 확인)</label>
        <input
          id="sq-my-info-password"
          v-model="infoForm.currentPassword"
          class="sq-mypage__input"
          type="password"
          autocomplete="current-password"
        />

        <p v-if="infoError" class="sq-mypage__error" role="alert">{{ infoError }}</p>
        <p v-if="infoSuccess" class="sq-mypage__success" role="status">{{ infoSuccess }}</p>

        <button type="submit" class="sq-mypage__btn" :disabled="infoSaving">
          {{ infoSaving ? "저장 중..." : "회원정보 저장" }}
        </button>
      </form>

      <!-- 비밀번호 변경 -->
      <form class="sq-mypage__card sq-mypage__form" novalidate @submit.prevent="savePassword">
        <h2 class="sq-mypage__section-title">비밀번호 변경</h2>
        <p class="sq-mypage__hint">영문과 숫자를 포함해 8~64자로 입력하세요. 아이디와 같은 비밀번호는 사용할 수 없습니다.</p>

        <label class="sq-mypage__label" for="sq-my-pw-current">현재 비밀번호</label>
        <input id="sq-my-pw-current" v-model="pwForm.current" class="sq-mypage__input" type="password" autocomplete="current-password" />

        <label class="sq-mypage__label" for="sq-my-pw-new">새 비밀번호</label>
        <input id="sq-my-pw-new" v-model="pwForm.next" class="sq-mypage__input" type="password" maxlength="64" autocomplete="new-password" />

        <label class="sq-mypage__label" for="sq-my-pw-confirm">새 비밀번호 확인</label>
        <input id="sq-my-pw-confirm" v-model="pwForm.confirm" class="sq-mypage__input" type="password" maxlength="64" autocomplete="new-password" />

        <p v-if="pwError" class="sq-mypage__error" role="alert">{{ pwError }}</p>
        <p v-if="pwSuccess" class="sq-mypage__success" role="status">{{ pwSuccess }}</p>

        <button type="submit" class="sq-mypage__btn" :disabled="pwSaving">
          {{ pwSaving ? "변경 중..." : "비밀번호 변경" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";
import { useAuthStore } from "@/stores/auth";
import { useProfileStore } from "@/stores/profile";

// 서버 규칙과 같은 값 (최종 검증은 서버 auth.py · profile.py)
const PASSWORD_MIN = 8;
const PASSWORD_MAX = 64;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE_RE = /^01[0-9]{8,9}$/;
const NICKNAME_RE = /^[a-zA-Z0-9가-힣_]+$/;

const authStore = useAuthStore();
const profileStore = useProfileStore();

const account = ref({});
const loadError = ref("");

const infoForm = reactive({ name: "", nickname: "", email: "", phone: "", currentPassword: "" });
const infoSaving = ref(false);
const infoError = ref("");
const infoSuccess = ref("");

const pwForm = reactive({ current: "", next: "", confirm: "" });
const pwSaving = ref(false);
const pwError = ref("");
const pwSuccess = ref("");

const joinedAt = computed(() => (account.value.createdAt ? account.value.createdAt.slice(0, 10) : "-"));

function fillInfoForm(data) {
  account.value = data;
  infoForm.name = data.name;
  infoForm.nickname = data.nickname;
  infoForm.email = data.email;
  infoForm.phone = data.phone;
}

onMounted(async () => {
  try {
    const { data } = await client.get("/profile/account");
    fillInfoForm(data);
    await profileStore.fetchProfile();
  } catch (error) {
    loadError.value = getErrorMessage(error, "회원정보를 불러오지 못했습니다.");
  }
});

// 회원정보 1차 검증
function validateInfo() {
  const name = infoForm.name.trim();
  const nickname = infoForm.nickname.trim();
  const phone = infoForm.phone.replace(/\D/g, "");
  if (!name || name.length > 30) return "이름은 1~30자로 입력하세요.";
  if (nickname && (nickname.length < 2 || nickname.length > 20)) return "닉네임은 2~20자여야 합니다.";
  if (nickname && !NICKNAME_RE.test(nickname)) return "닉네임은 한글·영문·숫자·밑줄만 사용할 수 있습니다.";
  if (!EMAIL_RE.test(infoForm.email.trim())) return "이메일 형식이 올바르지 않습니다.";
  if (!PHONE_RE.test(phone)) return "휴대폰 번호는 숫자 10~11자리(예: 01012345678)로 입력하세요.";
  if (!infoForm.currentPassword) return "본인 확인을 위해 현재 비밀번호를 입력하세요.";
  return "";
}

async function saveAccount() {
  infoError.value = "";
  infoSuccess.value = "";
  const invalid = validateInfo();
  if (invalid) {
    infoError.value = invalid;
    return;
  }

  infoSaving.value = true;
  try {
    const { data } = await client.patch("/profile/account", {
      name: infoForm.name.trim(),
      nickname: infoForm.nickname.trim(),
      email: infoForm.email.trim(),
      phone: infoForm.phone.replace(/\D/g, ""),
      current_password: infoForm.currentPassword,
    });
    fillInfoForm(data);
    infoSuccess.value = data.message;
    // 헤더(이름 · 이메일)와 프로필 패널(닉네임)에 바로 반영
    if (authStore.user) {
      authStore.user.name = data.name;
      authStore.user.email = data.email;
    }
    profileStore.nickname = data.nickname || data.name;
  } catch (error) {
    infoError.value = getErrorMessage(error, "회원정보 변경에 실패했습니다.");
  } finally {
    infoForm.currentPassword = "";
    infoSaving.value = false;
  }
}

// 비밀번호 1차 검증
function validatePassword() {
  if (!pwForm.current || !pwForm.next || !pwForm.confirm) return "모든 항목을 입력하세요.";
  if (pwForm.next.length < PASSWORD_MIN || pwForm.next.length > PASSWORD_MAX) {
    return `새 비밀번호는 ${PASSWORD_MIN}~${PASSWORD_MAX}자로 입력하세요.`;
  }
  if (!/[A-Za-z]/.test(pwForm.next) || !/[0-9]/.test(pwForm.next)) return "새 비밀번호에는 영문과 숫자가 모두 들어가야 합니다.";
  if (pwForm.next !== pwForm.confirm) return "새 비밀번호 확인이 일치하지 않습니다.";
  if (pwForm.next === pwForm.current) return "새 비밀번호가 현재 비밀번호와 같습니다.";
  return "";
}

async function savePassword() {
  pwError.value = "";
  pwSuccess.value = "";
  const invalid = validatePassword();
  if (invalid) {
    pwError.value = invalid;
    return;
  }

  pwSaving.value = true;
  try {
    const { data } = await client.post("/profile/password", {
      current_password: pwForm.current,
      new_password: pwForm.next,
    });
    pwSuccess.value = data.message || "비밀번호가 변경되었습니다.";
    pwForm.current = "";
    pwForm.next = "";
    pwForm.confirm = "";
  } catch (error) {
    pwError.value = getErrorMessage(error, "비밀번호 변경에 실패했습니다.");
  } finally {
    pwSaving.value = false;
  }
}
</script>

<style scoped>
.sq-mypage {
  display: flex;
  flex-direction: column;
  gap: var(--sq-card-gap);
  padding: 24px var(--sq-page-padding-x);
  font-family: var(--sq-font-family);
}

.sq-mypage__card {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-card-radius);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-mypage__title {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-mypage__subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-mypage__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--sq-card-gap);
  align-items: start;
}

.sq-mypage__section-title {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: var(--sq-font-weight-heading);
  color: var(--sq-text-main);
}

.sq-mypage__summary {
  display: flex;
  flex-direction: column;
  margin: 0;
}

.sq-mypage__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 14px;
}

.sq-mypage__row dt {
  font-weight: 600;
  color: var(--sq-text-sub);
}

.sq-mypage__row dd {
  margin: 0;
  color: var(--sq-text-main);
  text-align: right;
  word-break: break-all;
}

.sq-mypage__form {
  display: flex;
  flex-direction: column;
}

.sq-mypage__label {
  margin: 12px 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--sq-text-main);
}

.sq-mypage__input {
  padding: 10px 12px;
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  color: var(--sq-text-main);
  font-size: 14px;
  font-family: var(--sq-font-family);
}

.sq-mypage__input:focus {
  outline: none;
  border-color: var(--sq-color-accent);
}

.sq-mypage__hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--sq-text-sub);
}

.sq-mypage__form .sq-mypage__hint {
  margin: -8px 0 4px;
}

.sq-mypage__error {
  margin: 14px 0 0;
  font-size: 13px;
  color: var(--sq-badge-absent-text);
}

.sq-mypage__success {
  margin: 14px 0 0;
  font-size: 13px;
  color: var(--sq-badge-submitted-text);
}

.sq-mypage__btn {
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

.sq-mypage__btn:hover:not(:disabled) {
  background: var(--sq-color-accent-hover);
}

.sq-mypage__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .sq-mypage__grid {
    grid-template-columns: 1fr;
  }
}
</style>
