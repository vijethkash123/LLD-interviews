from decimal import Decimal


class Product:
    """Represents a basic unit of a product in the vending machine."""

    def __init__(self, product_code: str, description: str, unit_price: Decimal):
        self._product_code: str = product_code
        self._description: str = description
        self._unit_price: Decimal = unit_price

    def get_product_code(self) -> str:
        return self._product_code

    def get_description(self) -> str:
        return self._description

    def get_unit_price(self) -> Decimal:
        return self._unit_price

    def __repr__(self) -> str:
        return (f"Product(code={self._product_code!r}, "
                f"desc={self._description!r}, price={self._unit_price})")


class Rack:
    """
    Represents a designated slot in the vending machine that holds a single
    product type and can hold multiple units of that product.
    """

    def __init__(self, rack_code: str, product: Product, count: int = 0):
        self._rack_code: str = rack_code
        self._product: Product = product
        self._count: int = count

    def get_rack_code(self) -> str:
        return self._rack_code

    def get_product(self) -> Product:
        return self._product

    def get_product_count(self) -> int:
        return self._count

    def _set_count(self, count: int) -> None:
        self._count = count

    def __repr__(self) -> str:
        return (f"Rack(code={self._rack_code!r}, "
                f"product={self._product.get_product_code()!r}, count={self._count})")


class Transaction:
    """
    Tracks key details such as the selected product, the rack it belongs to,
    and the total cost required for the purchase.
    """

    def __init__(self, rack: Rack, product: Product, total_amount: Decimal):
        self._rack: Rack = rack
        self._product: Product = product
        self._total_amount: Decimal = total_amount

    def get_rack(self) -> Rack:
        return self._rack

    def get_product(self) -> Product:
        return self._product

    def get_total_amount(self) -> Decimal:
        return self._total_amount

    def set_total_amount(self, amount: Decimal) -> None:
        self._total_amount = amount

    def __repr__(self) -> str:
        return (f"Transaction(product={self._product.get_product_code()!r}, "
                f"rack={self._rack.get_rack_code()!r}, amount={self._total_amount})")
