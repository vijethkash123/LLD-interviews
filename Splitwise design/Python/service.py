import heapq
import uuid
from typing import List, Optional, Dict

from models import Group, User, SplitType, Expense, Split
from splitStrategyFactory import SplitStrategyFactory


class GroupRepository:
    def __init__(self):
        self._store: Dict[str, Group] = {}

    def save(self, group: Group):
        self._store[group.id] = group

    def find_by_id(self, group_id: str) -> Optional[Group]:
        return self._store.get(group_id)

class GroupService:
    def __init__(self, repo: GroupRepository, expense_service: 'ExpenseService', simplifier: 'DebtSimplificationService'):
        self.repo = repo
        self.expense_service = expense_service
        self.simplifier = simplifier

    def create_group(self, name: str, members: List[User]) -> str:
        group_id = str(uuid.uuid4())
        g = Group(group_id, name)
        for member in members:
            g.add_member(member)
        self.repo.save(g)
        return group_id

    def add_member(self, group_id: str, user: User):
        self._get(group_id).add_member(user)

    def add_expense(self, group_id: str, description: str, amount: float,
                    paid_by: User, participants: List[User],
                    split_type: SplitType, meta: dict):
        self.expense_service.addExpense(
            self._get(group_id), description, amount,
            paid_by, participants, split_type, meta
        )

    def simplify_debts(self, group_id: str):
        self.simplifier.simplify_debts(self._get(group_id))

    def print_balances(self, group_id: str):
        g = self._get(group_id)
        for user in g.members:
            sheet = g.get_balance_sheet(user)
            print(sheet.print(user))

    def _get(self, group_id: str) -> Group:
        g = self.repo.find_by_id(group_id)
        if g is None:
            raise ValueError(f"Group not found: {group_id}")
        return g



class BalanceSheetService:
    def updateBalances(self, group: Group, paid_by: User, splits: List[Split]):
        total_amount = sum(split.amount for split in splits)
        group.get_balance_sheet(paid_by).addTotalPaid(total_amount)
        for split in splits:
            user = split.user
            amount = split.amount
            group.get_balance_sheet(user).addTotalExpense(amount)
            if user != paid_by:
                group.get_balance_sheet(user).addBalance(paid_by, -amount)
                group.get_balance_sheet(paid_by).addBalance(user, amount)


class DebtSimplificationService:
    def simplify_debts(self, group: Group):
        users = list(group.members)
        sheets = group.balance_sheets  # Dict[User, BalanceSheet]

        # Step 1: Calculate net balance for each user and clear old balances
        net_balances: Dict[User, float] = {}
        for user in users:
            net = sum(sheets[user].balances.values())
            net_balances[user] = net
            sheets[user].clearBalance()

        # Step 2: Separate creditors (net > 0) and debtors (net < 0)
        # creditors: max-heap by net amount (negate for heapq)
        creditors = []  # (-net, user.id, user)
        debtors = []    # (net, user.id, user)
        for user in users:
            net = net_balances[user]
            if net > 0:
                heapq.heappush(creditors, (-net, user.id, user))
            elif net < 0:
                heapq.heappush(debtors, (net, user.id, user))

        # Step 3: Match debtors and creditors to settle debts
        while creditors and debtors:
            neg_credit, _, creditor = heapq.heappop(creditors)
            debit, _, debtor = heapq.heappop(debtors)

            credit_amount = -neg_credit
            debit_amount = debit  # negative value

            settled = min(credit_amount, -debit_amount)

            sheets[creditor].addBalance(debtor, settled)
            sheets[debtor].addBalance(creditor, -settled)

            net_balances[creditor] = credit_amount - settled
            net_balances[debtor] = debit_amount + settled

            if net_balances[creditor] > 0:
                heapq.heappush(creditors, (-net_balances[creditor], creditor.id, creditor))
            if net_balances[debtor] < 0:
                heapq.heappush(debtors, (net_balances[debtor], debtor.id, debtor))

class ExpenseService:
    def __init__(self, balance_sheet_service: BalanceSheetService):
        self.balance_sheet_service = balance_sheet_service

    def addExpense(self, group: Group, description: str, amount: float, paid_by: User, participants: List[User], split_type: SplitType, metadata: dict[User, float]):
        split_strategy = SplitStrategyFactory.get_split_strategy(split_type)
        splits: List[Split] = split_strategy.split(amount, participants, metadata)
        expense: Expense = Expense(description, amount, paid_by, splits, split_type)
        group.add_expense(expense)
        self.balance_sheet_service.updateBalances(group, paid_by, splits)