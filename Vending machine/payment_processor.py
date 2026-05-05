from decimal import Decimal


class PaymentProcessor:
    """
    Handles payment-related operations: adding funds, charging for purchases,
    and returning change. Uses Decimal for precision.
    """

    def __init__(self):
        self._current_balance: Decimal = Decimal("0.0")

    def get_current_balance(self) -> Decimal:
        return self._current_balance

    def add_balance(self, amount: Decimal) -> None:
        """Add the specified amount to the current balance."""
        self._current_balance = self._current_balance + amount

    def charge(self, amount: Decimal) -> None:
        """Deduct the specified amount from the current balance."""
        self._current_balance = self._current_balance - amount

    def return_change(self) -> Decimal:
        """Return the current balance as change and reset to zero."""
        change = self._current_balance
        self._current_balance = Decimal("0.0")
        return change

    def __repr__(self) -> str:
        return f"PaymentProcessor(balance={self._current_balance})"
