"""1회차 개념 학습 확인 문제 (과목별 4지선다, 5문항 이상).

과목 정보 탭(원리 · 비유 · 피해 · 방어)을 읽고 판단해서 풀 수 있도록 출제한다.
3회차 방어 퀴즈(50문항 은행)와는 별개 문항이다.
문항이 5개 미만인 과목은 확인 문제가 "준비 중"으로 표시된다.

문항 형식:
    {
        "id": "cc-<과목약어>-<번호>",      # 예: cc-ci-1 (과목 안에서 고유)
        "question": "질문",
        "options": ["보기1", "보기2", "보기3", "보기4"],
        "answer": 0,                       # 정답 보기 번호 (0~3)
        "explanation": "채점 후 보여줄 해설",
    }
"""

CONCEPT_QUESTIONS = {
    "command-injection": [],
    "xss-reflected": [],
    "xss-dom": [],
    "xss-stored": [],
    "sql-injection": [],
    "sql-injection-blind": [],
    "file-upload": [],
    "csrf": [],
}
