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

  return { items, count, claiming, fetchPending, fetchCourseRewards, claimTask, reset };
});
