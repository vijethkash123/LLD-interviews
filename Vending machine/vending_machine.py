from typing import Dict, List, Optional

from models import Product, Rack, Transaction
from inventory_manager import InventoryManager
from payment_processor import PaymentProcessor
from states import VendingMachineState, NoMoneyInsertedState


class VendingMachine:
    """
    Central component of the system. Acts as a Facade, coordinating all
    operations. Also serves as the Context object for the State pattern.
    """

    def __init__(self):
        self._inventory_manager: InventoryManager = InventoryManager()
        self._payment_processor: PaymentProcessor = PaymentProcessor()
        self._current_transaction: Optional[Transaction] = None
        self._transaction_history: List[Transaction] = []
        self._current_state: VendingMachineState = NoMoneyInsertedState()
        self._selected_product: Optional[str] = None

    # ── State delegation ──────────────────────────────────────────────────

    def insert_money(self, amount: float) -> None:
        self._current_state.insert_money(self, amount)

    def select_product_by_code(self, product_code: str) -> None:
        self._current_state.select_product_by_code(self, product_code)

    def choose_product(self, rack_id: str) -> None:
        self.select_product_by_code(rack_id)

    def dispense_product_action(self) -> None:
        self._current_state.dispense_product(self)

    # ── Admin operations ──────────────────────────────────────────────────

    def set_rack(self, racks: Dict[str, Rack]) -> None:
        self._inventory_manager.update_rack(racks)

    def set_product(self, product: Product, rack_code: str) -> None:
        existing = self._inventory_manager.get_rack(rack_code)
        if existing:
            new_count = existing.get_product_count() + 1
            existing._set_count(new_count)
        else:
            new_rack = Rack(rack_code, product, 1)
            self._inventory_manager._racks[rack_code] = new_rack

    def cancel_transaction(self) -> InventoryManager:
        print("  [VendingMachine] Transaction cancelled. Returning money...")
        change = self._payment_processor.return_change()
        print(f"  [VendingMachine] Returned: {change}")
        self._current_transaction = None
        self._selected_product = None
        self._current_state = NoMoneyInsertedState()
        return self._inventory_manager

    def get_transaction_history(self) -> List[Transaction]:
        return list(self._transaction_history)

    # ── Getters / setters (used by State objects) ─────────────────────────

    def get_inventory_manager(self) -> InventoryManager:
        return self._inventory_manager

    def get_payment_processor(self) -> PaymentProcessor:
        return self._payment_processor

    def get_current_state(self) -> VendingMachineState:
        return self._current_state

    def set_state(self, state: VendingMachineState) -> None:
        self._current_state = state

    def get_selected_product(self) -> Optional[str]:
        return self._selected_product

    def set_selected_product(self, product_code: Optional[str]) -> None:
        self._selected_product = product_code

    def __repr__(self) -> str:
        return (f"VendingMachine(state={self._current_state.get_state_description()!r}, "
                f"balance={self._payment_processor.get_current_balance()})")
