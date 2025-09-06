import { z } from 'zod'

// Order schemas
export const OrderSchema = z.object({
  id: z.string(),
  customer: z.string(),
  address: z.string(),
  coordinates: z.object({
    lat: z.number(),
    lng: z.number(),
  }),
  timeWindow: z.object({
    start: z.string(),
    end: z.string(),
  }),
  weight: z.number(),
  volume: z.number(),
  priority: z.enum(['low', 'medium', 'high']),
  items: z.array(z.object({
    sku: z.string(),
    name: z.string(),
    quantity: z.number(),
    weight: z.number(),
    dimensions: z.object({
      length: z.number(),
      width: z.number(),
      height: z.number(),
    }),
  })),
  createdAt: z.string(),
})

export type Order = z.infer<typeof OrderSchema>

// Route schemas
export const RouteSchema = z.object({
  id: z.string(),
  vehicleId: z.string(),
  stops: z.array(z.object({
    orderId: z.string(),
    sequenceNumber: z.number(),
    estimatedArrival: z.string(),
    coordinates: z.object({
      lat: z.number(),
      lng: z.number(),
    }),
  })),
  totalDistance: z.number(),
  totalDuration: z.number(),
  createdAt: z.string(),
})

export type Route = z.infer<typeof RouteSchema>

// Load plan schemas
export const LoadStepSchema = z.object({
  id: z.string(),
  orderId: z.string(),
  item: z.string(),
  position: z.object({
    compartment: z.string(),
    zone: z.string(),
    level: z.number(),
  }),
  sequenceNumber: z.number(),
  isAccessible: z.boolean(),
})

export const LoadPlanSchema = z.object({
  id: z.string(),
  vehicleId: z.string(),
  steps: z.array(LoadStepSchema),
  efficiency: z.number(),
  createdAt: z.string(),
})

export type LoadStep = z.infer<typeof LoadStepSchema>
export type LoadPlan = z.infer<typeof LoadPlanSchema>