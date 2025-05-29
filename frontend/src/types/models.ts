import {z} from "zod"

// Company schemas
export const CompanySchema = z.object({
	id: z.number(),
	name: z.string(),
	usdot: z.number(),
	carrier_identifier: z.string(),
	mc: z.number(),
	drivers_count: z.number(),
})

export const CompanyCreateSchema = z.object({
	name: z.string().min(1, "Company name is required"),
	usdot: z.number().min(1, "USDOT number is required"),
	carrier_identifier: z.string().min(1, "Carrier identifier is required"),
	mc: z.number().min(1, "MC number is required"),
})

// Driver schemas
export const DriverSchema = z.object({
	id: z.number(),
	name: z.string(),
	company_id: z.number(),
	chat_id: z.number().nullable().optional(),
})

export const DriverCreateSchema = z.object({
	name: z.string().min(1, "Driver name is required"),
	company_id: z.number().min(1, "Company is required"),
	chat_id: z.number().nullable().optional(),
})

// Dispatcher schemas
export const DispatcherSchema = z.object({
	id: z.number(),
	name: z.string(),
	telegram_id: z.number(),
})

export const DispatcherCreateSchema = z.object({
	name: z.string().min(1, "Dispatcher name is required"),
	telegram_id: z.number().min(1, "Telegram ID is required"),
})

// Leg schema for load details
export const LegSchema = z.object({
	id: z.number(),
	leg_id: z.string(),
	pickup_facility_id: z.string().or(z.number()).nullable().optional(),
	dropoff_facility_id: z.string().or(z.number()).nullable().optional(),
	pickup_address: z.string().nullable().optional(),
	dropoff_address: z.string().nullable().optional(),
	pickup_time: z.string().datetime().nullable().optional(),
	dropoff_time: z.string().datetime().nullable().optional(),
	fuel_sur_charge: z.number(),
	distance: z.number().nullable().optional(),
	assigned_driver: z.string().nullable().optional(),
})

// Load schema
export const LoadSchema = z.object({
	id: z.number(),
	trip_id: z.string(),
	pickup_facility: z.string().nullable().optional(),
	dropoff_facility: z.string().nullable().optional(),
	pickup_address: z.string().nullable().optional(),
	dropoff_address: z.string().nullable().optional(),
	start_time: z.string().datetime(),
	end_time: z.string().datetime(),
	rate: z.number(),
	rate_per_mile: z.number(),
	distance: z.number().nullable().optional(),
	assigned_driver: z.string().nullable().optional(),
	legs: z.array(LegSchema).optional(),
})

// Parsed load response schema
export const ParsedLoadSchema = z.object({
	tripInfo: z.record(z.any()),
	legs: z.array(z.record(z.any())),
})

// Types
export type Company = z.infer<typeof CompanySchema>
export type CompanyCreate = z.infer<typeof CompanyCreateSchema>
export type Driver = z.infer<typeof DriverSchema>
export type DriverCreate = z.infer<typeof DriverCreateSchema>
export type Dispatcher = z.infer<typeof DispatcherSchema>
export type DispatcherCreate = z.infer<typeof DispatcherCreateSchema>
export type Leg = z.infer<typeof LegSchema>
export type Load = z.infer<typeof LoadSchema>
export type ParsedLoad = z.infer<typeof ParsedLoadSchema>