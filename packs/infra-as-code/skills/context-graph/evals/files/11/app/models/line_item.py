"""Line item model. Immutable once the parent order is placed (DR-009)."""
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String

from .base import Base


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(BigInteger, primary_key=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False, index=True)
    sku = Column(String(32), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_minor = Column(Integer, nullable=False)
