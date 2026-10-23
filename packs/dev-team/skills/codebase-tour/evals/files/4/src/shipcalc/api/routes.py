from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel

from shipcalc.api.preview import free_shipping_banner
from shipcalc.discounts import loyalty_discount
from shipcalc.shipping import shipping_cost
from shipcalc.tax import vat

router = APIRouter()


class QuoteRequest(BaseModel):
    region: str
    subtotal: Decimal
    weight_kg: Decimal
    tier: str = "bronze"


@router.post("/quote")
def quote(req: QuoteRequest) -> dict:
    discount = loyalty_discount(req.tier, req.subtotal)
    shipping = shipping_cost(req.region, req.subtotal, req.weight_kg)
    tax = vat(req.region, req.subtotal - discount + shipping)
    return {
        "discount": str(discount),
        "shipping": str(shipping),
        "tax": str(tax),
        "total": str(req.subtotal - discount + shipping + tax),
    }


@router.get("/preview/banner")
def banner(region: str, subtotal: Decimal) -> dict:
    return {"banner": free_shipping_banner(region, subtotal)}
