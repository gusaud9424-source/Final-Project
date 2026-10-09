<!--
  SecuQuest — 아이디 찾기 (이메일 / 휴대폰)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <AuthCard title="아이디 찾기">
    <!-- 찾기 방식 탭: 주소(/find-id, /find-id/phone)로 구분 -->
    <div class="sq-auth-tabs" role="tablist">
      <router-link
        to="/find-id"
        replace
        role="tab"
        class="sq-auth-tab"
        :class="{ 'sq-auth-tab--active': !isPhone }"
        :aria-selected="!isPhone"
      >
        이메일로 찾기
      </router-link>
      <router-link
        to="/find-id/phone"
        replace
        role="tab"
        class="sq-auth-tab"
        :class="{ 'sq-auth-tab--active': isPhone }"
        :aria-selected="isPhone"
      >
        휴대폰으로 찾기
      </router-link>
    </div>

    <form class="sq-auth-form" @submit.prevent="onSendCode">
      <template v-if="isPhone">
        <label class="sq-auth-label" for="name">이름</label>
        <input id="name" v-model="name" class="sq-auth-input" type="text" autocomplete="name" required />

        <label class="sq-auth-label" for="phone">휴대폰 번호</label>
        <input
          id="phone"
          v-model="phone"
          class="sq-auth-input"
          type="tel"
          inputmode="numeric"
          autocomplete="tel"
          placeholder="01012345678"
          required
        />
        <span class="sq-auth-hint">가입할 때 입력한 이름과 휴대폰 번호로 SMS 인증코드를 보냅니다.</span>
      </template>
      <template v-else>
        <label class="sq-auth-label" for="email">이메일</label>
        <input id="email" v-model="email" class="sq-auth-input" type="email" autocomplete="email" required />
        <span class="sq-auth-hint">가입할 때 입력한 이메일로 인증코드를 보냅니다.</span>
      </template>

      <p v-if="sendError" class="sq-auth-error">{{ sendError }}</p>
      <p v-if="sendMessage" class="sq-auth-notice">{{ sendMessage }}</p>

      <button type="submit" class="sq-auth-submit" :disabled="sending">
        {{ sending ? "발송 중..." : isPhone ? "SMS 인증코드 발송" : "이메일 인증코드 발송" }}
      </button>
    </form>

    <form class="sq-auth-form" @submit.prevent="onVerify">
      <label class="sq-auth-label" for="code">인증코드</label>
      <input id="code" v-model="code" class="sq-auth-input" type="text" inputmode="numeric" required />

      <p v-if="errorMessage" class="sq-auth-error">{{ errorMessage }}</p>
      <div v-if="foundUsernames.length" class="sq-auth-result">
        <template v-if="foundUsernames.length === 1">
          회원님의 아이디는 <strong>{{ foundUsernames[0] }}</strong> 입니다.
        </template>
        <template v-else>
          이 정보로 가입된 아이디입니다.
          <ul>
            <li v-for="item in foundUsernames" :key="item"><strong>{{ item }}</strong></li>
          </ul>
        </template>
      </div>

      <button type="submit" class="sq-auth-submit" :disabled="verifying">
        {{ verifying ? "확인 중..." : "확인" }}
      </button>
    </form>

    <template #links>
      <router-link to="/login">로그인</router-link>
      <span aria-hidden="true">·</span>
      <router-link to="/find-password">비밀번호 찾기</router-link>
      <span aria-hidden="true">·</span>
      <router-link to="/signup">회원가입</router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import AuthCard from "@/components/auth/AuthCard.vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

// 라우터에서 /find-id/phone 이면 method="phone" 이 넘어옴
const props = defineProps({
  method: { type: String, default: "email" },
});
const isPhone = computed(() => props.method === "phone");

const email = ref("");
const name = ref("");
const phone = ref("");
const code = ref("");
const sending = ref(false);
const verifying = ref(false);
const sendMessage = ref("");
const sendError = ref("");
const errorMessage = ref("");
const foundUsernames = ref([]);

// 탭을 바꾸면 이전 방식의 메시지·결과를 비움
watch(isPhone, () => {
  code.value = "";
  sendMessage.value = "";
  sendError.value = "";
  errorMessage.value = "";
  foundUsernames.value = [];
});

async function onSendCode() {
  sending.value = true;
  sendMessage.value = "";
  sendError.value = "";
  try {
    const { data } = isPhone.value
      ? await client.post("/auth/find-id/send-sms-code", { name: name.value, phone: phone.value })
      : await client.post("/auth/find-id/send-code", { email: email.value });
    sendMessage.value = data.message;
  } catch (error) {
    sendError.value = getErrorMessage(error, "요청 처리 중 오류가 발생했습니다.");
  } finally {
    sending.value = false;
  }
}

async function onVerify() {
  verifying.value = true;
  errorMessage.value = "";
  foundUsernames.value = [];
  try {
    const { data } = isPhone.value
      ? await client.post("/auth/find-id/verify-sms", { name: name.value, phone: phone.value, code: code.value })
      : await client.post("/auth/find-id/verify", { email: email.value, code: code.value });
    foundUsernames.value = data.usernames || [data.username];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "인증에 실패했습니다.");
  } finally {
    verifying.value = false;
  }
}
</script>
