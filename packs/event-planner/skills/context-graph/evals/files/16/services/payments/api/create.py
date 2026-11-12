from services.payments.ledger import record_payment


def create_payment(request):
    body = request.json()
    payment = record_payment(request.merchant_id, body)
    return 201, payment
