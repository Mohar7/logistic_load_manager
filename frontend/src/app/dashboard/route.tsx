import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {StatsCard} from "./-components/stats-card";
import {Building2, DollarSign, Package, Truck} from "lucide-react";
import {useLoads} from "@/app/loads/-api/load-api";
import {useDrivers} from "@/app/drivers/-api/driver-api";
import {useCompanies} from "@/app/companies/-api/company-api";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";

export function Dashboard() {
  const { data: loads = [], isLoading: isLoadingLoads } = useLoads(0, 5);
  const { data: drivers = [], isLoading: isLoadingDrivers } = useDrivers();
  const { data: companies = [] } = useCompanies();

  // In a real app, you'd fetch this data from your API
  const stats = {
    totalLoads: loads.length || 0,
    loadsChange: 12,
    activeDrivers: drivers.length || 0,
    driversChange: 3,
    activeCompanies: companies.length || 0,
    companiesChange: 1,
    loadRevenue: "$47,625",
    revenueChange: 8.2,
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your logistics operations</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Total Loads"
            value={stats.totalLoads}
            change={stats.loadsChange}
            icon={<Package />}
          />
          <StatsCard
            title="Active Drivers"
            value={stats.activeDrivers}
            change={stats.driversChange}
            icon={<Truck />}
          />
          <StatsCard
            title="Active Companies"
            value={stats.activeCompanies}
            change={stats.companiesChange}
            icon={<Building2 />}
          />
          <StatsCard
            title="Total Revenue"
            value={stats.loadRevenue}
            change={stats.revenueChange}
            icon={<DollarSign />}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {/* Display recent loads */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Loads</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingLoads ? (
                <p className="text-center py-4">Loading...</p>
              ) : loads.length > 0 ? (
                <div className="space-y-4">
                  {/* Map through loads and display them */}
                  <p>List of recent loads would go here</p>
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">No active loads available</p>
              )}
            </CardContent>
          </Card>
          
          {/* Display driver status */}
          <Card>
            <CardHeader>
              <CardTitle>Driver Status</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingDrivers ? (
                <p className="text-center py-4">Loading...</p>
              ) : drivers.length > 0 ? (
                <div className="space-y-4">
                  {/* Map through drivers and display them */}
                  <p>List of drivers would go here</p>
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">No active drivers available</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}