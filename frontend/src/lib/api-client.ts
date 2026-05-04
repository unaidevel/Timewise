import { client } from "@/client/client.gen";
import { useAuthStore } from "@/features/auth/store";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

client.setConfig({ baseUrl: API_BASE_URL });

client.interceptors.request.use((request) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    request.headers.set("Authorization", `Bearer ${token}`);
  }
  return request;
});

client.interceptors.response.use((response) => {
  if (response.status === 401) {
    useAuthStore.getState().logout();
  }
  return response;
});
