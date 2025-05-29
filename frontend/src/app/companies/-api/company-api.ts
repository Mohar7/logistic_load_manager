import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";
import API_ENDPOINTS from "@/lib/api/endpoints";
import type {Company, CompanyCreate} from "@/types/models";

// Query key factory
const companyKeys = {
	all: ['companies'] as const,
	lists: () => [...companyKeys.all, 'list'] as const,
	list: (filters: Record<string, any>) => [...companyKeys.lists(), { filters }] as const,
	details: () => [...companyKeys.all, 'detail'] as const,
	detail: (id: number) => [...companyKeys.details(), id] as const,
};

// Fetch all companies
export const useCompanies = (
	page = 0,
	limit = 20
) => {
	return useQuery({
		queryKey: companyKeys.list({ page, limit }),
		queryFn: () =>
			apiRequest<Company[]>({
				url: API_ENDPOINTS.companies.getAll,
				params: { skip: page * limit, limit },
			}),
	});
};

// Fetch a single company by ID
export const useCompany = (id: number) => {
	return useQuery({
		queryKey: companyKeys.detail(id),
		queryFn: () =>
			apiRequest<Company>({
				url: API_ENDPOINTS.companies.getById(id),
			}),
		enabled: !!id,
	});
};

// Create a new company
export const useCreateCompany = () => {
	const queryClient = useQueryClient();
	
	return useMutation({
		mutationFn: (data: CompanyCreate) =>
			apiRequest<Company>({
				url: API_ENDPOINTS.companies.create,
				method: "POST",
				data,
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
		},
	});
};

// Update a company
export const useUpdateCompany = (id: number) => {
	const queryClient = useQueryClient();
	
	return useMutation({
		mutationFn: (data: CompanyCreate) =>
			apiRequest<Company>({
				url: API_ENDPOINTS.companies.update(id),
				method: "PUT",
				data,
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: companyKeys.detail(id) });
			queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
		},
	});
};

// Delete a company
export const useDeleteCompany = () => {
	const queryClient = useQueryClient();
	
	return useMutation({
		mutationFn: (id: number) =>
			apiRequest<{ message: string }>({
				url: API_ENDPOINTS.companies.delete(id),
				method: "DELETE",
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
		},
	});
};