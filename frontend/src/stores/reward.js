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

  async function claim(id) {
    if (claiming.value) return;
    claiming.value = true;
    try {
      const { data } = await client.post(`/rewards/${id}/claim`);
      items.value = items.value.filter((item) => item.id !== id);
      applyProfile(data.profile);
    } finally {
      claiming.value = false;
    }
  }

  async function claimAll() {
    if (claiming.value || !items.value.length) return;
    claiming.value = true;
    try {
      const { data } = await client.post("/rewards/claim-all");
      items.value = [];
      applyProfile(data.profile);
    } finally {
      claiming.value = false;
    }
  }

  function reset() {
    items.value = [];
  }

  return { items, count, claiming, fetchPending, claim, claimAll, reset };
});
