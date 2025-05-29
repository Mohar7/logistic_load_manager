import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useDriver, useUpdateDriver} from "../-api/driver-api";
import {useCompanies} from "@/app/companies/-api/company-api";
import {DriverForm} from "../-components/driver-form";
import {Button} from "@/components/ui/button";
import {ArrowLeft} from "lucide-react";
import type {DriverCreate} from "@/types/models";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {toast} from "sonner";

export const Route = createFileRoute('/drivers/$driverId')({
	component: DriverDetailPage,
});

export function DriverDetailPage() {
	const { driverId } = Route.useParams();
	const id = parseInt(driverId);
	const { data: driver, isLoading } = useDriver(id);
	const { data: companies = [] } = useCompanies(0, 100);
	const updateDriver = useUpdateDriver(id);
	const navigate = useNavigate();
	
	const handleUpdateDriver = async (data: DriverCreate) => {
		try {
			await updateDriver.mutateAsync(data);
			toast.success("Driver updated successfully");
		} catch (error) {
			toast.error("Failed to update driver");
			console.error(error);
		}
	};
	
	if (isLoading) {
		return (
			<DashboardLayout>
				<div className="flex items-center justify-center h-full">
					<p>Loading driver details...</p>
				</div>
			</DashboardLayout>
		);
	}
	
	if (!driver) {
		return (
			<DashboardLayout>
				<div className="flex items-center justify-center h-full">
					<p>Driver not found</p>
				</div>
			</DashboardLayout>
		);
	}
	
	const company = companies.find(c => c.id === driver.company_id);
	
	return (
		<DashboardLayout>
			<div className="space-y-6">
				<div className="flex items-center space-x-2">
					<Button
						variant="outline"
						size="icon"
						onClick={() => navigate({ to: "/drivers" })}
					>
						<ArrowLeft className="h-4 w-4" />
					</Button>
					<h1 className="text-3xl font-bold">{driver.name}</h1>
				</div>
				
				<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
					<Card>
						<CardHeader>
							<CardTitle>Driver Details</CardTitle>
						</CardHeader>
						<CardContent>
							<DriverForm
								onSubmit={handleUpdateDriver}
								isSubmitting={updateDriver.isPending}
								defaultValues={{
									name: driver.name,
									company_id: driver.company_id,
									chat_id: driver.chat_id,
								}}
								companies={companies}
							/>
						</CardContent>
					</Card>
					
					<Card>
						<CardHeader>
							<CardTitle>Driver Info</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							<div>
								<h3 className="font-medium">Driver ID</h3>
								<p>{driver.id}</p>
							</div>
							<div>
								<h3 className="font-medium">Company</h3>
								<p>{company?.name || driver.company_id}</p>
							</div>
							<div>
								<h3 className="font-medium">Chat ID</h3>
								<p>{driver.chat_id || "Not assigned"}</p>
							</div>
						</CardContent>
					</Card>
				</div>
			</div>
		</DashboardLayout>
	);
}