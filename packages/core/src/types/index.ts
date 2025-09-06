// Common types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  total: number
  page: number
  limit: number
}

// Vehicle types
export interface Vehicle {
  id: string
  name: string
  capacity: {
    weight: number
    volume: number
  }
  compartments: Compartment[]
}

export interface Compartment {
  id: string
  name: string
  zones: Zone[]
  maxWeight: number
  maxVolume: number
}

export interface Zone {
  id: string
  name: string
  levels: number
  accessible: boolean
}

// Analytics types
export interface KPI {
  label: string
  value: string | number
  change?: number
  trend?: 'up' | 'down' | 'neutral'
}