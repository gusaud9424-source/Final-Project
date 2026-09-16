import { createApp } from "vue";
import App from "./App.vue";
import "./assets/design-tokens.css";           // 먼저: CSS 변수 정의
import "./assets/bootstrap-overrides.scss";    // 다음: Bootstrap + 오버라이드
import "bootstrap-icons/font/bootstrap-icons.css";
// router, pinia 등록은 이후 단계에서 추가

createApp(App).mount("#app");
