import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useCompany, useUpdateCompany} from "../-api/company-api";
import {useDrivers} from "@/app/drivers/-api/driver-api";
import {CompanyForm} from "../-components/company-form";
import {Button} from "@/components/ui/button";
import {ArrowLeft} from "lucide-react";
import {DataTable} from "@/components/ui/data-table";
import type {CompanyCreate, Driver} from "@/types/models";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {toast} from "sonner";
import type {ColumnDef} from "@tanstack/react-table";

export const Route = createFileRoute('/companies/$companyId')({
	component: CompanyDetailPage,
});

export function CompanyDetailPage() {
	const { companyId } = Route.useParams();
	const id = parseInt(companyId);
	const { data: company, isLoading } = useCompany(id);
	const { data: drivers = [], isLoading: isLoadingDrivers } = useDrivers(0, 100, id);
	const updateCompany = useUpdateCompany(id);
	const navigate = useNavigate();
	
	const driverColumns: ColumnDef<Driver>[] = [
		{
			accessorKey: "id",
			header: "ID",
		},
		{
			accessorKey: "name",
			header: "Driver Name",
		},
		{
			accessorKey: "chat_id",
			header: "Chat ID",
		},
	];
	
	const handleUpdateCompany = async (data: CompanyCreate) => {
		try {
			await updateCompany.mutateAsync(data);
			toast.success("Company updated successfully");
		} catch (error) {
			toast.error("Failed to update company");
			console.error(error);
		}
	};
	
	if (isLoading) {
		return (
			<DashboardLayout>
				<div className="flex items-center justify-center h-full">
					<p>Loading company details...</p>
				</div>
			</DashboardLayout>
		);
	}
	
	if (!company) {
		return (
			<DashboardLayout>
				<div className="flex items-center justify-center h-full">
					<p>Company not found</p>
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
						onClick={() => navigate({ to: "/companies" })}
					>
						<ArrowLeft className="h-4 w-4" />
					</Button>
					<h1 className="text-3xl font-bold">{company.name}</h1>
				</div>
				
				<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
					<Card>
						<CardHeader>
							<CardTitle>Company Details</CardTitle>
						</CardHeader>
						<CardContent>
							<CompanyForm
								onSubmit={handleUpdateCompany}
								isSubmitting={updateCompany.isPending}
								defaultValues={{
									name: company.name,
									usdot: company.usdot,
									carrier_identifier: company.carrier_identifier,
									mc: company.mc,
								}}
							/>
						</CardContent>
					</Card>
					
					<Card>
						<CardHeader>
							<CardTitle>Company Info</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							<div>
								<h3 className="font-medium">USDOT Number</h3>
								<p>{company.usdot}</p>
							</div>
							<div>
								<h3 className="font-medium">Carrier Identifier</h3>
								<p>{company.carrier_identifier}</p>
							</div>
							<div>
								<h3 className="font-medium">MC Number</h3>
								<p>{company.mc}</p>
							</div>
							<div>
								<h3 className="font-medium">Total Drivers</h3>
								<p>{company.drivers_count}</p>
							</div>
						</CardContent>
					</Card>
				</div>
				
				<Card>
					<CardHeader>
						<CardTitle>Drivers</CardTitle>
					</CardHeader>
					<CardContent>
						<DataTable
							columns={driverColumns}
							data={drivers}
							isLoading={isLoadingDrivers}
							onRowClick={(driver) => navigate({ to: `/drivers/${driver.id}` })}
							searchColumn="name"
							searchPlaceholder="Search drivers..."
						/>
					</CardContent>
				</Card>
			</div>
		</DashboardLayout>
	);
}