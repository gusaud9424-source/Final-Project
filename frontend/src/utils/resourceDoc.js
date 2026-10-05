// SecuQuest — 자료실 학습 문서(HTML) 생성
// 과목 상세에서 쓰는 기존 콘텐츠(courseGuides · enroll 상세 · 레벨 안내 · 미션 안내)를 모아
// 내려받아 브라우저에서 바로 읽을 수 있는 단일 HTML 문서로 만든다.
// 색은 하드코딩하지 않고 현재 화면의 디자인 토큰(--sq-*) 값을 읽어 문서에 넣는다.
// © 2026 5팀_Security Learning Platform

import { COURSE_GUIDES, MISSION_GUIDE } from "@/content/courseGuides";
import { TIER_META } from "@/content/tierGuides";

const TIER_ORDER = ["low", "medium", "high", "impossible"];

// HTML 특수문자 이스케이프 (문서에 들어가는 모든 텍스트에 적용)
function esc(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// 백틱(`)으로 감싼 구간을 <code> 로 표시 (이스케이프 후 변환)
function rich(text) {
  return esc(text)
    .split("`")
    .map((part, i) => (i % 2 === 1 ? `<code>${part}</code>` : part))
    .join("");
}

// 현재 화면의 디자인 토큰 값 읽기 (문서는 앱 밖에서 열리므로 실제 값을 복사해 둔다)
function readTokens() {
  const style = getComputedStyle(document.documentElement);
  const pick = (name) => style.getPropertyValue(name).trim();
  return {
    accent: pick("--sq-color-accent"),
    onAccent: pick("--sq-color-on-accent"),
    text: pick("--sq-text-main"),
    sub: pick("--sq-text-sub"),
    border: pick("--sq-card-border"),
    card: pick("--sq-bg-card"),
    subtle: pick("--sq-badge-round-bg"),
    font: pick("--sq-font-family"),
  };
}

function section(no, title, body) {
  return `<section><h2><span class="no">${no}</span>${esc(title)}</h2>${body}</section>`;
}

export function buildResourceDoc(course) {
  const guide = COURSE_GUIDES[course.id] || {};
  const info = guide.info || {};
  const practice = guide.practice || {};
  const detail = course.detail || {};
  const t = readTokens();
  const today = new Date().toLocaleDateString("ko-KR");

  const parts = [];
  let no = 1;

  parts.push(
    section(
      no++,
      "한눈에 보기",
      `<div class="box">${rich(info.summary || detail.summary)}</div>` +
        (detail.summary && info.summary ? `<p>${rich(detail.summary)}</p>` : "")
    )
  );

  if (info.analogy) {
    parts.push(section(no++, "쉽게 이해하기 (비유)", `<p>${rich(info.analogy)}</p>`));
  }

  if (info.impact) {
    parts.push(section(no++, "방어에 실패하면", `<div class="box warn">${rich(info.impact)}</div>`));
  }

  if (info.defense || detail.defense) {
    parts.push(
      section(
        no++,
        "어떻게 방어하나",
        (info.defense ? `<p>${rich(info.defense)}</p>` : "") +
          (detail.defense ? `<div class="box ok"><strong>핵심 원칙</strong><br>${rich(detail.defense)}</div>` : "")
      )
    );
  }

  if (practice.goal) {
    const steps = (practice.steps || []).map((s) => `<li>${rich(s)}</li>`).join("");
    parts.push(
      section(
        no++,
        "실습 안내",
        `<dl>
          <dt>실습 목적</dt><dd>${rich(practice.goal)}</dd>
          <dt>왜 배우나</dt><dd>${rich(practice.why)}</dd>
          <dt>실습 화면</dt><dd>${rich(practice.scenario)}</dd>
        </dl>
        <h3>진행 방법</h3><ol>${steps}</ol>
        ${practice.tip ? `<div class="box">💡 ${rich(practice.tip)}</div>` : ""}`
      )
    );
  }

  const tierRows = TIER_ORDER.map(
    (key) => `<tr><td>${esc(TIER_META[key].label)} (${esc(TIER_META[key].name)})</td><td>${esc(TIER_META[key].summary)}</td></tr>`
  ).join("");
  parts.push(
    section(
      no++,
      "레벨 구성 (하 → 중 → 상 → 안전)",
      `<p>앞 레벨을 통과해야 다음 레벨이 열립니다. 레벨을 클리어할 때마다 보물상자로 보상이 지급되며,
       막히면 실습 페이지의 <strong>힌트 보기</strong>에서 레벨별 단계 힌트를 확인할 수 있습니다.</p>
       <table><thead><tr><th>레벨</th><th>학습 포인트</th></tr></thead><tbody>${tierRows}</tbody></table>`
    )
  );

  const missionRows = ["concept", "practice", "defense"]
    .map((key, i) => {
      const m = MISSION_GUIDE[key];
      return m ? `<tr><td>${i + 1}회차 · ${esc(m.title)}</td><td>${rich(m.desc)}</td></tr>` : "";
    })
    .join("");
  parts.push(
    section(
      no++,
      "미션 수행 가이드",
      `<table><thead><tr><th>미션</th><th>수행 방법</th></tr></thead><tbody>${missionRows}</tbody></table>
       <p>미션을 완수하면 과목 상세 &gt; 미션 탭 오른쪽 칸에 보상이 표시되며, 클릭해서 받습니다.</p>`
    )
  );

  const title = `${course.title} 학습 자료`;
  return `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} — SecuQuest</title>
<style>
  body { margin: 0; background: ${t.card}; color: ${t.text}; font-family: ${t.font}; line-height: 1.75; }
  main { max-width: 820px; margin: 0 auto; padding: 48px 24px 64px; }
  header { border-bottom: 3px solid ${t.accent}; padding-bottom: 20px; margin-bottom: 32px; }
  .brand { color: ${t.accent}; font-weight: 800; letter-spacing: 0.5px; font-size: 14px; }
  h1 { margin: 6px 0 8px; font-size: 32px; }
  .meta { color: ${t.sub}; font-size: 14px; }
  .badge { display: inline-block; padding: 2px 10px; background: ${t.subtle}; color: ${t.accent}; font-size: 13px; font-weight: 700; margin-right: 8px; }
  section { margin-bottom: 36px; }
  h2 { font-size: 22px; margin: 0 0 12px; display: flex; align-items: center; gap: 10px; }
  h2 .no { display: inline-flex; width: 30px; height: 30px; align-items: center; justify-content: center; background: ${t.accent}; color: ${t.onAccent}; font-size: 15px; }
  h3 { font-size: 17px; margin: 20px 0 8px; }
  .box { padding: 14px 18px; border-left: 4px solid ${t.accent}; background: ${t.subtle}; margin: 12px 0; }
  .box.warn { border-left-color: ${t.sub}; }
  .box.ok { border-left-color: ${t.accent}; }
  dl { margin: 0; } dt { font-weight: 700; margin-top: 12px; } dd { margin: 4px 0 0; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 15px; }
  th, td { border: 1px solid ${t.border}; padding: 10px 12px; text-align: left; vertical-align: top; }
  th { background: ${t.subtle}; }
  code { background: ${t.subtle}; padding: 1px 6px; font-size: 0.92em; }
  footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid ${t.border}; color: ${t.sub}; font-size: 13px; }
  @media print { main { padding: 0; } section { break-inside: avoid; } }
</style>
</head>
<body>
<main>
  <header>
    <div class="brand">SECU EDUCATION · SecuQuest 자료실</div>
    <h1>${esc(course.title)}</h1>
    <div class="meta"><span class="badge">${esc(course.difficulty)}</span>${esc(course.desc)} · 내려받은 날짜 ${esc(today)}</div>
  </header>
  ${parts.join("\n")}
  <footer>
    SecuQuest는 5팀_Security Learning Platform의 부트캠프 캡스톤 학습 프로젝트입니다.<br>
    실습 구성은 DVWA(Damn Vulnerable Web Application, GPLv3)의 레벨 구조를 참고했습니다.<br>
    © 2026 5팀_Security Learning Platform. All rights reserved.
  </footer>
</main>
</body>
</html>`;
}

// 문서를 HTML 파일로 내려받기
export function downloadResourceDoc(course) {
  const html = buildResourceDoc(course);
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `SecuQuest_${course.id}_학습자료.html`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
