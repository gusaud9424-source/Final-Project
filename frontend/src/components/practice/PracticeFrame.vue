<!--
  SecuQuest — XSS 실습 미리보기 iframe (별도 CSP 프레임 + postMessage 렌더)
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <!--
    srcdoc 은 부모(앱)의 CSP를 그대로 물려받아 실습 스크립트가 막힌다.
    그래서 실습 전용 CSP가 붙는 /practice-frame.html 을 불러오고 HTML은 postMessage로 넘긴다.
    html 이 바뀌면 key 를 바꿔 프레임을 새로 만든다 (이전 실습 상태 초기화).
  -->
  <iframe
    :key="renderKey"
    ref="frameEl"
    sandbox="allow-scripts"
    src="/practice-frame.html"
    :title="title"
  ></iframe>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  html: { type: String, required: true },
  title: { type: String, default: "실습 미리보기" },
});

const frameEl = ref(null);
const renderKey = ref(0);

watch(
  () => props.html,
  () => {
    renderKey.value += 1;
  }
);

function onMessage(event) {
  const win = frameEl.value?.contentWindow;
  if (!win || event.source !== win) return;
  if (event.data?.type !== "sq-frame-ready") return;
  // 프레임은 opaque origin 이라 targetOrigin 을 특정할 수 없어 "*" 사용 (보내는 값은 공개 실습 HTML)
  win.postMessage({ type: "sq-render", html: props.html }, "*");
}

onMounted(() => window.addEventListener("message", onMessage));
onBeforeUnmount(() => window.removeEventListener("message", onMessage));

// 부모 컴포넌트가 판정 메시지 출처(event.source)를 확인할 때 사용
// (Window 객체를 그대로 expose 하면 Vue 가 ref 여부를 검사하다 cross-origin 오류가 나서 함수로 노출)
function getWindow() {
  return frameEl.value?.contentWindow ?? null;
}

defineExpose({ getWindow });
</script>
