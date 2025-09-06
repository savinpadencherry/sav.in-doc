"""
Domain models for ChainSync
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

@dataclass
class Coordinates:
    lat: float
    lng: float

@dataclass
class TimeWindow:
    start: datetime
    end: datetime

@dataclass
class Dimensions:
    length: float
    width: float
    height: float

@dataclass
class Item:
    sku: str
    name: str
    quantity: int
    weight: float
    dimensions: Dimensions

@dataclass
class Order:
    id: str
    customer: str
    address: str
    coordinates: Coordinates
    time_window: TimeWindow
    weight: float
    volume: float
    priority: Priority
    items: List[Item]
    created_at: datetime

@dataclass
class Stop:
    order_id: str
    sequence_number: int
    estimated_arrival: datetime
    coordinates: Coordinates

@dataclass
class Route:
    id: str
    vehicle_id: str
    stops: List[Stop]
    total_distance: float
    total_duration: int  # minutes
    created_at: datetime

@dataclass
class LoadPosition:
    compartment: str
    zone: str
    level: int

@dataclass
class LoadStep:
    id: str
    order_id: str
    item: str
    position: LoadPosition
    sequence_number: int
    is_accessible: bool

@dataclass
class LoadPlan:
    id: str
    vehicle_id: str
    steps: List[LoadStep]
    efficiency: float
    created_at: datetime