import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useCreateLoad, useLoads, useParseLoad, useDeleteLoad, useUpdateLoad } from "./-api/load-api";
import { useDispatchers } from "@/app/dispatchers/-api/dispatcher-api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  ArrowRight,
  DollarSign,
  Edit,
  Eye,
  Plus,
  Route as RouteIcon,
  Search,
  Truck,
  TruckIcon,
  Trash2,
  Calendar,
  ChevronDown,
  ChevronUp,
  AlertTriangle
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { Load } from "@/types/models";
import { LoadForm } from "./-components/load-form";
import { LoadEditForm } from "./-components/load-edit-form";
import { DataTable } from "@/components/ui/data-table";
import { formatCurrency, formatDate, formatNumber } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import { toast } from "sonner";

export const Route = createFileRoute('/loads')({
  component: LoadsPage,
});

// Simplified dialog state
type DialogState = {
  type: 'none' | 'create' | 'edit' | 'details';
  load?: Load;
};

export function LoadsPage() {
  // Simplified state management
  const [dialog, setDialog] = useState<DialogState>({ type: 'none' });
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('cards');
  
  // API hooks
  const { data: loads = [], isLoading, error, refetch } = useLoads();
  const { data: dispatchers = [] } = useDispatchers();
  const parseLoad = useParseLoad();
  const createLoad = useCreateLoad();
  const deleteLoad = useDeleteLoad();
  const updateLoad = useUpdateLoad();
  const navigate = useNavigate();

  // Derived state
  const filteredLoads = loads.filter(load => {
    const searchLower = searchQuery.toLowerCase();
    return (
      load.trip_id?.toLowerCase().includes(searchLower) ||
      load.pickup_facility?.toLowerCase().includes(searchLower) ||
      load.dropoff_facility?.toLowerCase().includes(searchLower) ||
      load.pickup_address?.toLowerCase().includes(searchLower) ||
      load.dropoff_address?.toLowerCase().includes(searchLower) ||
      load.assigned_driver?.toLowerCase().includes(searchLower)
    );
  });

  const stats = {
    total: loads.length,
    assigned: loads.filter(load => load.assigned_driver).length,
    unassigned: loads.filter(load => !load.assigned_driver).length,
    totalRevenue: loads.reduce((sum, load) => sum + (load.rate || 0), 0),
    totalDistance: loads.reduce((sum, load) => sum + (load.distance || 0), 0),
  };

  // Event handlers
  const openDialog = (type: DialogState['type'], load?: Load) => {
    setDialog({ type, load });
  };

  const closeDialog = () => {
    setDialog({ type: 'none' });
  };

  const toggleCardExpansion = (loadId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(loadId)) {
      newExpanded.delete(loadId);
    } else {
      newExpanded.add(loadId);
    }
    setExpandedCards(newExpanded);
  };

  // CRUD operations with proper error handling
  const handleCreateLoad = async ({ text, dispatcherId }: { text: string; dispatcherId?: number }) => {
    try {
      await createLoad.mutateAsync({ text, dispatcherId });
      toast.success("Load created successfully");
      closeDialog();
    } catch (error) {
      console.error('Create error:', error);
      const message = error instanceof Error ? error.message : "Failed to create load";
      toast.error(message);
    }
  };

  const handleUpdateLoad = async (updateData: Partial<Load>) => {
    if (!dialog.load) return;
    
    try {
      await updateLoad.mutateAsync({
        loadId: dialog.load.id,
        updateData
      });
      toast.success("Load updated successfully");
      closeDialog();
    } catch (error) {
      console.error('Update error:', error);
      const message = error instanceof Error ? error.message : "Failed to update load";
      toast.error(message);
    }
  };

  const handleDeleteLoad = async (loadId: number) => {
    try {
      await deleteLoad.mutateAsync(loadId);
      toast.success("Load deleted successfully");
    } catch (error) {
      console.error('Delete error:', error);
      const message = error instanceof Error ? error.message : "Failed to delete load";
      toast.error(message);
    }
  };

  // Table columns definition
  const columns: ColumnDef<Load>[] = [
    {
      accessorKey: "trip_id",
      header: "Trip ID",
      cell: ({ row }) => (
        <div className="font-medium">{row.original.trip_id}</div>
      ),
    },
    {
      accessorKey: "pickup_facility",
      header: "Route",
      cell: ({ row }) => {
        const load = row.original;
        const pickup = load.pickup_facility || load.pickup_address || "Unknown";
        const dropoff = load.dropoff_facility || load.dropoff_address || "Unknown";
        return (
          <div className="flex items-center space-x-2 max-w-xs">
            <div className="flex-1 truncate">
              <div className="text-sm font-medium truncate">{pickup}</div>
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                <ArrowRight className="h-3 w-3" />
                <span className="truncate">{dropoff}</span>
              </div>
            </div>
          </div>
        );
      }
    },
    {
      accessorKey: "start_time",
      header: "Schedule",
      cell: ({ row }) => (
        <div className="text-sm">
          <div>{formatDate(row.original.start_time, true)}</div>
          <div className="text-xs text-muted-foreground">
            to {formatDate(row.original.end_time, true)}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "rate",
      header: "Rate",
      cell: ({ row }) => (
        <div className="text-right">
          <div className="font-medium">{formatCurrency(row.original.rate)}</div>
          <div className="text-xs text-muted-foreground">
            {formatCurrency(row.original.rate_per_mile)}/mi
          </div>
        </div>
      ),
    },
    {
      accessorKey: "distance",
      header: "Distance",
      cell: ({ row }) => (
        <div className="text-center">
          <span className="font-medium">{formatNumber(row.original.distance || 0)}</span>
          <span className="text-xs text-muted-foreground ml-1">mi</span>
        </div>
      ),
    },
    {
      accessorKey: "assigned_driver",
      header: "Driver",
      cell: ({ row }) => {
        const driver = row.original.assigned_driver;
        return driver ? (
          <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100">
            {driver}
          </Badge>
        ) : (
          <Badge variant="secondary">Unassigned</Badge>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const load = row.original;
        return (
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                openDialog('details', load);
              }}
              title="View Details"
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                openDialog('edit', load);
              }}
              title="Edit Load"
            >
              <Edit className="h-4 w-4" />
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => e.stopPropagation()}
                  className="text-red-600 hover:text-red-700"
                  title="Delete Load"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Load</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete load #{load.trip_id}? This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => handleDeleteLoad(load.id)}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        );
      },
    },
  ];

  // Loading state
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="text-muted-foreground">Loading loads...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Alert className="max-w-md">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-2">
                <p className="font-medium">Error Loading Loads</p>
                <p className="text-sm">Please check your connection and try again.</p>
                <Button onClick={() => refetch()} size="sm" className="mt-2">
                  Try Again
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div>
            <h1 className="text-3xl font-bold">Loads Management</h1>
            <p className="text-muted-foreground">Create, view, edit, and manage all your loads</p>
          </div>
          <Button size="lg" onClick={() => openDialog('create')}>
            <Plus className="mr-2 h-4 w-4" />
            Create New Load
          </Button>
        </div>

        {/* Stats Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <TruckIcon className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.total}</p>
                  <p className="text-sm text-muted-foreground">Total Loads</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Truck className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.assigned}</p>
                  <p className="text-sm text-muted-foreground">Assigned ({((stats.assigned / stats.total) * 100).toFixed(0)}%)</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{formatCurrency(stats.totalRevenue)}</p>
                  <p className="text-sm text-muted-foreground">Total Revenue</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <RouteIcon className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{formatNumber(stats.totalDistance)}</p>
                  <p className="text-sm text-muted-foreground">Total Miles</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and View Controls */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search loads by ID, location, or driver..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'cards' ? 'default' : 'outline'}
              onClick={() => setViewMode('cards')}
              size="sm"
            >
              Cards
            </Button>
            <Button
              variant={viewMode === 'table' ? 'default' : 'outline'}
              onClick={() => setViewMode('table')}
              size="sm"
            >
              Table
            </Button>
          </div>
        </div>

        {/* Main Content */}
        {filteredLoads.length === 0 && searchQuery ? (
          // No search results
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No loads found</h3>
              <p className="text-muted-foreground text-center mb-4">
                No loads match your search criteria "{searchQuery}". Try adjusting your search terms.
              </p>
              <Button onClick={() => setSearchQuery("")} variant="outline">
                Clear Search
              </Button>
            </CardContent>
          </Card>
        ) : filteredLoads.length === 0 ? (
          // Empty state
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <TruckIcon className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No loads yet</h3>
              <p className="text-muted-foreground text-center mb-6">
                Get started by creating your first load to begin managing your transportation operations.
              </p>
              <Button onClick={() => openDialog('create')}>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Load
              </Button>
            </CardContent>
          </Card>
        ) : viewMode === 'cards' ? (
          // Cards view
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredLoads.map((load) => {
              const isExpanded = expandedCards.has(load.id);
              return (
                <Card key={load.id} className="hover:shadow-lg transition-all duration-200">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">#{load.trip_id}</CardTitle>
                      <div className="flex items-center space-x-2">
                        {load.assigned_driver ? (
                          <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
                            Assigned
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Unassigned</Badge>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => toggleCardExpansion(load.id, e)}
                          className="p-1 h-auto"
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Route Information */}
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2 text-sm">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="font-medium">From:</span>
                        <span className="text-muted-foreground truncate">
                          {load.pickup_facility || load.pickup_address || "Not specified"}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm">
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        <span className="font-medium">To:</span>
                        <span className="text-muted-foreground truncate">
                          {load.dropoff_facility || load.dropoff_address || "Not specified"}
                        </span>
                      </div>
                    </div>

                    {/* Financial Information */}
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-1">
                          <DollarSign className="h-4 w-4 text-green-600" />
                          <span className="font-semibold">{formatCurrency(load.rate)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <RouteIcon className="h-4 w-4 text-blue-600" />
                          <span>{formatNumber(load.distance || 0)} mi</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">Rate/Mile</p>
                        <p className="font-medium">{formatCurrency(load.rate_per_mile)}</p>
                      </div>
                    </div>

                    {/* Schedule */}
                    <div className="flex items-center justify-between text-sm">
                      <div>
                        <p className="text-muted-foreground">Start</p>
                        <p className="font-medium">{formatDate(load.start_time, true)}</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-right">
                        <p className="text-muted-foreground">End</p>
                        <p className="font-medium">{formatDate(load.end_time, true)}</p>
                      </div>
                    </div>

                    {/* Driver Assignment */}
                    {load.assigned_driver && (
                      <div className="flex items-center space-x-2 text-sm bg-green-50 p-2 rounded">
                        <Truck className="h-4 w-4 text-green-600" />
                        <span className="font-medium">Driver:</span>
                        <span className="text-green-700">{load.assigned_driver}</span>
                      </div>
                    )}

                    {/* Expanded Content - Legs */}
                    {isExpanded && load.legs && load.legs.length > 0 && (
                      <>
                        <Separator />
                        <div className="space-y-3">
                          <h4 className="font-semibold text-sm flex items-center space-x-2">
                            <RouteIcon className="h-4 w-4" />
                            <span>Load Legs ({load.legs.length})</span>
                          </h4>
                          <div className="space-y-2 max-h-32 overflow-y-auto">
                            {load.legs.map((leg, index) => (
                              <div key={leg.id} className="bg-gray-50 p-3 rounded text-xs">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium">Leg {index + 1}</span>
                                  {leg.leg_id && (
                                    <Badge variant="outline" className="text-xs">
                                      {leg.leg_id}
                                    </Badge>
                                  )}
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                  <div>
                                    <span className="text-muted-foreground">From:</span>
                                    <p className="font-medium truncate">
                                      {leg.pickup_address || leg.pickup_facility_id || "N/A"}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground">To:</span>
                                    <p className="font-medium truncate">
                                      {leg.dropoff_address || leg.dropoff_facility_id || "N/A"}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground">Distance:</span>
                                    <p className="font-medium">{leg.distance || 0} mi</p>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground">FSC:</span>
                                    <p className="font-medium text-green-600">
                                      {formatCurrency(leg.fuel_sur_charge)}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {/* Card Actions */}
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openDialog('details', load)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openDialog('edit', load)}
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          Edit
                        </Button>
                      </div>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:text-red-700 border-red-200 hover:border-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Load</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete load #{load.trip_id}? This action cannot be undone and will remove all associated leg data.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteLoad(load.id)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              Delete Load
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          // Table view
          <Card>
            <CardContent className="p-0">
              <DataTable
                columns={columns}
                data={filteredLoads}
                isLoading={false}
                onRowClick={(load) => openDialog('details', load)}
              />
            </CardContent>
          </Card>
        )}

        {/* Dialogs */}
        
        {/* Create Load Dialog */}
        <Dialog open={dialog.type === 'create'} onOpenChange={closeDialog}>
          <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-hidden">
            <DialogHeader>
              <DialogTitle>Create New Load</DialogTitle>
            </DialogHeader>
            <div className="max-h-[70vh] overflow-y-auto">
              <LoadForm
                onSubmit={handleCreateLoad}
                isSubmitting={createLoad.isPending || parseLoad.isPending}
                parseLoad={parseLoad.mutateAsync}
                dispatchers={dispatchers}
              />
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit Load Dialog */}
        <Dialog open={dialog.type === 'edit'} onOpenChange={closeDialog}>
          <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-hidden">
            <DialogHeader>
              <DialogTitle>Edit Load #{dialog.load?.trip_id}</DialogTitle>
            </DialogHeader>
            {dialog.load && (
              <LoadEditForm
                load={dialog.load}
                onSubmit={handleUpdateLoad}
                isSubmitting={updateLoad.isPending}
                dispatchers={dispatchers}
              />
            )}
          </DialogContent>
        </Dialog>

        {/* Load Details Dialog */}
        <Dialog open={dialog.type === 'details'} onOpenChange={closeDialog}>
          <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <TruckIcon className="h-5 w-5" />
                <span>Load Details #{dialog.load?.trip_id}</span>
              </DialogTitle>
            </DialogHeader>
            {dialog.load && (
              <div className="space-y-6">
                {/* Basic Information Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">Route Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div>
                          <p className="text-sm text-muted-foreground">Pickup</p>
                          <p className="font-medium">
                            {dialog.load.pickup_facility || dialog.load.pickup_address || "Not specified"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        <div>
                          <p className="text-sm text-muted-foreground">Dropoff</p>
                          <p className="font-medium">
                            {dialog.load.dropoff_facility || dialog.load.dropoff_address || "Not specified"}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">Financial Details</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Rate:</span>
                        <span className="font-semibold">{formatCurrency(dialog.load.rate)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Rate per Mile:</span>
                        <span className="font-medium">{formatCurrency(dialog.load.rate_per_mile)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Distance:</span>
                        <span className="font-medium">{formatNumber(dialog.load.distance || 0)} miles</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Schedule Information */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center space-x-2">
                      <Calendar className="h-4 w-4" />
                      <span>Schedule</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Start Time</p>
                        <p className="font-medium">{formatDate(dialog.load.start_time, true)}</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">End Time</p>
                        <p className="font-medium">{formatDate(dialog.load.end_time, true)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Driver Assignment */}
                {dialog.load.assigned_driver && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center space-x-2">
                        <Truck className="h-4 w-4" />
                        <span>Driver Assignment</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center space-x-3 p-3 bg-green-50 rounded">
                        <div className="p-2 bg-green-100 rounded-full">
                          <Truck className="h-4 w-4 text-green-600" />
                        </div>
                        <div>
                          <p className="font-semibold">{dialog.load.assigned_driver}</p>
                          <p className="text-sm text-muted-foreground">Assigned Driver</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Load Legs Table */}
                {dialog.load.legs && dialog.load.legs.length > 0 && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center space-x-2">
                        <RouteIcon className="h-4 w-4" />
                        <span>Load Legs ({dialog.load.legs.length})</span>
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
                              <TableHead>Distance</TableHead>
                              <TableHead>FSC</TableHead>
                              <TableHead>Times</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {dialog.load.legs.map((leg, index) => (
                              <TableRow key={leg.id || index}>
                                <TableCell className="font-medium">
                                  {leg.leg_id || `Leg ${index + 1}`}
                                </TableCell>
                                <TableCell>
                                  {leg.pickup_address || leg.pickup_facility_id || "N/A"}
                                </TableCell>
                                <TableCell>
                                  {leg.dropoff_address || leg.dropoff_facility_id || "N/A"}
                                </TableCell>
                                <TableCell>
                                  {leg.distance ? `${formatNumber(leg.distance)} mi` : "N/A"}
                                </TableCell>
                                <TableCell>
                                  {formatCurrency(leg.fuel_sur_charge || 0)}
                                </TableCell>
                                <TableCell>
                                  <div className="text-xs">
                                    {leg.pickup_time && (
                                      <div>
                                        <span className="text-muted-foreground">Pickup:</span>
                                        <br />
                                        {formatDate(leg.pickup_time, true)}
                                      </div>
                                    )}
                                    {leg.dropoff_time && (
                                      <div className="mt-1">
                                        <span className="text-muted-foreground">Dropoff:</span>
                                        <br />
                                        {formatDate(leg.dropoff_time, true)}
                                      </div>
                                    )}
                                    {!leg.pickup_time && !leg.dropoff_time && "N/A"}
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Dialog Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button variant="outline" onClick={closeDialog}>
                    Close
                  </Button>
                  <Button onClick={() => openDialog('edit', dialog.load)}>
                    <Edit className="h-4 w-4 mr-2" />
                    Edit Load
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

// Helper function to format load data for text editing
function formatLoadForEditing(load: Load): string {
  const formatDateTime = (dateStr: string | Date | null | undefined) => {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toISOString();
    } catch {
      return String(dateStr);
    }
  };

  let text = `**Trip Information**
**trip id:** ${load.trip_id || 'N/A'}
**pick up facility id:** ${load.pickup_facility || 'N/A'}
**drop off facility id:** ${load.dropoff_facility || 'N/A'}
**pick up address:** ${load.pickup_address || 'N/A'}
**drop off address:** ${load.dropoff_address || 'N/A'}
**pick up time:** ${formatDateTime(load.start_time)}
**drop off time:** ${formatDateTime(load.end_time)}
**rate:** ${load.rate || 0}
**rate per mile:** ${load.rate_per_mile || 0}
**distance:** ${load.distance || 0}
**assigned driver:** ${load.assigned_driver || 'N/A'}
**is team load:** false

**Load Legs**`;

  if (load.legs && load.legs.length > 0) {
    load.legs.forEach((leg, index) => {
      text += `
**Leg ${index + 1}**
**ID:** ${leg.leg_id || `LEG-${index + 1}`}
**Pickup Facility ID:** ${leg.pickup_facility_id || 'N/A'}
**Dropoff Facility ID:** ${leg.dropoff_facility_id || 'N/A'}
**Pickup Address:** ${leg.pickup_address || 'N/A'}
**Dropoff Address:** ${leg.dropoff_address || 'N/A'}
**Distance:** ${leg.distance || 0} miles
**Fuel Surcharge:** ${leg.fuel_sur_charge || 0}
**Pickup Time:** ${formatDateTime(leg.pickup_time)}
**Dropoff Time:** ${formatDateTime(leg.dropoff_time)}
**Assigned Driver:** ${leg.assigned_driver || 'N/A'}`;
    });
  } else {
    text += '\n**No legs found**';
  }

  return text;
}