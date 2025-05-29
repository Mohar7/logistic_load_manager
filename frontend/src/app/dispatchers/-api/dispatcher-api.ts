import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";
import API_ENDPOINTS from "@/lib/api/endpoints";
import type {Dispatcher, DispatcherCreate} from "@/types/models";

// Query key factory
const dispatcherKeys = {
  all: ['dispatchers'] as const,
  lists: () => [...dispatcherKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...dispatcherKeys.lists(), { filters }] as const,
  details: () => [...dispatcherKeys.all, 'detail'] as const,
  detail: (id: number) => [...dispatcherKeys.details(), id] as const,
  byTelegram: (telegramId: number) => [...dispatcherKeys.details(), { telegramId }] as const,
};

// Fetch all dispatchers
export const useDispatchers = (
  page = 0,
  limit = 100,
) => {
  return useQuery({
    queryKey: dispatcherKeys.list({ page, limit }),
    queryFn: () =>
      apiRequest<Dispatcher[]>({
        url: API_ENDPOINTS.dispatchers.getAll,
        params: {
          skip: page * limit,
          limit,
        },
      }),
  });
};

// Fetch a single dispatcher by ID
export const useDispatcher = (id: number) => {
  return useQuery({
    queryKey: dispatcherKeys.detail(id),
    queryFn: () =>
      apiRequest<Dispatcher>({
        url: API_ENDPOINTS.dispatchers.getById(id),
      }),
    enabled: !!id,
  });
};

// Fetch a dispatcher by Telegram ID
export const useDispatcherByTelegramId = (telegramId: number) => {
  return useQuery({
    queryKey: dispatcherKeys.byTelegram(telegramId),
    queryFn: () =>
      apiRequest<Dispatcher>({
        url: API_ENDPOINTS.dispatchers.getByTelegramId(telegramId),
      }),
    enabled: !!telegramId,
  });
};

// Create a new dispatcher
export const useCreateDispatcher = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: DispatcherCreate) =>
      apiRequest<Dispatcher>({
        url: API_ENDPOINTS.dispatchers.create,
        method: "POST",
        data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dispatcherKeys.lists() });
    },
  });
};

// Update a dispatcher
export const useUpdateDispatcher = (id: number) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { name?: string; telegram_id?: number }) =>
      apiRequest<Dispatcher>({
        url: API_ENDPOINTS.dispatchers.update(id),
        method: "PUT",
        params: {
          ...(data.name && { name: data.name }),
          ...(data.telegram_id && { telegram_id: data.telegram_id }),
        },
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: dispatcherKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: dispatcherKeys.lists() });
      if (data.telegram_id) {
        queryClient.invalidateQueries({
          queryKey: dispatcherKeys.byTelegram(data.telegram_id)
        });
      }
    },
  });
};

// Delete a dispatcher
export const useDeleteDispatcher = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest({
        url: API_ENDPOINTS.dispatchers.delete(id),
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dispatcherKeys.lists() });
    },
  });
};