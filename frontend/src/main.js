import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import "./assets/design-tokens.css";           // 먼저: CSS 변수 정의
import "./assets/bootstrap-overrides.scss";    // 다음: Bootstrap + 오버라이드
import "bootstrap-icons/font/bootstrap-icons.css";
import router from "./router";

createApp(App).use(createPinia()).use(router).mount("#app");
