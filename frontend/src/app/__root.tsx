import {Toaster} from "@/components/ui/sonner";
import {Outlet} from "@tanstack/react-router";

export function RootComponent() {
  return (
    <>
      <Outlet />
      <Toaster />
    </>
  );
}