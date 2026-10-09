import { defineStore } from "pinia";
import { ref } from "vue";
import client from "@/api/client";

export const useProfileStore = defineStore("profile", () => {
  const nickname = ref("");
  const level = ref(1);
  const currentXp = ref(0);
  const xpForNextLevel = ref(null);
  const totalXp = ref(0);
  const points = ref(0);
  const loaded = ref(false);

  async function fetchProfile() {
    const { data } = await client.get("/profile");
    nickname.value = data.nickname;
    level.value = data.level;
    currentXp.value = data.currentXp;
    xpForNextLevel.value = data.xpForNextLevel;
    totalXp.value = data.totalXp;
    points.value = data.points;
    loaded.value = true;
  }

  return {
    nickname,
    level,
    currentXp,
    xpForNextLevel,
    totalXp,
    points,
    loaded,
    fetchProfile,
  };
});
