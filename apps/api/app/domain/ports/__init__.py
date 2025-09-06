"""
Domain ports for ChainSync hexagonal architecture
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import Order, Route, LoadPlan

class OrderRepository(ABC):
    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass
    
    @abstractmethod
    async def find_by_id(self, order_id: str) -> Optional[Order]:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Order]:
        pass
    
    @abstractmethod
    async def delete(self, order_id: str) -> bool:
        pass

class RouteRepository(ABC):
    @abstractmethod
    async def save(self, route: Route) -> Route:
        pass
    
    @abstractmethod
    async def find_by_id(self, route_id: str) -> Optional[Route]:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Route]:
        pass

class RouteSolver(ABC):
    @abstractmethod
    async def solve(self, orders: List[Order]) -> List[Route]:
        pass
    
    @abstractmethod
    async def calculate_cost(self, route: Route) -> float:
        pass

class LoadPlanner(ABC):
    @abstractmethod
    async def plan(self, orders: List[Order]) -> LoadPlan:
        pass

class VectorStore(ABC):
    @abstractmethod
    async def add_documents(self, texts: List[str], metadata: List[dict]) -> None:
        pass
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[tuple]:
        pass

class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: dict) -> None:
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler) -> None:
        pass