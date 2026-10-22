"""Order model."""
from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String

from .base import Base

# Keys allowed in Order.attributes (DR-014). Review additions like a column.
ORDER_ATTRIBUTE_KEYS = {
    "delivery_note",
    "leave_with_neighbour",
}


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True)
    customer_id = Column(BigInteger, nullable=False, index=True)
    status = Column(String(16), nullable=False, default="draft")
    currency = Column(String(3), nullable=False)
    subtotal_minor = Column(Integer, nullable=False)
    shipping_minor = Column(Integer, nullable=False, default=0)
    total_minor = Column(Integer, nullable=False)
    placed_at = Column(DateTime(timezone=True))
    attributes = Column(JSON, nullable=False, default=dict)
