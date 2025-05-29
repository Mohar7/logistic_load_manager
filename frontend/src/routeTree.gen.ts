// src/routeTree.gen.ts
import {createRootRoute, createRoute} from "@tanstack/react-router";
import {RootComponent} from "./app/__root";
import {Dashboard} from "./app/dashboard/route";
import {CompaniesPage} from "./app/companies/route";
import {CompanyDetailPage} from "./app/companies/$companyId/route";
import {DriversPage} from "./app/drivers/route";
import {DriverDetailPage} from "./app/drivers/$driverId/route";
import {DispatchersPage} from "./app/dispatchers/route";
import {DispatcherDetailPage} from "./app/dispatchers/$dispatcherId/route";
import {LoadsPage} from "./app/loads/route";
import {LoadDetailPage} from "./app/loads/$loadId/route";
import {LoginPage} from "./app/login/route";
import {IndexComponent} from "./app/index/route";

// First, create the root route
export const rootRoute = createRootRoute({
  component: RootComponent,
});

// Create other routes
export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: IndexComponent,
});

export const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "login",
  component: LoginPage,
});

export const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "dashboard",
  component: Dashboard,
});

// Companies routes
export const companiesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "companies",
  component: CompaniesPage,
});

export const companyDetailsRoute = createRoute({
  getParentRoute: () => companiesRoute,
  path: "$companyId",
  component: CompanyDetailPage,
});

// Drivers routes
export const driversRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "drivers",
  component: DriversPage,
});

export const driverDetailsRoute = createRoute({
  getParentRoute: () => driversRoute,
  path: "$driverId",
  component: DriverDetailPage,
});

// Dispatchers routes
export const dispatchersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "dispatchers",
  component: DispatchersPage,
});

export const dispatcherDetailsRoute = createRoute({
  getParentRoute: () => dispatchersRoute,
  path: "$dispatcherId",
  component: DispatcherDetailPage,
});

// Loads routes
export const loadsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "loads",
  component: LoadsPage,
});

export const loadDetailsRoute = createRoute({
  getParentRoute: () => loadsRoute,
  path: "$loadId",
  component: LoadDetailPage,
});

// Register all routes
export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  dashboardRoute,
  companiesRoute.addChildren([
    companyDetailsRoute,
  ]),
  driversRoute.addChildren([
    driverDetailsRoute,
  ]),
  dispatchersRoute.addChildren([
    dispatcherDetailsRoute,
  ]),
  loadsRoute.addChildren([
    loadDetailsRoute,
  ]),
]);