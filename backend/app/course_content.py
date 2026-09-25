# 과목별 방어 퀴즈 (정답 인덱스 answer 는 서버에만 보관, 클라이언트로 내려주지 않음)
DEFENSE_QUIZZES = {
    "command-injection": {
        "question": "사용자 입력으로 OS 명령을 실행해야 할 때 가장 안전한 방법은?",
        "options": [
            "`;`, `&&`, `|` 같은 셸 메타문자를 블랙리스트로 제거한 뒤 셸로 실행한다",
            "입력값 전체를 작은따옴표로 감싸 하나의 인자처럼 만든 뒤 셸로 실행한다",
            "셸 대신 언어 내장 API나 인자 배열로 전달하고 화이트리스트로 검증한다",
            "프론트엔드에서 정규식으로 입력을 검증하고 서버는 전달받은 값을 그대로 실행한다",
        ],
        "answer": 2,
        "explanation": "블랙리스트·따옴표 처리·클라이언트 검증은 우회 가능하므로, 입력이 셸에 해석되지 않도록 하는 것이 근본 대책입니다.",
    },
    "xss-reflected": {
        "question": "쿼리 파라미터 값을 응답 HTML에 출력할 때 핵심 방어는?",
        "options": [
            "출력 위치(HTML·속성·JS)에 맞게 이스케이프하고 CSP로 이중 방어한다",
            "`<script>` 문자열을 서버에서 찾아 제거한 뒤 원래 위치에 그대로 출력한다",
            "입력 단계에서 URL 인코딩해 보관하고 출력 직전에 디코딩해서 HTML에 넣는다",
            "브라우저 내장 XSS 필터에 맡기고 서버에서는 별도의 출력 처리를 하지 않는다",
        ],
        "answer": 0,
        "explanation": "특정 태그 제거나 입력 시점 인코딩은 이벤트 핸들러·디코딩 후 출력으로 우회되므로, 출력 시점에 컨텍스트별 이스케이프가 필요합니다.",
    },
    "xss-dom": {
        "question": "`location.hash` 값을 화면에 표시하는 코드를 안전하게 고치는 방법은?",
        "options": [
            "해시 값에서 `<script>` 태그만 정규식으로 제거한 뒤 innerHTML로 삽입한다",
            "encodeURIComponent로 인코딩했다가 decodeURIComponent로 되돌려 innerHTML에 넣는다",
            "서버 응답에 CSP 헤더만 추가하고 innerHTML로 삽입하는 코드는 그대로 둔다",
            "innerHTML 대신 textContent로 넣거나 DOMPurify로 새니타이즈한 뒤 삽입한다",
        ],
        "answer": 3,
        "explanation": "DOM XSS는 데이터가 innerHTML 같은 위험한 싱크에 도달해서 생기므로, 싱크를 안전한 API로 바꾸거나 새니타이즈해야 합니다.",
    },
    "xss-stored": {
        "question": "게시글 본문을 통한 저장형 XSS 방어로 가장 적절한 조합은?",
        "options": [
            "저장 시 입력 검증을 철저히 하면 출력 시 이스케이프는 생략해도 안전하다",
            "저장 전 입력 검증과 출력 시 이스케이프를 함께 적용하고 CSP로 보강한다",
            "게시글 작성 폼에서 JavaScript로 태그 입력을 막고 서버는 그대로 저장한다",
            "`<script>`, `onerror` 등 위험 키워드 목록을 만들어 저장 전에 제거한다",
        ],
        "answer": 1,
        "explanation": "입력 검증만, 클라이언트 차단, 키워드 제거처럼 한 지점만 막으면 우회 경로가 남으므로 저장·출력 양쪽에서 방어해야 합니다.",
    },
    "sql-injection": {
        "question": "SQL Injection의 근본적인 방어 방법은?",
        "options": [
            "입력값의 작은따옴표를 두 개(`''`)로 치환한 뒤 쿼리 문자열에 결합한다",
            "`OR`, `UNION`, `--` 같은 SQL 키워드를 블랙리스트로 걸러낸 뒤 결합한다",
            "DB 에러 메시지를 숨기고 쿼리 실패 시 일반 오류 페이지만 보여준다",
            "Prepared Statement로 값을 바인딩하고 최소 권한 DB 계정을 쓴다",
        ],
        "answer": 3,
        "explanation": "문자 치환·키워드 필터는 인코딩이나 숫자형 컨텍스트로 우회되며, 입력이 쿼리 구조와 분리되어야 근본적으로 막을 수 있습니다.",
    },
    "csrf": {
        "question": "CSRF 방어로 함께 적용해야 하는 조합은?",
        "options": [
            "세션 만료 시간을 짧게 줄이고 모든 페이지에 HTTPS와 HSTS를 적용한다",
            "Referer 헤더에 우리 도메인 문자열이 포함되어 있는지만 확인한다",
            "서버 발급 CSRF 토큰을 요청마다 검증하고 쿠키에 SameSite를 건다",
            "상태를 바꾸는 요청을 POST로만 받도록 바꾸고 토큰 검증은 생략한다",
        ],
        "answer": 2,
        "explanation": "세션 쿠키는 위조 요청에도 자동 전송되므로, 공격자가 알 수 없는 토큰 검증과 교차 사이트 쿠키 전송 제한이 함께 필요합니다.",
    },
    "file-upload": {
        "question": "파일 업로드 기능의 방어로 가장 적절한 것은?",
        "options": [
            "확장자 화이트리스트와 실제 콘텐츠 검사 후 실행 권한 없는 저장소에 둔다",
            "`.php`, `.jsp`, `.asp` 등 위험 확장자를 블랙리스트로 막고 웹 루트에 저장한다",
            "요청의 Content-Type이 image/로 시작하면 원래 파일명 그대로 저장한다",
            "업로드 폼의 accept 속성으로 이미지만 고르게 하고 서버는 그대로 저장한다",
        ],
        "answer": 0,
        "explanation": "블랙리스트·Content-Type·클라이언트 제한은 모두 조작 가능하며, 저장된 파일이 실행되지 않게 하는 조치까지 필요합니다.",
    },
    "sql-injection-blind": {
        "question": "Blind SQL Injection에 대해 Prepared Statement와 함께 적용할 보완책은?",
        "options": [
            "응답 시간을 일정하게 맞추려고 모든 쿼리 뒤에 고정 SLEEP을 추가한다",
            "에러 메시지 노출을 최소화하고 반복 요청에는 속도 제한을 적용한다",
            "참/거짓이 드러나지 않도록 모든 응답을 HTTP 200과 빈 본문으로 통일한다",
            "쿼리 결과를 캐싱해 같은 요청에는 DB 조회 없이 이전 결과를 반환한다",
        ],
        "answer": 1,
        "explanation": "Blind 기법은 반복 요청으로 응답 차이를 관찰하므로, 노출되는 정보를 줄이고 대량 요청 자체를 제한해야 합니다.",
    },
}


def public_quiz(slug):
    """클라이언트 전달용: 정답·해설 제외"""
    quiz = DEFENSE_QUIZZES.get(slug)
    if not quiz:
        return None
    return {"question": quiz["question"], "options": list(quiz["options"])}
