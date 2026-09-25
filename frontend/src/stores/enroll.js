import { defineStore } from "pinia";
import { ref } from "vue";
// import client from "@/api/client";

export const useEnrollStore = defineStore("enroll", () => {
  const items = ref([
    // ── 초급 ──
    {
      id: "command-injection",
      difficulty: "초급",
      category: "command-injection",
      title: "Command Injection",
      desc: "입력값에 OS 명령을 주입해 서버에서 실행시키는 취약점",
      detail: {
        summary: "사용자 입력이 검증 없이 셸 명령 문자열에 그대로 결합될 때 발생한다.",
        exploit: "`; ls -al` `&& cat /etc/passwd` 처럼 구분자를 섞어 임의 명령을 실행한다.",
        defense: "셸 실행 대신 언어 내장 API를 쓰고, 불가피하면 화이트리스트 검증과 인자 배열 전달을 사용한다.",
      },
      route: "/chapters/command-injection",
      enrolled: false,
    },
    {
      id: "xss-reflected",
      difficulty: "초급",
      category: "xss",
      title: "XSS (Reflected)",
      desc: "요청 파라미터가 응답에 그대로 반사되어 스크립트가 실행됨",
      detail: {
        summary: "서버가 쿼리스트링 등 입력값을 이스케이프 없이 HTML 응답에 즉시 반영할 때 발생한다.",
        exploit: "`?q=<script>alert(document.cookie)</script>` 링크를 피해자가 클릭하면 즉시 실행된다.",
        defense: "출력 시 컨텍스트에 맞는 이스케이프 처리와 CSP 헤더를 적용한다.",
      },
      route: "/chapters/xss-reflected",
      enrolled: false,
    },
    {
      id: "xss-dom",
      difficulty: "초급",
      category: "xss",
      title: "XSS (DOM)",
      desc: "클라이언트 DOM 조작 과정에서 스크립트가 실행됨",
      detail: {
        summary: "서버를 거치지 않고 클라이언트 JS가 location.hash 등을 innerHTML에 직접 삽입할 때 발생한다.",
        exploit: "URL 해시(`#`) 값을 innerHTML로 렌더링하는 코드에 스크립트 태그를 담아 전달한다.",
        defense: "innerHTML 대신 textContent를 쓰거나 DOMPurify 같은 새니타이저를 거친다.",
      },
      route: "/chapters/xss-dom",
      enrolled: false,
    },
    {
      id: "xss-stored",
      difficulty: "초급",
      category: "xss",
      title: "XSS (Stored)",
      desc: "저장된 입력값이 다른 사용자 화면에서 스크립트로 실행됨",
      detail: {
        summary: "게시글·댓글처럼 DB에 저장된 입력값이 이스케이프 없이 모든 열람자에게 렌더링될 때 발생한다.",
        exploit: "게시글 본문에 스크립트를 저장하면 이후 방문하는 모든 사용자 브라우저에서 실행된다.",
        defense: "저장 전 입력 검증과 출력 시 이스케이프를 함께 적용하고 CSP로 이중 방어한다.",
      },
      route: "/chapters/xss-stored",
      enrolled: false,
    },
    // ── 중급 ──
    {
      id: "sql-injection",
      difficulty: "중급",
      category: "sql-injection",
      title: "SQL Injection",
      desc: "쿼리 조작으로 DB 데이터를 유출하는 취약점",
      detail: {
        summary: "입력값이 SQL 쿼리 문자열에 직접 결합되어 쿼리 구조 자체를 바꿀 수 있을 때 발생한다.",
        exploit: "`' OR '1'='1` 같은 입력으로 인증을 우회하거나 UNION SELECT로 다른 테이블 데이터를 조회한다.",
        defense: "Prepared Statement(파라미터 바인딩)를 사용하고 최소 권한 DB 계정을 적용한다.",
      },
      route: "/chapters/sql-injection",
      enrolled: false,
    },
    {
      id: "csrf",
      difficulty: "중급",
      category: "csrf",
      title: "CSRF",
      desc: "피해자 권한으로 위조 요청(비밀번호 변경 등)을 실행시키는 취약점",
      detail: {
        summary: "인증된 세션 쿠키가 자동 전송되는 점을 악용해 피해자 브라우저가 의도치 않은 요청을 보내게 한다.",
        exploit: "공격자 페이지에 숨겨진 폼이 피해자의 세션으로 비밀번호 변경 API를 자동 제출한다.",
        defense: "CSRF 토큰 검증과 SameSite 쿠키 속성을 함께 적용한다.",
      },
      route: "/chapters/csrf",
      enrolled: false,
    },
    {
      id: "file-upload",
      difficulty: "중급",
      category: "file-upload",
      title: "File Upload",
      desc: "웹셸 등 악성 파일 업로드로 원격 코드 실행",
      detail: {
        summary: "업로드 파일의 확장자·MIME·내용 검증이 부실해 실행 가능한 파일이 서버에 저장될 때 발생한다.",
        exploit: "이미지로 위장한 웹셸(.php 등)을 업로드해 실행 경로로 접근하면 원격 명령 실행이 가능해진다.",
        defense: "확장자 화이트리스트, 실제 콘텐츠 검사, 실행 권한 없는 별도 스토리지 저장을 병행한다.",
      },
      route: "/chapters/file-upload",
      enrolled: false,
    },
    // ── 고급 ──
    {
      id: "sql-injection-blind",
      difficulty: "고급",
      category: "sql-injection-blind",
      title: "SQL Injection (Blind)",
      desc: "참/거짓·시간지연 응답으로 데이터를 추론하는 기법",
      detail: {
        summary: "쿼리 결과가 화면에 직접 노출되지 않아도 응답의 차이(참/거짓, 지연 시간)로 데이터를 한 글자씩 추론할 수 있다.",
        exploit: "`AND SUBSTRING(password,1,1)='a'` 또는 `SLEEP(5)` 조건으로 응답 차이를 관찰해 데이터를 유추한다.",
        defense: "Prepared Statement 적용은 동일하며, 추가로 에러 메시지 노출 최소화와 요청 속도 제한을 둔다.",
      },
      route: "/chapters/sql-injection-blind",
      enrolled: false,
    },
  ]);

  function enroll(id) {
    const item = items.value.find((i) => i.id === id);
    if (item && !item.enrolled) {
      item.enrolled = true;
      // TODO: 백엔드 연동 시 활성화
      // await client.post("/enrollments", { chapter_id: id });
    }
  }

  return { items, enroll };
});
