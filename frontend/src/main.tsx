import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {createRouter, RouterProvider,} from "@tanstack/react-router";
import {StrictMode} from "react";
import {createRoot} from "react-dom/client";
import "./index.css";
// Import the route tree
import {ThemeProvider} from "./components/theme-provider";
import {Spinner} from "./components/ui/spinner";
import {routeTree} from "./routeTree.gen";

// Create instance of tanstack query
export const queryClient = new QueryClient();

// Create a new router instance
const router = createRouter({
  routeTree,
  defaultPendingComponent: () => (
    <div className={`p-2 text-2xl`}>
      <Spinner size={"medium"} />
    </div>
  ),
  defaultErrorComponent: ({ error }) => (
    <div className="p-2 text-red-500">An error occurred: {error.message}</div>
  ),
  context: {
    queryClient,
  },
  defaultPreload: "intent",
  defaultPreloadStaleTime: 0,
  scrollRestoration: true,
});

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" attribute="class">
        <RouterProvider router={router} />
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>
);