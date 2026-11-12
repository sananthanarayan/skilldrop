"""Loans for the Pellow Street lending library."""
from dataclasses import dataclass, field
from datetime import date, timedelta

LOAN_DAYS = 21
RENEWAL_DAYS = 14
MAX_RENEWALS = 2


class LoanError(Exception):
    pass


@dataclass
class Loan:
    item_id: str
    member_id: str
    due: date
    renewals: int = 0


class Desk:
    def __init__(self):
        self.loans = {}  # item_id -> Loan
        self.holds = {}  # item_id -> member_ids waiting, oldest first

    def lend(self, item_id, member_id, today):
        if item_id in self.loans:
            raise LoanError(f"{item_id} is already on loan")
        waiting = self.holds.get(item_id, [])
        if waiting and waiting[0] != member_id:
            raise LoanError(f"{item_id} is held for another member")
        if waiting:
            waiting.pop(0)
        loan = Loan(item_id, member_id, today + timedelta(days=LOAN_DAYS))
        self.loans[item_id] = loan
        return loan

    def place_hold(self, item_id, member_id):
        queue = self.holds.setdefault(item_id, [])
        if member_id not in queue:
            queue.append(member_id)

    def renew(self, item_id, member_id):
        loan = self.loans.get(item_id)
        if loan is None or loan.member_id != member_id:
            raise LoanError(f"{member_id} has no loan of {item_id}")
        others = [m for m in self.holds.get(item_id, []) if m != member_id]
        if others:
            raise LoanError(f"{item_id} is on hold for another member")
        if loan.renewals > MAX_RENEWALS:
            raise LoanError(f"{item_id} has already been renewed {MAX_RENEWALS} times")
        loan.due = loan.due + timedelta(days=RENEWAL_DAYS)
        loan.renewals += 1
        return loan

    def give_back(self, item_id):
        return self.loans.pop(item_id, None)
