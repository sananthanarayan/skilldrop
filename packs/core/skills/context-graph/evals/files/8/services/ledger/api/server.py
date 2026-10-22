from concurrent import futures

import grpc

from services.ledger.api import idempotency
from services.ledger.api.gen import ledger_pb2, ledger_pb2_grpc
from services.ledger.logging import get_logger

log = get_logger(__name__)


class LedgerServicer(ledger_pb2_grpc.LedgerServicer):
    def __init__(self, db):
        self.db = db

    def PostEntry(self, request, context):
        with self.db.transaction() as conn:
            cached = idempotency.lookup(conn, request.idempotency_key)
            if cached:
                return ledger_pb2.PostEntryResponse(**cached)
            entry_id = self.db.post_entry(conn, request)
            idempotency.store(conn, request.idempotency_key, {"entry_id": entry_id})
        return ledger_pb2.PostEntryResponse(entry_id=entry_id)

    def GetBalance(self, request, context):
        return self.db.balance(request.account_id)


def serve(db, port: int = 50051) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    ledger_pb2_grpc.add_LedgerServicer_to_server(LedgerServicer(db), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    log.info("ledger gRPC server started")
    server.wait_for_termination()
