import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  LoginRequest,
  RegisterRequest,
  UpdateEmailRequest,
  UpdateNameRequest,
  UpdatePasswordRequest,
} from "@/client";
import {
  getMeApiV1AuthMeGet,
  loginUserApiV1AuthLoginPost,
  logoutUserApiV1AuthLogoutPost,
  registerApiV1AuthRegisterPost,
  updateMyEmailApiV1AuthMeEmailPut,
  updateMyNameApiV1AuthMeNamePut,
  updateMyPasswordApiV1AuthMePasswordPut,
} from "@/client";
import { useTenantStore } from "@/features/tenants/store";
import { useAuthStore } from "./store";

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const { data, error } = await loginUserApiV1AuthLoginPost({ body });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: (data) => setSession(data),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (body: RegisterRequest) => {
      const { data, error } = await registerApiV1AuthRegisterPost({ body });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      try {
        await logoutUserApiV1AuthLogoutPost({});
      } catch {
        /* ignore — local logout still happens */
      }
    },
    onSettled: () => {
      logout();
      useTenantStore.getState().setCurrentTenantId(null);
      qc.clear();
    },
  });
}

export function useMe() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ["auth", "me"],
    enabled: Boolean(token),
    queryFn: async () => {
      const { data, error } = await getMeApiV1AuthMeGet({});
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useUpdateMyName() {
  const setUser = useAuthStore((s) => s.setUser);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: UpdateNameRequest) => {
      const { data, error } = await updateMyNameApiV1AuthMeNamePut({ body });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: (data) => {
      setUser(data);
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useUpdateMyEmail() {
  const setUser = useAuthStore((s) => s.setUser);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: UpdateEmailRequest) => {
      const { data, error } = await updateMyEmailApiV1AuthMeEmailPut({ body });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: (data) => {
      setUser(data);
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useUpdateMyPassword() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: async (body: UpdatePasswordRequest) => {
      const { data, error } = await updateMyPasswordApiV1AuthMePasswordPut({ body });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: (data) => setSession(data),
  });
}
