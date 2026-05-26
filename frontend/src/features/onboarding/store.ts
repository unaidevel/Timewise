import { create } from "zustand";

interface TourState {
  shouldRun: boolean;
  startTour: () => void;
  stopTour: () => void;
}

export const useTourStore = create<TourState>((set) => ({
  shouldRun: false,
  startTour: () => set({ shouldRun: true }),
  stopTour: () => set({ shouldRun: false }),
}));
