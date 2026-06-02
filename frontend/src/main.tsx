import { QueryClientProvider } from "@tanstack/react-query";
import { domMax, LazyMotion, MotionConfig } from "framer-motion";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";
import { RouterProvider } from "react-router";
import { Toaster } from "@/components/shadcn/sonner";
import "./index.css";
import "./lib/api-client";
import { router } from "./app/router";
import i18n from "./lib/i18n";
import { queryClient } from "./lib/query-client";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={queryClient}>
        <MotionConfig reducedMotion="user">
          <LazyMotion features={domMax} strict>
            <RouterProvider router={router} />
            <Toaster richColors position="top-right" />
          </LazyMotion>
        </MotionConfig>
      </QueryClientProvider>
    </I18nextProvider>
  </StrictMode>,
);
