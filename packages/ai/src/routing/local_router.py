"""
Local route optimization using OR-Tools
"""
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math

@dataclass
class Location:
    id: str
    lat: float
    lng: float
    time_window_start: int = 0  # minutes from start of day
    time_window_end: int = 1440  # minutes from start of day (24 hours)
    service_time: int = 30  # minutes

@dataclass
class RouteResult:
    vehicle_id: int
    stops: List[Tuple[str, int]]  # (location_id, arrival_time)
    total_distance: float
    total_time: int

class LocalRouter:
    def __init__(self, max_vehicles: int = 5):
        self.max_vehicles = max_vehicles
        
    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance between two points in kilometers"""
        R = 6371  # Earth radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def create_distance_matrix(self, locations: List[Location]) -> List[List[int]]:
        """Create distance matrix in meters"""
        n = len(locations)
        matrix = [[0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_km = self.haversine_distance(
                        locations[i].lat, locations[i].lng,
                        locations[j].lat, locations[j].lng
                    )
                    matrix[i][j] = int(dist_km * 1000)  # Convert to meters
        
        return matrix
    
    def solve_vrp(self, locations: List[Location], depot_idx: int = 0) -> List[RouteResult]:
        """Solve Vehicle Routing Problem with time windows"""
        if len(locations) <= 1:
            return []
        
        # Create distance matrix
        distance_matrix = self.create_distance_matrix(locations)
        
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(
            len(locations), 
            min(self.max_vehicles, len(locations) - 1), 
            depot_idx
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Time windows
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_time = distance_matrix[from_node][to_node] // 500  # Assume 30 km/h average speed
            return travel_time + locations[from_node].service_time
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            60,  # slack
            1440,  # maximum time per vehicle (24 hours)
            False,  # start cumul to zero
            'Time'
        )
        time_dimension = routing.GetDimensionOrDie('Time')
        
        # Add time windows
        for location_idx, location in enumerate(locations):
            if location_idx == depot_idx:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(
                location.time_window_start, 
                location.time_window_end
            )
        
        # Solve
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            return []
        
        # Extract routes
        routes = []
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route_stops = []
            total_distance = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                time_var = time_dimension.CumulVar(index)
                arrival_time = solution.Value(time_var)
                
                route_stops.append((locations[node_index].id, arrival_time))
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                if not routing.IsEnd(index):
                    total_distance += distance_matrix[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
            
            if len(route_stops) > 1:  # Only include routes with actual stops
                routes.append(RouteResult(
                    vehicle_id=vehicle_id,
                    stops=route_stops,
                    total_distance=total_distance / 1000.0,  # Convert to km
                    total_time=solution.Value(time_dimension.CumulVar(routing.End(vehicle_id)))
                ))
        
        return routes