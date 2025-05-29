import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {useState} from "react";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useCreateDispatcher, useDeleteDispatcher, useDispatchers} from "./-api/dispatcher-api";
import {Button} from "@/components/ui/button";
import {Edit, Plus, Trash2} from "lucide-react";
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,} from "@/components/ui/dialog";
import type {Dispatcher, DispatcherCreate} from "@/types/models";
import {DispatcherForm} from "./-components/dispatcher-form";
import {DataTable} from "@/components/ui/data-table";
import type {ColumnDef} from "@tanstack/react-table";
import {toast} from "sonner";

export const Route = createFileRoute('/dispatchers')({
  component: DispatchersPage,
});

export function DispatchersPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const { data: dispatchers = [], isLoading } = useDispatchers();
  const createDispatcher = useCreateDispatcher();
  const deleteDispatcher = useDeleteDispatcher();
  const navigate = useNavigate();

  const columns: ColumnDef<Dispatcher>[] = [
    {
      accessorKey: "id",
      header: "ID",
    },
    {
      accessorKey: "name",
      header: "Name",
    },
    {
      accessorKey: "telegram_id",
      header: "Telegram ID",
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const dispatcher = row.original;
        return (
          <div className="flex space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate({ to: `/dispatchers/${dispatcher.id}` })}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(dispatcher.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        );
      },
    },
  ];

  const handleCreateDispatcher = async (data: DispatcherCreate) => {
    try {
      await createDispatcher.mutateAsync(data);
      toast.success("Dispatcher created successfully");
      setIsCreateDialogOpen(false);
    } catch (error) {
      toast.error("Failed to create dispatcher");
      console.error(error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm("Are you sure you want to delete this dispatcher?")) {
      try {
        await deleteDispatcher.mutateAsync(id);
        toast.success("Dispatcher deleted successfully");
      } catch (error) {
        toast.error("Failed to delete dispatcher");
        console.error(error);
      }
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Dispatchers</h1>
            <p className="text-muted-foreground">Manage dispatchers and telegram connections</p>
          </div>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Dispatcher
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Add New Dispatcher</DialogTitle>
              </DialogHeader>
              <DispatcherForm
                onSubmit={handleCreateDispatcher}
                isSubmitting={createDispatcher.isPending}
              />
            </DialogContent>
          </Dialog>
        </div>

        <DataTable
          columns={columns}
          data={dispatchers}
          isLoading={isLoading}
          onRowClick={(dispatcher) => navigate({ to: `/dispatchers/${dispatcher.id}` })}
          searchColumn="name"
          searchPlaceholder="Search dispatchers..."
        />
      </div>
    </DashboardLayout>
  );
}