import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {ArrowDown, ArrowUp} from "lucide-react";

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  suffix?: string;
}

export function StatsCard({ title, value, change, icon, suffix }: StatsCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}{suffix}</div>
        {typeof change !== 'undefined' && (
          <p className="text-xs text-muted-foreground flex items-center">
            {change > 0 ? (
              <>
                <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
                <span className="text-green-500">{change}% increase</span>
              </>
            ) : (
              <>
                <ArrowDown className="mr-1 h-4 w-4 text-red-500" />
                <span className="text-red-500">{Math.abs(change)}% decrease</span>
              </>
            )}
            {" "}from last month
          </p>
        )}
      </CardContent>
    </Card>
  );
}