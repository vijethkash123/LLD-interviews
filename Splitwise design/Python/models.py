from enum import Enum
from typing import List


class Group:
    id: str
    name: str
    members: List['User']
    expenses: List['Expense']
    balance_sheets: dict['User', 'BalanceSheet']

    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.members = []
        self.expenses = []
        self.balance_sheets = {}

    def add_member(self, user: 'User'):
        self.members.append(user)
        self.balance_sheets[user] = self.balance_sheets.get(user, BalanceSheet())
    
    def add_expense(self, expense: 'Expense'):
        self.expenses.append(expense)

    def get_balance_sheet(self, user: User) -> 'BalanceSheet':
        return self.balance_sheets.get(user) if self.balance_sheets.get(user) is not None else BalanceSheet()


class User:
    id: str
    name: str

    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name



class Split:
    user: User
    amount: float

    def __init__(self, user: User, amount: float):
        self.user = user
        self.amount = amount

    def set_amount(self, amount: float):
        self.amount = amount

# enum for split type
class SplitType(Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"

class Expense:
    description: str
    amount: float
    paid_by: User
    splits: List[Split]
    split_type: SplitType

    def __init__(self, description: str, amount: float, paid_by: User, splits: List[Split], split_type: SplitType):
        self.description = description
        self.amount = amount
        self.paid_by = paid_by
        self.splits = splits
        self.split_type = split_type



class BalanceSheet:
    total_paid: float  # total amount paid by the user since group creation
    total_expense: float  # total amount owed by the user since group creation
    balances = dict['User', float]  # other user id -> balance (positive means the user is owed money, negative means the user owes money to the other user)

    def __init__(self):
        self.total_paid = 0.0
        self.total_expense = 0.0
        self.balances = {}

    def addTotalPaid(self, amount: float):
        self.total_paid += amount
    
    def addTotalExpense(self, amount: float):
        self.total_expense += amount
    
    def addBalance(self, other: User, amount: float):
        self.balances[other] = self.balances.get(other, 0) + amount
        if self.balances[other] == 0:
            del self.balances[other]
    
    def clearBalance(self):
        self.balances.clear()

    def print(self, me: User):
        you_owe = 0.0
        you_get_back = 0.0
        for amount in self.balances.values():
            if amount < 0:
                you_owe += -amount
            else:
                you_get_back += amount

        lines = []
        lines.append(f"💵 Balance sheet of : {me.name}")
        lines.append(f"Total You Paid : {self.total_paid}")
        lines.append(f"Total Expense : {self.total_expense}")
        lines.append(f"Total You Owe : {you_owe}")
        lines.append(f"Total You Get Back : {you_get_back}")

        for other, amount in self.balances.items():
            if amount > 0:
                lines.append(f"You get back {amount} from {other.name}")
            elif amount < 0:
                lines.append(f"You owe {-amount} to {other.name}")

        lines.append("---------------------------------")
        lines.append("---------------------------------")
        return "\n".join(lines)
