from models import User, SplitType
from service import GroupRepository, BalanceSheetService, ExpenseService, DebtSimplificationService, GroupService

if __name__ == "__main__":

    # users
    shubh = User("u1", "Shubh")
    bob   = User("u2", "Bob")
    tom   = User("u3", "Tom")
    jake  = User("u4", "Jake")

    repo                 = GroupRepository()
    balance_sheet_service = BalanceSheetService()
    expense_service      = ExpenseService(balance_sheet_service)
    simplification_service = DebtSimplificationService()

    group_service = GroupService(repo, expense_service, simplification_service)

    # ---------- create groups ----------
    goa_group_id = group_service.create_group("Goa Trip", [shubh, bob, tom])
    misc_group   = group_service.create_group("Non-Group Expenses", [shubh, bob, tom, jake])

    # ---------- add expenses ----------
    group_service.add_expense(goa_group_id,
                              "Lunch Day-1", 100, shubh,
                              [shubh, bob], SplitType.EQUAL, None)

    group_service.add_expense(goa_group_id,
                              "Lunch Day-2", 100, bob,
                              [bob, tom], SplitType.EQUAL, None)

    # ---------- simplify & print ----------
    group_service.simplify_debts(goa_group_id)
    group_service.print_balances(goa_group_id)


"""
With Simplify debt off:
Total You Paid : 100.0
Total Expense : 50.0
Total You Owe : 0.0
Total You Get Back : 50.0
You get back 50.0 from Bob
---------------------------------
---------------------------------
💵 Balance sheet of : Bob
Total You Paid : 100.0
Total Expense : 100.0
Total You Owe : 50.0
Total You Get Back : 50.0
You owe 50.0 to Shubh
You get back 50.0 from Tom
---------------------------------
---------------------------------
💵 Balance sheet of : Tom
Total You Paid : 0.0
Total Expense : 50.0
Total You Owe : 50.0
Total You Get Back : 0.0
You owe 50.0 to Bob
---------------------------------
---------------------------------

------------------------------------------------

With Simplify debt on:
💵 Balance sheet of : Shubh
Total You Paid : 100.0
Total Expense : 50.0
Total You Owe : 0.0
Total You Get Back : 50.0
You get back 50.0 from Tom
---------------------------------
---------------------------------
💵 Balance sheet of : Bob
Total You Paid : 100.0
Total Expense : 100.0
Total You Owe : 0.0
Total You Get Back : 0.0
---------------------------------
---------------------------------
💵 Balance sheet of : Tom
Total You Paid : 0.0
Total Expense : 50.0
Total You Owe : 50.0
Total You Get Back : 0.0
You owe 50.0 to Shubh
---------------------------------
---------------------------------
"""
