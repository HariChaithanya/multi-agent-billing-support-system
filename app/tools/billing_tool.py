from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer, Invoice, Payment


def _decimal_to_float(value: Decimal | None) -> float:
    return float(value) if value is not None else 0.0


async def fetch_billing_analysis(session: AsyncSession, customer_id: str) -> dict:
    customer_result = await session.execute(
        select(Customer).where(Customer.external_id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if customer is None:
        return {"found": False, "customer_id": customer_id}

    invoice_result = await session.execute(
        select(Invoice)
        .where(Invoice.customer_id == customer.id)
        .order_by(Invoice.issued_at.desc())
    )
    invoices = invoice_result.scalars().all()

    payment_result = await session.execute(
        select(Payment)
        .where(Payment.customer_id == customer.id)
        .order_by(Payment.paid_at.desc())
    )
    payments = payment_result.scalars().all()

    outstanding = sum(
        _decimal_to_float(invoice.amount)
        for invoice in invoices
        if invoice.status in {"issued", "overdue"}
    )

    return {
        "found": True,
        "customer_id": customer_id,
        "summary": {
            "invoice_count": len(invoices),
            "payment_count": len(payments),
            "total_outstanding": outstanding,
            "open_invoices": sum(
                1 for invoice in invoices if invoice.status in {"issued", "overdue"}
            ),
        },
        "invoices": [
            {
                "invoice_number": invoice.invoice_number,
                "amount": _decimal_to_float(invoice.amount),
                "currency": invoice.currency,
                "status": invoice.status,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "description": invoice.description,
            }
            for invoice in invoices
        ],
        "payments": [
            {
                "amount": _decimal_to_float(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "payment_method": payment.payment_method,
                "transaction_ref": payment.transaction_ref,
            }
            for payment in payments
        ],
    }
