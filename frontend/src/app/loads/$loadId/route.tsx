import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {useState} from "react";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useAssignDriverToLoad, useLoad, useNotifyDriver} from "../-api/load-api";
import {useDrivers} from "@/app/drivers/-api/driver-api";
import {Button} from "@/components/ui/button";
import {ArrowLeft, Bell, Calendar, DollarSign, MapPin, Route as RouteIcon, SendHorizontal, Truck, User} from "lucide-react";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {Separator} from "@/components/ui/separator";
import {formatCurrency, formatDate, formatNumber} from "@/lib/utils";
import {toast} from "sonner";
import type {Driver} from "@/types/models";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from "@/components/ui/select";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow,} from "@/components/ui/table";
import {Alert, AlertDescription} from "@/components/ui/alert";

export const Route = createFileRoute('/loads/$loadId')({
  component: LoadDetailPage,
});

export function LoadDetailPage() {
  const { loadId } = Route.useParams();
  const id = parseInt(loadId);
  const { data: load, isLoading } = useLoad(id);
  const { data: drivers = [] } = useDrivers();
  const [selectedDriverId, setSelectedDriverId] = useState<number | undefined>(undefined);
  const assignDriverToLoad = useAssignDriverToLoad();
  const notifyDriver = useNotifyDriver();
  const navigate = useNavigate();

  const handleAssignDriver = async () => {
    if (!selectedDriverId) {
      toast.error("Please select a driver");
      return;
    }

    try {
      await assignDriverToLoad.mutateAsync({
        loadId: id,
        driverId: selectedDriverId,
      });
      toast.success("Driver assigned successfully");
      setSelectedDriverId(undefined);
    } catch (error) {
      toast.error("Failed to assign driver");
      console.error(error);
    }
  };

  const handleNotifyDriver = async () => {
    const driverToNotify = selectedDriverId || (load?.assigned_driver ?
      drivers.find(d => d.name === load.assigned_driver)?.id : undefined);
    
    if (!driverToNotify) {
      toast.error("No driver to notify");
      return;
    }

    try {
      await notifyDriver.mutateAsync({
        loadId: id,
        driverId: driverToNotify,
      });
      toast.success("Notification sent to driver");
    } catch (error) {
      toast.error("Failed to send notification");
      console.error(error);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="text-muted-foreground">Loading load details...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!load) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Alert className="max-w-md">
            <AlertDescription>
              Load not found. Please check the ID and try again.
            </AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  const getStatusBadge = () => {
    if (load.assigned_driver) {
      return <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100">Assigned</Badge>;
    }
    return <Badge variant="secondary">Unassigned</Badge>;
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate({ to: "/loads" })}
              className="rounded-full"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Load #{load.trip_id}</h1>
              <p className="text-muted-foreground">Manage load details and driver assignment</p>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(load.rate)}</p>
                <p className="text-sm text-muted-foreground">Total Rate</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <RouteIcon className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatNumber(load.distance || 0)}</p>
                <p className="text-sm text-muted-foreground">Miles</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(load.rate_per_mile)}</p>
                <p className="text-sm text-muted-foreground">Per Mile</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <User className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-lg font-semibold truncate">
                  {load.assigned_driver || "No Driver"}
                </p>
                <p className="text-sm text-muted-foreground">Assigned Driver</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Load Details */}
          <div className="xl:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPin className="h-5 w-5" />
                  <span>Route Information</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-green-700">Pickup Location</h3>
                        <p className="text-sm text-muted-foreground">
                          {load.pickup_facility || load.pickup_address || "Not specified"}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-3">
                      <div className="w-3 h-3 bg-red-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-red-700">Dropoff Location</h3>
                        <p className="text-sm text-muted-foreground">
                          {load.dropoff_facility || load.dropoff_address || "Not specified"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <h3 className="font-medium">Start Time</h3>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(load.start_time, true)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <h3 className="font-medium">End Time</h3>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(load.end_time, true)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Legs Table */}
            {load.legs && load.legs.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Load Legs</span>
                    <Badge variant="outline">{load.legs.length} legs</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Leg ID</TableHead>
                          <TableHead>Pickup</TableHead>
                          <TableHead>Dropoff</TableHead>
                          <TableHead>Pickup Time</TableHead>
                          <TableHead>Dropoff Time</TableHead>
                          <TableHead>FSC</TableHead>
                          <TableHead>Distance</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {load.legs.map((leg) => (
                          <TableRow key={leg.id}>
                            <TableCell className="font-medium">{leg.leg_id}</TableCell>
                            <TableCell>{leg.pickup_address || leg.pickup_facility_id || "N/A"}</TableCell>
                            <TableCell>{leg.dropoff_address || leg.dropoff_facility_id || "N/A"}</TableCell>
                            <TableCell>{leg.pickup_time ? formatDate(leg.pickup_time, true) : "N/A"}</TableCell>
                            <TableCell>{leg.dropoff_time ? formatDate(leg.dropoff_time, true) : "N/A"}</TableCell>
                            <TableCell>{formatCurrency(leg.fuel_sur_charge)}</TableCell>
                            <TableCell>{leg.distance ? formatNumber(leg.distance, 1) + " mi" : "N/A"}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Driver Assignment Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Truck className="h-5 w-5" />
                  <span>Driver Assignment</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {load.assigned_driver && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-green-100 rounded-full">
                        <User className="h-4 w-4 text-green-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-green-900">Current Driver</h3>
                        <p className="text-green-700">{load.assigned_driver}</p>
                      </div>
                    </div>
                  </div>
                )}

                <Separator />

                <div className="space-y-4">
                  <h3 className="font-semibold">Assign New Driver</h3>
                  <Select
                    onValueChange={(value) => setSelectedDriverId(parseInt(value))}
                    value={selectedDriverId?.toString()}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a driver" />
                    </SelectTrigger>
                    <SelectContent>
                      {drivers.map((driver: Driver) => (
                        <SelectItem key={driver.id} value={driver.id.toString()}>
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span>{driver.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Button
                    onClick={handleAssignDriver}
                    disabled={assignDriverToLoad.isPending || !selectedDriverId}
                    className="w-full"
                    size="lg"
                  >
                    <Truck className="mr-2 h-4 w-4" />
                    {assignDriverToLoad.isPending ? "Assigning..." : "Assign Driver"}
                  </Button>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="font-semibold">Driver Communication</h3>
                  <Button
                    variant="outline"
                    onClick={handleNotifyDriver}
                    disabled={notifyDriver.isPending || (!selectedDriverId && !load.assigned_driver)}
                    className="w-full"
                    size="lg"
                  >
                    <Bell className="mr-2 h-4 w-4" />
                    {notifyDriver.isPending ? "Sending..." : "Send Notification"}
                  </Button>
                  
                  {(!selectedDriverId && !load.assigned_driver) && (
                    <p className="text-xs text-muted-foreground text-center">
                      Assign a driver first to send notifications
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Load Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Load Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Trip ID</span>
                  <span className="font-medium">{load.trip_id}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Total Rate</span>
                  <span className="font-medium">{formatCurrency(load.rate)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Distance</span>
                  <span className="font-medium">{formatNumber(load.distance || 0)} mi</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Rate/Mile</span>
                  <span className="font-medium">{formatCurrency(load.rate_per_mile)}</span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Status</span>
                  {getStatusBadge()}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}