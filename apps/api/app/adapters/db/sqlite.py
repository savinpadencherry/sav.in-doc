"""
SQLite adapter for ChainSync
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import json
from datetime import datetime

from ...domain.ports import OrderRepository
from ...domain.models import Order, Priority, Coordinates, TimeWindow, Item, Dimensions

Base = declarative_base()

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True)
    customer = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    weight = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    priority = Column(String, nullable=False)
    items_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SQLiteOrderRepository(OrderRepository):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
    
    def _to_domain(self, model: OrderModel) -> Order:
        """Convert SQLAlchemy model to domain object"""
        items_data = json.loads(model.items_json)
        items = [
            Item(
                sku=item["sku"],
                name=item["name"],
                quantity=item["quantity"],
                weight=item["weight"],
                dimensions=Dimensions(**item["dimensions"])
            )
            for item in items_data
        ]
        
        return Order(
            id=model.id,
            customer=model.customer,
            address=model.address,
            coordinates=Coordinates(lat=model.lat, lng=model.lng),
            time_window=TimeWindow(
                start=model.time_window_start,
                end=model.time_window_end
            ),
            weight=model.weight,
            volume=model.volume,
            priority=Priority(model.priority),
            items=items,
            created_at=model.created_at
        )
    
    def _to_model(self, order: Order) -> OrderModel:
        """Convert domain object to SQLAlchemy model"""
        items_data = [
            {
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "weight": item.weight,
                "dimensions": {
                    "length": item.dimensions.length,
                    "width": item.dimensions.width,
                    "height": item.dimensions.height
                }
            }
            for item in order.items
        ]
        
        return OrderModel(
            id=order.id,
            customer=order.customer,
            address=order.address,
            lat=order.coordinates.lat,
            lng=order.coordinates.lng,
            time_window_start=order.time_window.start,
            time_window_end=order.time_window.end,
            weight=order.weight,
            volume=order.volume,
            priority=order.priority.value,
            items_json=json.dumps(items_data),
            created_at=order.created_at
        )
    
    async def save(self, order: Order) -> Order:
        model = self._to_model(order)
        self.session.merge(model)
        self.session.commit()
        return order
    
    async def find_by_id(self, order_id: str) -> Optional[Order]:
        model = self.session.query(OrderModel).filter(OrderModel.id == order_id).first()
        return self._to_domain(model) if model else None
    
    async def find_all(self) -> List[Order]:
        models = self.session.query(OrderModel).all()
        return [self._to_domain(model) for model in models]
    
    async def delete(self, order_id: str) -> bool:
        model = self.session.query(OrderModel).filter(OrderModel.id == order_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()
            return True
        return False