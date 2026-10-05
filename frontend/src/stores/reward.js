import { defineStore } from "pinia";
import { computed, ref } from "vue";
import client from "@/api/client";
import { useProfileStore } from "@/stores/profile";

export const useRewardStore = defineStore("reward", () => {
  const items = ref([]);
  const claiming = ref(false);
  const count = computed(() => items.value.length);

  async function fetchPending() {
    const { data } = await client.get("/rewards/pending");
    items.value = data.items;
  }

  // 수령 응답의 보유치로 프로필 즉시 갱신
  function applyProfile(profile) {
    const profileStore = useProfileStore();
    profileStore.level = profile.level;
    profileStore.currentXp = profile.currentXp;
    profileStore.xpForNextLevel = profile.xpForNextLevel;
    profileStore.totalXp = profile.totalXp;
    profileStore.points = profile.points;
  }

  // 보물상자 개별 수령 (미션 외 보상)
  async function claim(id) {
    if (claiming.value) return;
    claiming.value = true;
    try {
      const { data } = await client.post(`/rewards/${id}/claim`);
      items.value = items.value.filter((item) => item.id !== id);
      applyProfile(data.profile);
      // 수령으로 레벨이 오르면 서버가 레벨업 보상을 새로 만들므로 목록을 다시 불러온다
      await fetchPending().catch(() => {});
    } finally {
      claiming.value = false;
    }
  }

  // 보물상자 일괄 수령 (미션 외 보상)
  async function claimAll() {
    if (claiming.value || !items.value.length) return;
    claiming.value = true;
    try {
      const { data } = await client.post("/rewards/claim-all");
      items.value = [];
      applyProfile(data.profile);
      // 일괄 수령으로 생긴 레벨업 보상을 바로 표시
      await fetchPending().catch(() => {});
    } finally {
      claiming.value = false;
    }
  }

  function reset() {
    items.value = [];
  }

  // 미션 탭: 과목의 미션별 보상 상태 조회 / 미션 보상 수령
  async function fetchCourseRewards(slug) {
    const { data } = await client.get(`/courses/${slug}/rewards`);
    return data.rewards;
  }

  async function claimTask(slug, taskKey) {
    if (claiming.value) return null;
    claiming.value = true;
    try {
      const { data } = await client.post(`/courses/${slug}/rewards/${taskKey}/claim`);
      applyProfile(data.profile);
      await fetchPending().catch(() => {});
      return data;
    } finally {
      claiming.value = false;
    }
  }

  return {
    items,
    count,
    claiming,
    fetchPending,
    claim,
    claimAll,
    fetchCourseRewards,
    claimTask,
    reset,
  };
});
