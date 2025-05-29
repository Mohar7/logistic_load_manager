import {createFileRoute, useNavigate} from "@tanstack/react-router";
import {useState} from "react";
import {DashboardLayout} from "@/components/layout/dashboard-layout";
import {useCompanies, useCreateCompany, useDeleteCompany} from "./-api/company-api";
import {Button} from "@/components/ui/button";
import {Edit, Plus, Trash2} from "lucide-react";
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,} from "@/components/ui/dialog";
import type {Company, CompanyCreate} from "@/types/models";
import {CompanyForm} from "./-components/company-form";
import {DataTable} from "@/components/ui/data-table";
import type {ColumnDef} from "@tanstack/react-table";
import {toast} from "sonner";

export const Route = createFileRoute('/companies')({
	component: CompaniesPage,
});

export function CompaniesPage() {
	const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
	const { data: companies = [], isLoading } = useCompanies();
	const createCompany = useCreateCompany();
	const deleteCompany = useDeleteCompany();
	const navigate = useNavigate();
	
	const columns: ColumnDef<Company>[] = [
		{
			accessorKey: "id",
			header: "ID",
		},
		{
			accessorKey: "name",
			header: "Company Name",
		},
		{
			accessorKey: "usdot",
			header: "USDOT",
		},
		{
			accessorKey: "carrier_identifier",
			header: "Carrier ID",
		},
		{
			accessorKey: "mc",
			header: "MC Number",
		},
		{
			accessorKey: "drivers_count",
			header: "Drivers",
		},
		{
			id: "actions",
			cell: ({ row }) => {
				const company = row.original;
				return (
					<div className="flex space-x-2">
						<Button
							variant="ghost"
							size="icon"
							onClick={() => navigate({ to: `/companies/${company.id}` })}
						>
							<Edit className="h-4 w-4" />
						</Button>
						<Button
							variant="ghost"
							size="icon"
							onClick={() => handleDelete(company.id)}
						>
							<Trash2 className="h-4 w-4" />
						</Button>
					</div>
				);
			},
		},
	];
	
	const handleCreateCompany = async (data: CompanyCreate) => {
		try {
			await createCompany.mutateAsync(data);
			toast.success("Company created successfully");
			setIsCreateDialogOpen(false);
		} catch (error) {
			toast.error("Failed to create company");
			console.error(error);
		}
	};
	
	const handleDelete = async (id: number) => {
		if (window.confirm("Are you sure you want to delete this company?")) {
			try {
				await deleteCompany.mutateAsync(id);
				toast.success("Company deleted successfully");
			} catch (error) {
				toast.error("Failed to delete company");
				console.error(error);
			}
		}
	};
	
	return (
		<DashboardLayout>
			<div className="space-y-6">
				<div className="flex justify-between items-center">
					<div>
						<h1 className="text-3xl font-bold">Companies</h1>
						<p className="text-muted-foreground">Manage your companies and carriers</p>
					</div>
					<Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
						<DialogTrigger asChild>
							<Button>
								<Plus className="mr-2 h-4 w-4" />
								Add Company
							</Button>
						</DialogTrigger>
						<DialogContent className="sm:max-w-[600px]">
							<DialogHeader>
								<DialogTitle>Add New Company</DialogTitle>
							</DialogHeader>
							<CompanyForm
								onSubmit={handleCreateCompany}
								isSubmitting={createCompany.isPending}
							/>
						</DialogContent>
					</Dialog>
				</div>
				
				<DataTable
					columns={columns}
					data={companies}
					isLoading={isLoading}
					onRowClick={(company) => navigate({ to: `/companies/${company.id}` })}
					searchColumn="name"
					searchPlaceholder="Search companies..."
				/>
			</div>
		</DashboardLayout>
	);
}