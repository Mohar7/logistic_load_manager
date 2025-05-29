import {useNavigate} from "@tanstack/react-router";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Button} from "@/components/ui/button";
import {formatCurrency, formatDate} from "@/lib/utils";
import type {Load} from "@/types/models";
import {Eye} from "lucide-react";

interface RecentLoadsProps {
  loads: Load[];
  isLoading: boolean;
}

export function RecentLoads({ loads, isLoading }: RecentLoadsProps) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Loads</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center py-4">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  if (!loads.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Loads</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-4">No loads available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Loads</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {loads.slice(0, 5).map((load) => (
            <div key={load.id} className="flex justify-between items-start border-b pb-3 last:border-b-0 last:pb-0">
              <div>
                <h3 className="font-medium">{load.trip_id}</h3>
                <p className="text-sm text-muted-foreground">
                  {formatDate(load.start_time)}
                </p>
                <p className="text-sm">
                  {load.pickup_facility || load.pickup_address || "Unknown"} →{" "}
                  {load.dropoff_facility || load.dropoff_address || "Unknown"}
                </p>
              </div>
              <div className="text-right">
                <p className="font-medium">{formatCurrency(load.rate)}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate({
                    to: `/loads/${load.id}`,
                    search: {},
                    params: {
                      loadId: String(load.id)
                    }
                  })}
                >
                  <Eye className="h-4 w-4 mr-1" /> View
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}