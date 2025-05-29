import axios, {type AxiosInstance, type AxiosRequestConfig} from "axios"

// Base API client
const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export const createApiClient = (): AxiosInstance => {
	const client = axios.create({
		baseURL,
		headers: {
			"Content-Type": "application/json",
		},
	})
	
	// Request interceptor for adding auth token
	client.interceptors.request.use((config) => {
		const token = localStorage.getItem("auth_token")
		if (token) {
			config.headers.Authorization = `Bearer ${token}`
		}
		return config
	})
	
	// Response interceptor for handling errors
	client.interceptors.response.use(
		(response) => response,
		(error) => {
			if (error.response?.status === 401) {
				localStorage.removeItem("auth_token")
				window.location.href = "/login"
			}
			return Promise.reject(error)
		}
	)
	
	return client
}

const apiClient = createApiClient()

export default apiClient

// API request wrapper with type safety
export const apiRequest = async <T>({
	                                    method = "GET",
	                                    url,
	                                    data,
	                                    params,
	                                    headers,
                                    }: AxiosRequestConfig): Promise<T> => {
	try {
		const response = await apiClient({
			method,
			url,
			data,
			params,
			headers,
		})
		return response.data
	} catch (error) {
		if (axios.isAxiosError(error)) {
			throw new Error(
				error.response?.data?.detail || error.message || "API request failed"
			)
		}
		throw error
	}
}