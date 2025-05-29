import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";
import API_ENDPOINTS from "@/lib/api/endpoints";
import type {Driver, Load, ParsedLoad} from "@/types/models";

// Query key factory
const loadKeys = {
  all: ['loads'] as const,
  lists: () => [...loadKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...loadKeys.lists(), { filters }] as const,
  details: () => [...loadKeys.all, 'detail'] as const,
  detail: (id: number) => [...loadKeys.details(), id] as const,
  assigned: ['assigned-drivers'] as const,
  available: ['available-drivers'] as const,
};

// Fetch all loads
export const useLoads = (page = 0, limit = 100) => {
  return useQuery({
    queryKey: loadKeys.list({ page, limit }),
    queryFn: () =>
      apiRequest<Load[]>({
        url: API_ENDPOINTS.loads.getAll,
        params: { skip: page * limit, limit },
      }),
  });
};

// Fetch a single load by ID
export const useLoad = (id: number) => {
  return useQuery({
    queryKey: loadKeys.detail(id),
    queryFn: () =>
      apiRequest<Load>({
        url: API_ENDPOINTS.loads.getById(id),
      }),
    enabled: !!id,
  });
};

// Parse load text
export const useParseLoad = () => {
  return useMutation({
    mutationFn: (text: string) =>
      apiRequest<ParsedLoad>({
        url: API_ENDPOINTS.loads.parse,
        method: "POST",
        data: text,
        headers: {
          "Content-Type": "text/plain",
        }
      }),
  });
};

// Create a load from parsed text
export const useCreateLoad = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      text,
      dispatcherId,
      parsedData
    }: {
      text: string;
      dispatcherId?: number;
      parsedData?: any;
    }) => {
      if (!text?.trim()) {
        throw new Error("Load text is required");
      }

      return apiRequest<Load>({
        url: API_ENDPOINTS.loads.create,
        method: "POST",
        data: text.trim(),
        params: dispatcherId ? { dispatcher_id: dispatcherId } : undefined,
        headers: {
          "Content-Type": "text/plain",
        }
      });
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: loadKeys.lists() });
      queryClient.setQueryData(loadKeys.detail(data.id), data);
      console.log("Load created successfully:", data);
    },
    onError: (error) => {
      console.error("Failed to create load:", error);
    },
  });
};

// Update a load
export const useUpdateLoad = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      loadId,
      updateData
    }: {
      loadId: number;
      updateData: Partial<Load>;
    }) => {
      return apiRequest<Load>({
        url: API_ENDPOINTS.loads.update(loadId),
        method: "PUT",
        data: updateData,
        headers: {
          "Content-Type": "application/json",
        }
      });
    },
    onSuccess: (data, variables) => {
      // Update the specific load in cache
      queryClient.setQueryData(loadKeys.detail(variables.loadId), data);
      // Invalidate the lists to refresh
      queryClient.invalidateQueries({ queryKey: loadKeys.lists() });
      queryClient.invalidateQueries({ queryKey: loadKeys.assigned });
      queryClient.invalidateQueries({ queryKey: loadKeys.available });
    },
    onError: (error) => {
      console.error("Failed to update load:", error);
    },
  });
};

// Delete a load
export const useDeleteLoad = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (loadId: number) => {
      console.log('API: Deleting load', loadId);
      const result = await apiRequest<{ message: string }>({
        url: API_ENDPOINTS.loads.delete(loadId),
        method: "DELETE",
      });
      console.log('API: Delete response', result);
      return result;
    },
    onSuccess: (data, loadId) => {
      console.log('API: Delete success', data, loadId);
      // Remove from cache
      queryClient.removeQueries({ queryKey: loadKeys.detail(loadId) });
      // Invalidate lists to refresh
      queryClient.invalidateQueries({ queryKey: loadKeys.lists() });
      queryClient.invalidateQueries({ queryKey: loadKeys.assigned });
      queryClient.invalidateQueries({ queryKey: loadKeys.available });
    },
    onError: (error, loadId) => {
      console.error('API: Delete error', error, loadId);
    },
  });
};

// Update load with parsed data
export const useUpdateLoadWithParsedData = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      loadId,
      text,
      dispatcherId
    }: {
      loadId: number;
      text: string;
      dispatcherId?: number;
    }) => {
      return apiRequest<Load>({
        url: API_ENDPOINTS.loads.updateWithParsedData(loadId),
        method: "PUT",
        data: text.trim(),
        params: dispatcherId ? { dispatcher_id: dispatcherId } : undefined,
        headers: {
          "Content-Type": "text/plain",
        }
      });
    },
    onSuccess: (data, variables) => {
      queryClient.setQueryData(loadKeys.detail(variables.loadId), data);
      queryClient.invalidateQueries({ queryKey: loadKeys.lists() });
    },
    onError: (error) => {
      console.error("Failed to update load with parsed data:", error);
    },
  });
};

// Assign dispatcher to a load
export const useSetDispatcherForLoad = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ loadId, dispatcherId }: { loadId: number; dispatcherId: number }) =>
      apiRequest<{ message: string }>({
        url: API_ENDPOINTS.loads.setDispatcher(loadId, dispatcherId),
        method: "GET",
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: loadKeys.detail(variables.loadId) });
      queryClient.invalidateQueries({ queryKey: loadKeys.lists() });
    },
  });
};

// Assign driver to a load
export const useAssignDriverToLoad = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ loadId, driverId }: { loadId: number; driverId: number }) =>
      apiRequest<Load>({
        url: API_ENDPOINTS.loadManagement.assignDriver(loadId, driverId),
        method: "PUT",
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: loadKeys.detail(variables.loadId) });
      queryClient.invalidateQueries({ queryKey: loadKeys.lists() });
      queryClient.invalidateQueries({ queryKey: loadKeys.assigned });
      queryClient.invalidateQueries({ queryKey: loadKeys.available });
    },
  });
};

// Notify driver about a load
export const useNotifyDriver = () => {
  return useMutation({
    mutationFn: ({ loadId, driverId }: { loadId: number; driverId?: number }) =>
      apiRequest<{ success: boolean }>({
        url: API_ENDPOINTS.loadManagement.notifyDriver(loadId, driverId),
        method: "POST",
      }),
  });
};

// Get assigned drivers
export const useAssignedDrivers = () => {
  return useQuery({
    queryKey: loadKeys.assigned,
    queryFn: () =>
      apiRequest<Driver[]>({
        url: API_ENDPOINTS.loadManagement.assignedDrivers,
      }),
  });
};

// Get available drivers
export const useAvailableDrivers = () => {
  return useQuery({
    queryKey: loadKeys.available,
    queryFn: () =>
      apiRequest<Driver[]>({
        url: API_ENDPOINTS.loadManagement.availableDrivers,
      }),
  });
};