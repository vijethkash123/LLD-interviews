from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING

from exceptions import InvalidStateException, InvalidTransactionException
from models import Transaction

if TYPE_CHECKING:
    from vending_machine import VendingMachine


class VendingMachineState(ABC):
    """
    Interface (abstract base) for all vending machine states.
    Each state defines behaviour for: inserting money, selecting a product,
    and dispensing the product.
    """

    @abstractmethod
    def insert_money(self, vm: "VendingMachine", amount: float) -> None:
        pass

    @abstractmethod
    def select_product_by_code(self, vm: "VendingMachine", product_code: str) -> None:
        pass

    @abstractmethod
    def dispense_product(self, vm: "VendingMachine") -> None:
        pass

    @abstractmethod
    def get_state_description(self) -> str:
        pass


class NoMoneyInsertedState(VendingMachineState):
    """
    Initial state. No money has been inserted yet.
    """

    def insert_money(self, vm: "VendingMachine", amount: float) -> None:
        print(f"  [State] Money inserted: {amount}")
        vm.get_payment_processor().add_balance(Decimal(str(amount)))
        vm.set_state(MoneyInsertedState())

    def select_product_by_code(self, vm: "VendingMachine", product_code: str) -> None:
        raise InvalidStateException(
            "Cannot select a product without money. Please insert money to proceed."
        )

    def dispense_product(self, vm: "VendingMachine") -> None:
        raise InvalidStateException(
            "Cannot dispense product without money. Please insert money to proceed."
        )

    def get_state_description(self) -> str:
        return "No Money Inserted State — Insert money to proceed."


class MoneyInsertedState(VendingMachineState):
    """
    State after money has been inserted.
    Allows adding more money or selecting a product.
    """

    def insert_money(self, vm: "VendingMachine", amount: float) -> None:
        print(f"  [State] Additional money inserted: {amount}")
        vm.get_payment_processor().add_balance(Decimal(str(amount)))

    def select_product_by_code(self, vm: "VendingMachine", product_code: str) -> None:
        print(f"  [State] Product selected: {product_code}")
        vm.set_selected_product(product_code)
        vm.set_state(DispenseState())

    def dispense_product(self, vm: "VendingMachine") -> None:
        raise InvalidStateException(
            "Please select a product before dispensing."
        )

    def get_state_description(self) -> str:
        return "Money Inserted State — Select a product."


class DispenseState(VendingMachineState):
    """
    State where the vending machine is ready to dispense the selected product.
    Validates payment and inventory before dispensing.
    """

    def insert_money(self, vm: "VendingMachine", amount: float) -> None:
        raise InvalidStateException(
            "Cannot insert money. Dispensing is already in progress."
        )

    def select_product_by_code(self, vm: "VendingMachine", product_code: str) -> None:
        raise InvalidStateException(
            "Cannot select another product. Dispensing is already in progress."
        )

    def dispense_product(self, vm: "VendingMachine") -> None:
        rack_id = vm.get_selected_product()
        if rack_id is None:
            raise InvalidTransactionException("Invalid product selection.")

        rack = vm.get_inventory_manager().get_rack(rack_id)
        if rack is None:
            raise InvalidTransactionException(f"Rack '{rack_id}' not found.")

        product = rack.get_product()
        balance = vm.get_payment_processor().get_current_balance()

        if rack.get_product_count() <= 0:
            raise InvalidTransactionException("Insufficient inventory for the selected product.")

        if balance < product.get_unit_price():
            raise InvalidTransactionException("Insufficient funds.")

        # Charge the customer
        vm.get_payment_processor().charge(product.get_unit_price())

        # Build and store the transaction
        transaction = Transaction(rack, product, product.get_unit_price())
        vm._transaction_history.append(transaction)
        vm._current_transaction = transaction

        # Dispense and update inventory
        vm.get_inventory_manager().dispense_product_from_rack(rack_id)

        # Return any change
        change = vm.get_payment_processor().return_change()
        print(f"  [State] Dispensing: {product.get_description()} — "
              f"Price: {product.get_unit_price()}, Change: {change}")

        # Reset state
        vm.set_selected_product(None)
        vm.set_state(NoMoneyInsertedState())

    def get_state_description(self) -> str:
        return "Dispense State — Dispensing product..."
