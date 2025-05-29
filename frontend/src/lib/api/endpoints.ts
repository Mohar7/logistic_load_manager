// API endpoints organized by domain
const API_ENDPOINTS = {
    // Load management endpoints
    loads: {
       getAll: "/loads",
       getById: (id: number) => `/loads/${id}`,
       create: "/loads/create",
       update: (id: number) => `/loads/${id}`,
       updateWithParsedData: (id: number) => `/loads/${id}/parse`,
       delete: (id: number) => `/loads/${id}`,
       parse: "/loads/parse",
       setDispatcher: (loadId: number, dispatcherId: number) =>
          `/loads/set_dispatcher/${loadId}/${dispatcherId}`,
    },
    
    // Load management endpoints
    loadManagement: {
       assignDriver: (loadId: number, driverId: number) =>
          `/load-management/${loadId}/assign-driver/${driverId}`,
       notifyDriver: (loadId: number, driverId?: number) =>
          `/load-management/${loadId}/notify-driver${driverId ? `?driver_id=${driverId}` : ''}`,
       assignedDrivers: "/load-management/assigned-drivers",
       availableDrivers: "/load-management/available-drivers",
    },
    
    // Driver management endpoints
    drivers: {
       getAll: "/drivers",
       getById: (id: number) => `/drivers/${id}`,
       create: "/drivers",
       update: (id: number) => `/drivers/${id}`,
       delete: (id: number) => `/drivers/${id}`,
       byCompany: (companyId: number) => `/drivers?company_id=${companyId}`,
    },
    
    // Company management endpoints
    companies: {
       getAll: "/companies",
       getById: (id: number) => `/companies/${id}`,
       create: "/companies",
       update: (id: number) => `/companies/${id}`,
       delete: (id: number) => `/companies/${id}`,
    },
    
    // Dispatcher management endpoints
    dispatchers: {
       getAll: "/dispatchers",
       getById: (id: number) => `/dispatchers/${id}`,
       getByTelegramId: (telegramId: number) => `/dispatchers/telegram/${telegramId}`,
       create: "/dispatchers",
       update: (id: number) => `/dispatchers/${id}`,
       delete: (id: number) => `/dispatchers/${id}`,
    },
    
    // Health check
    health: "/health"
}

export default API_ENDPOINTS