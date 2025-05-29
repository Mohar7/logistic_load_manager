import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useDispatcher, useUpdateDispatcher} from "../-api/dispatcher-api";
import {DispatcherForm} from "../-components/dispatcher-form";
import {Button} from "@/components/ui/button";
import {ArrowLeft} from "lucide-react";
import type {DispatcherCreate} from "@/types/models";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {toast} from "sonner";

export const Route = createFileRoute('/dispatchers/$dispatcherId')({
  component: DispatcherDetailPage,
});

export function DispatcherDetailPage() {
  const { dispatcherId } = Route.useParams();
  const id = parseInt(dispatcherId);
  const { data: dispatcher, isLoading } = useDispatcher(id);
  const updateDispatcher = useUpdateDispatcher(id);
  const navigate = useNavigate();

  const handleUpdateDispatcher = async (data: DispatcherCreate) => {
    try {
      await updateDispatcher.mutateAsync({
        name: data.name,
        telegram_id: data.telegram_id,
      });
      toast.success("Dispatcher updated successfully");
    } catch (error) {
      toast.error("Failed to update dispatcher");
      console.error(error);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <p>Loading dispatcher details...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (!dispatcher) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <p>Dispatcher not found</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate({ to: "/dispatchers" })}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-3xl font-bold">{dispatcher.name}</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Dispatcher Details</CardTitle>
            </CardHeader>
            <CardContent>
              <DispatcherForm
                onSubmit={handleUpdateDispatcher}
                isSubmitting={updateDispatcher.isPending}
                defaultValues={{
                  name: dispatcher.name,
                  telegram_id: dispatcher.telegram_id,
                }}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Dispatcher Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-medium">Dispatcher ID</h3>
                <p>{dispatcher.id}</p>
              </div>
              <div>
                <h3 className="font-medium">Telegram ID</h3>
                <p>{dispatcher.telegram_id}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}