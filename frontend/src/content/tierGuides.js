// SecuQuest — 실습 레벨(하 → 중 → 상 → 안전) 공통 안내
// 발표 피드백 반영: 레벨을 섞지 않고 순서대로 학습하도록, 레벨마다 의미를 고정해 보여준다.
// 레벨별 세부 접근 방법은 서버가 제공하는 단계별 힌트에서 확인한다.
// © 2026 5팀_Security Learning Platform

export const TIER_META = {
  low: { label: "하", name: "Low", summary: "방어가 없는 상태에서 취약점의 기본 원리를 확인합니다." },
  medium: { label: "중", name: "Medium", summary: "단순한 방어가 추가됩니다. 그 방어가 왜 충분하지 않은지 생각해 봅니다." },
  high: { label: "상", name: "High", summary: "방어가 강화됩니다. 금지 목록 방식 방어의 한계를 이해합니다." },
  impossible: { label: "안전", name: "Impossible", summary: "올바른 방어 코드가 적용됩니다. 공격이 왜 막히는지 확인하고 방어 원리를 정리합니다." },
};
