from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer


async def fetch_customer_profile(session: AsyncSession, customer_id: str) -> dict:
    result = await session.execute(
        select(Customer).where(Customer.external_id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        return {"found": False, "customer_id": customer_id}

    return {
        "found": True,
        "id": customer.id,
        "external_id": customer.external_id,
        "email": customer.email,
        "full_name": customer.full_name,
        "phone": customer.phone,
        "status": customer.status,
    }
