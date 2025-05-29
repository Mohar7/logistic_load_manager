// src/routeConfig.ts
import {string} from "zod";

export const routePaths = {
  '/': {},
  '/index': {},
  '/login': {},
  '/dashboard': {},
  '/companies': {},
  '/companies/$companyId': { companyId: string },
  '/drivers': {},
  '/drivers/$driverId': { driverId: string },
} as const;

declare module '@tanstack/react-router' {
  interface Register {
    routePaths: typeof routePaths
  }
}