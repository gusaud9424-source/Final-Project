<!--
  SecuQuest — 관리자용 전체 학생 진도 테이블
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
<template>
  <div class="sq-students">
    <p v-if="loading" class="sq-students__status">불러오는 중...</p>
    <p v-else-if="errorMessage" class="sq-students__error">{{ errorMessage }}</p>
    <p v-else-if="!students.length" class="sq-students__status">학생 데이터가 없습니다.</p>

    <div v-else class="sq-students__table-wrap">
      <table class="sq-students__table">
        <thead>
          <tr>
            <th>학생</th>
            <th>이메일</th>
            <th>강의별 진도</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.id">
            <td>{{ student.name }}</td>
            <td>{{ student.email }}</td>
            <td>
              <div class="sq-students__courses">
                <span
                  v-for="course in student.courses"
                  :key="course.id"
                  class="sq-students__badge"
                >
                  {{ course.title }} {{ course.percent }}%
                </span>
                <span v-if="!student.courses.length" class="sq-students__empty">수강 없음</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import client from "@/api/client";
import { getErrorMessage } from "@/api/errors";

const students = ref([]);
const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  try {
    const { data } = await client.get("/admin/students");
    students.value = data.students;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "학생 목록을 불러오지 못했습니다.");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.sq-students {
  padding: var(--sq-card-padding);
  border: 1px solid var(--sq-card-border);
  border-radius: var(--sq-radius-none);
  background: var(--sq-bg-card);
  box-shadow: var(--sq-card-shadow);
}

.sq-students__status {
  margin: 0;
  font-size: 14px;
  color: var(--sq-text-sub);
}

.sq-students__error {
  margin: 0;
  font-size: 14px;
  color: var(--sq-badge-absent-text);
}

.sq-students__table-wrap {
  overflow-x: auto;
}

.sq-students__table {
  width: 100%;
  border-collapse: collapse;
}

.sq-students__table th,
.sq-students__table td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid var(--sq-card-border);
  font-size: 14px;
  color: var(--sq-text-main);
  white-space: nowrap;
}

.sq-students__table th {
  font-size: 13px;
  color: var(--sq-text-sub);
  font-weight: 600;
}

.sq-students__courses {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  white-space: normal;
}

.sq-students__badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: var(--sq-radius-none);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  background: var(--sq-badge-round-bg);
  color: var(--sq-badge-round-text);
}

.sq-students__empty {
  font-size: 13px;
  color: var(--sq-text-sub);
}
</style>
