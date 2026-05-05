from decimal import Decimal
from typing import Dict

from exceptions import InvalidStateException, InvalidTransactionException
from models import Product, Rack
from vending_machine import VendingMachine


def main():
    print("=" * 60)
    print("   VENDING MACHINE — LLD DEMO")
    print("=" * 60)

    # ── Setup ──────────────────────────────────────────────────────────────
    vm = VendingMachine()

    chips = Product("P001", "Lays Classic Chips", Decimal("20.00"))
    cola = Product("P002", "Coca-Cola 330ml", Decimal("35.00"))
    water = Product("P003", "Mineral Water 500ml", Decimal("15.00"))

    racks: Dict[str, Rack] = {
        "R01": Rack("R01", chips, 5),
        "R02": Rack("R02", cola, 3),
        "R03": Rack("R03", water, 0),  # empty rack — for error demo
    }
    vm.set_rack(racks)

    print("\n[Admin] Racks loaded:")
    for code, rack in racks.items():
        print(f"  {code}: {rack.get_product().get_description()} "
              f"@ ₹{rack.get_product().get_unit_price()} x{rack.get_product_count()}")

    # ── Scenario 1: Normal purchase ────────────────────────────────────────
    print("\n" + "-" * 50)
    print("Scenario 1: Normal purchase (Chips ₹20, insert ₹50)")
    print("-" * 50)
    print(f"State: {vm.get_current_state().get_state_description()}")

    vm.insert_money(50.0)
    print(f"  Balance: ₹{vm.get_payment_processor().get_current_balance()}")
    print(f"  State: {vm.get_current_state().get_state_description()}")

    vm.select_product_by_code("R01")
    print(f"  State: {vm.get_current_state().get_state_description()}")

    vm.dispense_product_action()
    print(f"  Final state: {vm.get_current_state().get_state_description()}")

    # ── Scenario 2: Exact change ───────────────────────────────────────────
    print("\n" + "-" * 50)
    print("Scenario 2: Exact change purchase (Cola ₹35, insert ₹35)")
    print("-" * 50)

    vm.insert_money(35.0)
    vm.select_product_by_code("R02")
    vm.dispense_product_action()

    # ── Scenario 3: Select without money ──────────────────────────────────
    print("\n" + "-" * 50)
    print("Scenario 3: Select product without inserting money (error)")
    print("-" * 50)
    try:
        vm.select_product_by_code("R01")
    except InvalidStateException as e:
        print(f"  [Caught InvalidStateException] {e}")

    # ── Scenario 4: Insufficient funds ────────────────────────────────────
    print("\n" + "-" * 50)
    print("Scenario 4: Insufficient funds (Cola ₹35, insert ₹10)")
    print("-" * 50)
    vm.insert_money(10.0)
    vm.select_product_by_code("R02")
    try:
        vm.dispense_product_action()
    except InvalidTransactionException as e:
        print(f"  [Caught InvalidTransactionException] {e}")
    print("  Cancelling transaction...")
    vm.cancel_transaction()

    # ── Scenario 5: Empty rack ─────────────────────────────────────────────
    print("\n" + "-" * 50)
    print("Scenario 5: Empty rack (Water ₹15, count=0)")
    print("-" * 50)
    vm.insert_money(20.0)
    vm.select_product_by_code("R03")
    try:
        vm.dispense_product_action()
    except InvalidTransactionException as e:
        print(f"  [Caught InvalidTransactionException] {e}")
    vm.cancel_transaction()

    # ── Scenario 6: Multiple inserts before selection ──────────────────────
    print("\n" + "-" * 50)
    print("Scenario 6: Multiple money inserts (add ₹10 + ₹10 → buy Chips ₹20)")
    print("-" * 50)
    vm.insert_money(10.0)
    vm.insert_money(10.0)
    print(f"  Balance after two inserts: ₹{vm.get_payment_processor().get_current_balance()}")
    vm.select_product_by_code("R01")
    vm.dispense_product_action()

    # ── Scenario 7: Cancel mid-flow ────────────────────────────────────────
    print("\n" + "-" * 50)
    print("Scenario 7: Cancel after inserting money")
    print("-" * 50)
    vm.insert_money(100.0)
    print(f"  State: {vm.get_current_state().get_state_description()}")
    vm.cancel_transaction()
    print(f"  State after cancel: {vm.get_current_state().get_state_description()}")

    # ── Scenario 8: Dispense without selecting product ─────────────────────
    print("\n" + "-" * 50)
    print("Scenario 8: Dispense without selecting product (error)")
    print("-" * 50)
    vm.insert_money(20.0)
    try:
        vm.dispense_product_action()
    except InvalidStateException as e:
        print(f"  [Caught InvalidStateException] {e}")
    vm.cancel_transaction()

    # ── Transaction History ────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  TRANSACTION HISTORY")
    print("=" * 50)
    history = vm.get_transaction_history()
    if not history:
        print("  No completed transactions.")
    for i, txn in enumerate(history, 1):
        print(f"  [{i}] {txn.get_product().get_description()} "
              f"— Rack: {txn.get_rack().get_rack_code()} "
              f"— Amount: ₹{txn.get_total_amount()}")

    # ── Remaining inventory ────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  REMAINING INVENTORY")
    print("=" * 50)
    for code, rack in racks.items():
        print(f"  {code}: {rack.get_product().get_description()} — {rack.get_product_count()} left")

    print("\nDone.")


if __name__ == "__main__":
    main()
