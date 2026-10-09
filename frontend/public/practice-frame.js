// SecuQuest — XSS 실습 미리보기 프레임 로더
// 부모 창(SecuQuest 앱)이 보낸 실습 HTML 한 건만 받아 이 문서를 통째로 교체한다.
// 이 프레임은 sandbox="allow-scripts"(opaque origin)라 앱의 쿠키·세션·DOM에 접근할 수 없다.
(function () {
  function onRender(event) {
    // 부모 창에서 온 렌더 요청만 처리
    if (event.source !== window.parent) return;
    var data = event.data;
    if (!data || data.type !== "sq-render" || typeof data.html !== "string") return;

    window.removeEventListener("message", onRender);
    document.open();
    document.write(data.html);
    document.close();
  }

  window.addEventListener("message", onRender);
  // 준비 완료 알림 → 부모가 HTML 전송
  window.parent.postMessage({ type: "sq-frame-ready" }, "*");
})();
