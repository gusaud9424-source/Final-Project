export function getErrorMessage(error, fallback) {
  if (error.response?.status === 429) {
    return "요청이 너무 많습니다. 잠시 후 다시 시도하세요.";
  }
  return error.response?.data?.message || fallback;
}
