import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";
import API_ENDPOINTS from "@/lib/api/endpoints";
import type {Driver, DriverCreate} from "@/types/models";

// Query key factory
const driverKeys = {
	all: ['drivers'] as const,
	lists: () => [...driverKeys.all, 'list'] as const,
	list: (filters: Record<string, any>) => [...driverKeys.lists(), { filters }] as const,
	details: () => [...driverKeys.all, 'detail'] as const,
	detail: (id: number) => [...driverKeys.details(), id] as const,
	byCompany: (companyId: number) => [...driverKeys.lists(), { companyId }] as const,
};

// Fetch all drivers
export const useDrivers = (
	page = 0,
	limit = 100,
	companyId?: number
) => {
	return useQuery({
		queryKey: companyId ? driverKeys.byCompany(companyId) : driverKeys.list({ page, limit }),
		queryFn: () =>
			apiRequest<Driver[]>({
				url: API_ENDPOINTS.drivers.getAll,
				params: {
					skip: page * limit,
					limit,
					...(companyId ? { company_id: companyId } : {})
				},
			}),
	});
};

// Fetch a single driver by ID
export const useDriver = (id: number) => {
	return useQuery({
		queryKey: driverKeys.detail(id),
		queryFn: () =>
			apiRequest<Driver>({
				url: API_ENDPOINTS.drivers.getById(id),
			}),
		enabled: !!id,
	});
};

// Create a new driver
export const useCreateDriver = () => {
	const queryClient = useQueryClient();
	
	return useMutation({
		mutationFn: (data: DriverCreate) =>
			apiRequest<Driver>({
				url: API_ENDPOINTS.drivers.create,
				method: "POST",
				data,
			}),
		onSuccess: (data) => {
			queryClient.invalidateQueries({ queryKey: driverKeys.lists() });
			queryClient.invalidateQueries({
				queryKey: driverKeys.byCompany(data.company_id)
			});
		},
	});
};

// Update a driver
export const useUpdateDriver = (id: number) => {
	const queryClient = useQueryClient();
	
	return useMutation({
		mutationFn: (data: DriverCreate) =>
			apiRequest<Driver>({
				url: API_ENDPOINTS.drivers.update(id),
				method: "PUT",
				data,
			}),
		onSuccess: (data) => {
			queryClient.invalidateQueries({ queryKey: driverKeys.detail(id) });
			queryClient.invalidateQueries({ queryKey: driverKeys.lists() });
			queryClient.invalidateQueries({
				queryKey: driverKeys.byCompany(data.company_id)
			});
		},
	});
};

// Delete a driver
export const useDeleteDriver = () => {
	const queryClient = useQueryClient();
	
	return useMutation({
		mutationFn: (id: number) =>
			apiRequest<{ message: string }>({
				url: API_ENDPOINTS.drivers.delete(id),
				method: "DELETE",
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: driverKeys.lists() });
		},
	});
};