import { create } from "zustand";

type TourMode = "demo" | "scratch";

interface TourState {
  shouldRun: boolean;
  tourMode: TourMode;
  startTour: () => void;
  startScratchTour: () => void;
  stopTour: () => void;
}

export const useTourStore = create<TourState>((set) => ({
  shouldRun: false,
  tourMode: "demo",
  startTour: () => set({ shouldRun: true, tourMode: "demo" }),
  startScratchTour: () => set({ shouldRun: true, tourMode: "scratch" }),
  stopTour: () => set({ shouldRun: false }),
}));
