import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {useState} from "react";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useCreateDriver, useDeleteDriver, useDrivers} from "./-api/driver-api";
import {useCompanies} from "@/app/companies/-api/company-api";
import {Button} from "@/components/ui/button";
import {Edit, Plus, Trash2} from "lucide-react";
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,} from "@/components/ui/dialog";
import type {Driver, DriverCreate} from "@/types/models";
import {DriverForm} from "./-components/driver-form";
import {DataTable} from "@/components/ui/data-table";
import type {ColumnDef} from "@tanstack/react-table";
import {toast} from "sonner";

export const Route = createFileRoute('/drivers')({
	component: DriversPage,
});

export function DriversPage() {
	const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
	const { data: drivers = [], isLoading } = useDrivers();
	const { data: companies = [] } = useCompanies(0, 100);
	const createDriver = useCreateDriver();
	const deleteDriver = useDeleteDriver();
	const navigate = useNavigate();
	
	const columns: ColumnDef<Driver>[] = [
		{
			accessorKey: "id",
			header: "ID",
		},
		{
			accessorKey: "name",
			header: "Driver Name",
		},
		{
			accessorKey: "company_id",
			header: "Company ID",
			cell: ({ row }) => {
				const companyId = row.original.company_id;
				const company = companies.find(c => c.id === companyId);
				return company ? company.name : companyId;
			}
		},
		{
			accessorKey: "chat_id",
			header: "Chat ID",
		},
		{
			id: "actions",
			cell: ({ row }) => {
				const driver = row.original;
				return (
					<div className="flex space-x-2">
						<Button
							variant="ghost"
							size="icon"
							onClick={() => navigate({ to: `/drivers/${driver.id}` })}
						>
							<Edit className="h-4 w-4" />
						</Button>
						<Button
							variant="ghost"
							size="icon"
							onClick={() => handleDelete(driver.id)}
						>
							<Trash2 className="h-4 w-4" />
						</Button>
					</div>
				);
			},
		},
	];
	
	const handleCreateDriver = async (data: DriverCreate) => {
		try {
			await createDriver.mutateAsync(data);
			toast.success("Driver created successfully");
			setIsCreateDialogOpen(false);
		} catch (error) {
			toast.error("Failed to create driver");
			console.error(error);
		}
	};
	
	const handleDelete = async (id: number) => {
		if (window.confirm("Are you sure you want to delete this driver?")) {
			try {
				await deleteDriver.mutateAsync(id);
				toast.success("Driver deleted successfully");
			} catch (error) {
				toast.error("Failed to delete driver");
				console.error(error);
			}
		}
	};
	
	return (
		<DashboardLayout>
			<div className="space-y-6">
				<div className="flex justify-between items-center">
					<div>
						<h1 className="text-3xl font-bold">Drivers</h1>
						<p className="text-muted-foreground">Manage your drivers</p>
					</div>
					<Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
						<DialogTrigger asChild>
							<Button>
								<Plus className="mr-2 h-4 w-4" />
								Add Driver
							</Button>
						</DialogTrigger>
						<DialogContent className="sm:max-w-[600px]">
							<DialogHeader>
								<DialogTitle>Add New Driver</DialogTitle>
							</DialogHeader>
							<DriverForm
								onSubmit={handleCreateDriver}
								isSubmitting={createDriver.isPending}
								companies={companies}
							/>
						</DialogContent>
					</Dialog>
				</div>
				
				<DataTable
					columns={columns}
					data={drivers}
					isLoading={isLoading}
					onRowClick={(driver) => navigate({ to: `/drivers/${driver.id}` })}
					searchColumn="name"
					searchPlaceholder="Search drivers..."
				/>
			</div>
		</DashboardLayout>
	);
}