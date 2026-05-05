from typing import Dict, Optional

from exceptions import InvalidTransactionException
from models import Product, Rack


class InventoryManager:
    """
    Handles tracking and storage of products in the vending machine.
    Uses the Composite design pattern (InventoryManager -> Rack -> Product).
    """

    def __init__(self):
        self._racks: Dict[str, Rack] = {}

    def update_rack(self, racks: Dict[str, Rack]) -> None:
        """Replace the entire rack configuration."""
        self._racks = racks

    def get_product_from_rack(self, rack_code: str) -> Product:
        """Retrieve the product from the specified rack."""
        rack = self._racks.get(rack_code)
        if rack is None:
            raise InvalidTransactionException(f"Cannot dispense product. Rack '{rack_code}' not found.")
        return rack.get_product()

    def get_product_in_rack(self, rack_id: str) -> Product:
        return self.get_product_from_rack(rack_id)

    def dispense_product_from_rack(self, rack_code: str) -> None:
        """Dispense (decrement) one unit from the specified rack."""
        rack = self._racks.get(rack_code)
        if rack is None:
            raise InvalidTransactionException(f"Cannot dispense product. Rack '{rack_code}' not found.")
        if rack.get_product_count() <= 0:
            raise InvalidTransactionException(
                f"Cannot dispense product. Rack '{rack_code}' is empty."
            )
        rack._set_count(rack.get_product_count() - 1)

    def dispense_product(self, rack_id: str) -> None:
        self.dispense_product_from_rack(rack_id)

    def get_rack(self, rack_code: str) -> Optional[Rack]:
        return self._racks.get(rack_code)

    def __repr__(self) -> str:
        return f"InventoryManager(racks={list(self._racks.keys())})"
