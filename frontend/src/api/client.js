import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

let csrfToken = null;

export function resetCsrfToken() {
  csrfToken = null;
}

async function ensureCsrfToken() {
  if (!csrfToken) {
    const { data } = await client.get("/auth/csrf");
    csrfToken = data.csrf_token;
  }
  return csrfToken;
}

client.interceptors.request.use(async (config) => {
  const method = (config.method || "get").toLowerCase();
  const isCsrfEndpoint = (config.url || "").includes("/auth/csrf");
  if (method !== "get" && !isCsrfEndpoint) {
    config.headers["X-CSRFToken"] = await ensureCsrfToken();
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const isCsrfError = response?.status === 400 && response?.data?.error === "csrf";

    if (isCsrfError && config && !config._csrfRetried) {
      config._csrfRetried = true;
      resetCsrfToken();
      config.headers["X-CSRFToken"] = await ensureCsrfToken();
      return client(config);
    }
    return Promise.reject(error);
  }
);

export default client;
