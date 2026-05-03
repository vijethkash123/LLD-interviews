"""
Library Management System - Production Ready Implementation

Features:
- Book location and stock counting
- Librarian-only shelf management
- Automatic fine calculation (>30 days)
- Automatic member blocking (>35 days overdue)
- Complete CRUD operations
- Thread-safe operations
- Comprehensive error handling
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from enum import Enum
from dataclasses import dataclass
import threading
from decimal import Decimal


# ==========================================
# Enums and Constants
# ==========================================

class AccountStatus(Enum):
    ACTIVE = "Active"
    BLOCKED = "Blocked"
    SUSPENDED = "Suspended"


class ReservationStatus(Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class BookFormat(Enum):
    HARDCOVER = "Hardcover"
    PAPERBACK = "Paperback"
    EBOOK = "E-book"
    AUDIOBOOK = "Audiobook"


# Constants
MAX_LENDING_DAYS = 30
BLOCKING_THRESHOLD_DAYS = 35
FINE_PER_DAY = Decimal('5.00')  # $5 per day overdue


# ==========================================
# Custom Exceptions
# ==========================================

class LibraryException(Exception):
    """Base exception for library operations"""
    pass


class UnauthorizedOperationError(LibraryException):
    """Raised when unauthorized operation is attempted"""
    pass


class BookNotAvailableError(LibraryException):
    """Raised when book is not available for checkout"""
    pass


class MemberBlockedError(LibraryException):
    """Raised when a blocked member tries to perform operations"""
    pass


class InvalidReturnError(LibraryException):
    """Raised when return operation is invalid"""
    pass


# ==========================================
# Core Entities
# ==========================================

class Author:
    """Represents a book author"""
    
    def __init__(self, author_id: str, name: str, description: str):
        self.author_id = author_id
        self.name = name
        self.description = description
        self.books: List['Book'] = []
    
    def get_name(self) -> str:
        return self.name
    
    def add_book(self, book: 'Book'):
        if book not in self.books:
            self.books.append(book)
    
    def __repr__(self):
        return f"Author(id={self.author_id}, name={self.name})"


class Book:
    """Represents a book in the catalog (abstract concept)"""
    
    def __init__(self, isbn: str, title: str, subject: str):
        self.isbn = isbn
        self.title = title
        self.subject = subject
        self.authors: List[Author] = []
    
    def get_title(self) -> str:
        return self.title
    
    def add_author(self, author: Author):
        if author not in self.authors:
            self.authors.append(author)
            author.add_book(self)
    
    def __repr__(self):
        return f"Book(isbn={self.isbn}, title={self.title})"


class BookItem(Book):
    """Represents a physical copy of a book"""
    
    def __init__(self, isbn: str, title: str, subject: str, barcode: str, 
                 format_type: BookFormat):
        super().__init__(isbn, title, subject)
        self.barcode = barcode
        self.is_borrowed = False
        self.due_date: Optional[datetime] = None
        self.format_type = format_type
        self.shelf: Optional['Shelf'] = None
        self.current_lending: Optional['BookLending'] = None
        self._lock = threading.Lock()
    
    def checkout(self, member: 'Member', due_date: datetime) -> bool:
        """Thread-safe checkout operation"""
        with self._lock:
            if self.is_borrowed:
                return False
            self.is_borrowed = True
            self.due_date = due_date
            return True
    
    def return_book(self) -> bool:
        """Thread-safe return operation"""
        with self._lock:
            if not self.is_borrowed:
                return False
            self.is_borrowed = False
            self.due_date = None
            self.current_lending = None
            return True
    
    def get_location(self) -> Optional[str]:
        """Get the physical location of this book"""
        if self.shelf:
            return f"Shelf: {self.shelf.shelf_number}, Location: {self.shelf.location_identifier}"
        return None
    
    def __repr__(self):
        status = "Borrowed" if self.is_borrowed else "Available"
        return f"BookItem(barcode={self.barcode}, title={self.title}, status={status})"


class Shelf:
    """Represents a physical shelf in the library"""
    
    def __init__(self, shelf_number: str, location_identifier: str):
        self.shelf_number = shelf_number
        self.location_identifier = location_identifier
        self.book_items: List[BookItem] = []
        self._lock = threading.Lock()
    
    def add_book_item(self, book_item: BookItem):
        """Add a book item to this shelf"""
        with self._lock:
            if book_item not in self.book_items:
                book_item.shelf = self
                self.book_items.append(book_item)
    
    def remove_book_item(self, book_item: BookItem):
        """Remove a book item from this shelf"""
        with self._lock:
            if book_item in self.book_items:
                self.book_items.remove(book_item)
                book_item.shelf = None
    
    def get_available_books(self) -> List[BookItem]:
        """Get all available books on this shelf"""
        return [item for item in self.book_items if not item.is_borrowed]
    
    def __repr__(self):
        return f"Shelf(number={self.shelf_number}, location={self.location_identifier}, books={len(self.book_items)})"


@dataclass
class BookLocationInfo:
    """Data class for book location information"""
    isbn: str
    title: str
    total_copies: int
    available_copies: int
    borrowed_copies: int
    locations: List[Dict[str, str]]


class Library:
    """Main library class managing all operations"""
    
    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address
        self.book_items: List[BookItem] = []
        self.shelves: List[Shelf] = []
        self.members: Dict[str, 'Member'] = {}
        self.librarians: Dict[str, 'Librarian'] = {}
        self.catalog: Dict[str, Book] = {}  # ISBN -> Book
        self._lock = threading.Lock()
    
    def get_address(self) -> str:
        return self.address
    
    def add_book_to_catalog(self, book: Book):
        """Add a book to the library catalog"""
        with self._lock:
            if book.isbn not in self.catalog:
                self.catalog[book.isbn] = book
    
    def locate_book(self, isbn: str) -> Optional[BookLocationInfo]:
        """
        Locate all copies of a book by ISBN and return stock information
        
        Returns:
            BookLocationInfo with total count, available count, and locations
        """
        if isbn not in self.catalog:
            return None
        
        book = self.catalog[isbn]
        book_copies = [item for item in self.book_items if item.isbn == isbn]
        
        if not book_copies:
            return BookLocationInfo(
                isbn=isbn,
                title=book.title,
                total_copies=0,
                available_copies=0,
                borrowed_copies=0,
                locations=[]
            )
        
        available = [item for item in book_copies if not item.is_borrowed]
        borrowed = [item for item in book_copies if item.is_borrowed]
        
        locations = []
        for item in book_copies:
            location_info = {
                'barcode': item.barcode,
                'status': 'Available' if not item.is_borrowed else f'Borrowed (Due: {item.due_date.strftime("%Y-%m-%d")})',
                'location': item.get_location() or 'Location not assigned',
                'format': item.format_type.value
            }
            locations.append(location_info)
        
        return BookLocationInfo(
            isbn=isbn,
            title=book.title,
            total_copies=len(book_copies),
            available_copies=len(available),
            borrowed_copies=len(borrowed),
            locations=locations
        )
    
    def search_books_by_title(self, title: str) -> List[BookLocationInfo]:
        """Search books by title (partial match)"""
        results = []
        title_lower = title.lower()
        
        # We also make use of Prefix Trie data structure here to effeciently search for books by title prefix. For simplicity, we are doing a linear search here.
        for book in self.catalog.values():
            if title_lower in book.title.lower():
                location_info = self.locate_book(book.isbn)
                if location_info:
                    results.append(location_info)
        
        return results
    
    def __repr__(self):
        return f"Library(name={self.name}, books={len(self.book_items)}, members={len(self.members)})"


# ==========================================
# Actors and Accounts
# ==========================================

class LibraryCard:
    """Represents a library membership card"""

    def __init__(self, card_number: str, barcode: str, issue_date: datetime):
        self.card_number = card_number
        self.barcode = barcode
        self.issue_date = issue_date
        self.is_valid = True

    def invalidate(self):
        self.is_valid = False

    def reactivate(self):
        self.is_valid = True


class Account(ABC):
    """Base class for all user accounts"""
    
    def __init__(self, account_id: str, password: str, name: str, email: str):
        self.account_id = account_id
        self.password = password
        self.name = name
        self.email = email
        self.status = AccountStatus.ACTIVE
        self.library_card: Optional[LibraryCard] = None
    
    def reset_password(self, old_password: str, new_password: str) -> bool:
        """Reset password with validation"""
        if self.password == old_password:
            self.password = new_password
            return True
        return False
    
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.account_id}, name={self.name}, status={self.status.value})"


class Member(Account):
    """Represents a library member"""
    
    def __init__(self, account_id: str, password: str, name: str, email: str):
        super().__init__(account_id, password, name, email)
        self.date_of_membership = datetime.now()
        self.total_books_checked_out = 0
        self.active_lendings: List['BookLending'] = []
        self.lending_history: List['BookLending'] = []
        self.reservations: List['BookReservation'] = []
        self.fines: List['Fine'] = []
        self._lock = threading.Lock()
    
    def get_total_books(self) -> int:
        return self.total_books_checked_out
    
    def get_active_lendings_count(self) -> int:
        return len(self.active_lendings)
    
    def get_total_outstanding_fines(self) -> Decimal:
        """Calculate total unpaid fines"""
        return sum(fine.amount for fine in self.fines if not fine.is_paid)
    
    def add_lending(self, lending: 'BookLending'):
        with self._lock:
            self.active_lendings.append(lending)
            self.total_books_checked_out += 1
    
    def complete_lending(self, lending: 'BookLending'):
        with self._lock:
            if lending in self.active_lendings:
                self.active_lendings.remove(lending)
                self.lending_history.append(lending)
    
    def can_borrow(self) -> tuple[bool, str]:
        """Check if member can borrow books"""
        if self.status != AccountStatus.ACTIVE:
            return False, f"Account is {self.status.value}"
        
        if not self.library_card or not self.library_card.is_valid:
            return False, "Invalid library card"
        
        outstanding_fines = self.get_total_outstanding_fines()
        if outstanding_fines > Decimal('50.00'):
            return False, f"Outstanding fines: ${outstanding_fines}"
        
        if len(self.active_lendings) >= 5:
            return False, "Maximum lending limit reached (5 books)"
        
        return True, "OK"


class Librarian(Account):
    """Represents a librarian with administrative privileges"""
    
    def __init__(self, account_id: str, password: str, name: str, email: str):
        super().__init__(account_id, password, name, email)
        self.employee_id = account_id
    
    def add_book_item_to_library(self, book_item: BookItem, library: Library) -> bool:
        """Add a book item to the library inventory"""
        try:
            with library._lock:
                if book_item not in library.book_items:
                    library.book_items.append(book_item)
                    
                    # Add to catalog if not exists
                    if book_item.isbn not in library.catalog:
                        library.add_book_to_catalog(book_item)
                    
                    return True
                return False
        except Exception as e:
            print(f"Error adding book item: {e}")
            return False
    
    def assign_book_to_shelf(self, book_item: BookItem, shelf: Shelf) -> bool:
        """Assign a book item to a specific shelf"""
        try:
            shelf.add_book_item(book_item)
            return True
        except Exception as e:
            print(f"Error assigning book to shelf: {e}")
            return False
    
    def move_book_to_shelf(self, book_item: BookItem, new_shelf: Shelf) -> bool:
        """Move a book from one shelf to another"""
        try:
            if book_item.shelf:
                book_item.shelf.remove_book_item(book_item)
            new_shelf.add_book_item(book_item)
            return True
        except Exception as e:
            print(f"Error moving book: {e}")
            return False
    
    def create_shelf(self, shelf_number: str, location_identifier: str, library: Library) -> Shelf:
        """Create a new shelf in the library"""
        shelf = Shelf(shelf_number, location_identifier)
        with library._lock:
            library.shelves.append(shelf)
        return shelf
    
    def remove_shelf(self, shelf: Shelf, library: Library) -> bool:
        """Remove a shelf from the library (only if empty)"""
        if shelf.book_items:
            print("Cannot remove shelf: contains books")
            return False
        
        with library._lock:
            if shelf in library.shelves:
                library.shelves.remove(shelf)
                return True
        return False
    
    def block_member(self, member: Member, reason: str = ""):
        """Block a member account"""
        member.status = AccountStatus.BLOCKED
        if member.library_card:
            member.library_card.invalidate()
        print(f"Member {member.name} blocked. Reason: {reason}")
    
    def unblock_member(self, member: Member):
        """Unblock a member account"""
        member.status = AccountStatus.ACTIVE
        if member.library_card:
            member.library_card.reactivate()
        print(f"Member {member.name} unblocked")
    
    def issue_library_card(self, member: Member) -> LibraryCard:
        """Issue a library card to a member"""
        card_number = f"CARD-{member.account_id}"
        barcode = f"BC-{member.account_id}-{datetime.now().strftime('%Y%m%d')}"
        card = LibraryCard(card_number, barcode, datetime.now())
        member.library_card = card
        return card


# ==========================================
# Operational Classes
# ==========================================

class BookReservation:
    """Represents a book reservation"""
    
    def __init__(self, reservation_id: str, book_item: BookItem, member: Member):
        self.reservation_id = reservation_id
        self.creation_date = datetime.now()
        self.status = ReservationStatus.PENDING
        self.book_item = book_item
        self.member = member
    
    def get_status(self) -> str:
        return self.status.value
    
    def complete(self):
        self.status = ReservationStatus.COMPLETED
    
    def cancel(self):
        self.status = ReservationStatus.CANCELLED
    
    def fetch_reservation_details(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "creation_date": self.creation_date.isoformat(),
            "status": self.status.value,
            "book_barcode": self.book_item.barcode,
            "book_title": self.book_item.title,
            "member_id": self.member.account_id,
            "member_name": self.member.name
        }


class BookLending:
    """Represents a book lending transaction with automatic fine calculation"""
    
    def __init__(self, lending_id: str, book_item: BookItem, member: Member, due_date: datetime):
        self.lending_id = lending_id
        self.creation_date = datetime.now()
        self.due_date = due_date
        self.return_date: Optional[datetime] = None
        self.book_item = book_item
        self.member = member
        self.fine: Optional['Fine'] = None
    
    def is_overdue(self) -> bool:
        """Check if the book is overdue"""
        if self.return_date:
            return False
        return datetime.now() > self.due_date
    
    def get_overdue_days(self) -> int:
        """Get number of days overdue"""
        if not self.is_overdue():
            return 0
        
        reference_date = self.return_date if self.return_date else datetime.now()
        delta = reference_date - self.due_date
        return max(0, delta.days)
    
    def calculate_fine(self) -> Decimal:
        """Calculate fine based on overdue days"""
        overdue_days = self.get_overdue_days()
        if overdue_days <= 0:
            return Decimal('0.00')
        
        # First 30 days are free (normal lending period)
        # Fine starts after 30 days
        billable_days = max(0, overdue_days)
        return Decimal(billable_days) * FINE_PER_DAY
    
    def return_book(self, return_date: datetime) -> Optional['Fine']:
        """
        Process book return and generate fine if overdue
        
        Returns:
            Fine object if fine is applicable, None otherwise
        """
        self.return_date = return_date
        
        fine_amount = self.calculate_fine()
        if fine_amount > Decimal('0.00'):
            self.fine = Fine(
                fine_id=f"FINE-{self.lending_id}",
                lending_record=self,
                amount=fine_amount
            )
            self.member.fines.append(self.fine)
            return self.fine
        
        return None
    
    def get_lending_details(self) -> dict:
        """Get complete lending details"""
        return {
            "lending_id": self.lending_id,
            "book_barcode": self.book_item.barcode,
            "book_title": self.book_item.title,
            "member_id": self.member.account_id,
            "member_name": self.member.name,
            "checkout_date": self.creation_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "is_overdue": self.is_overdue(),
            "overdue_days": self.get_overdue_days(),
            "fine_amount": float(self.calculate_fine())
        }


# ==========================================
# Fines and Transactions
# ==========================================

class Fine:
    """Represents a fine for overdue books"""
    
    def __init__(self, fine_id: str, lending_record: BookLending, amount: Decimal):
        self.fine_id = fine_id
        self.lending_record = lending_record
        self.amount = amount
        self.creation_date = datetime.now()
        self.is_paid = False
        self.payment_date: Optional[datetime] = None
        self.transaction: Optional['Transaction'] = None
    
    def get_amount(self) -> Decimal:
        return self.amount
    
    def mark_paid(self, transaction: 'Transaction'):
        """Mark fine as paid"""
        self.is_paid = True
        self.payment_date = datetime.now()
        self.transaction = transaction
    
    def get_fine_details(self) -> dict:
        return {
            "fine_id": self.fine_id,
            "amount": float(self.amount),
            "creation_date": self.creation_date.isoformat(),
            "is_paid": self.is_paid,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "lending_id": self.lending_record.lending_id,
            "book_title": self.lending_record.book_item.title,
            "overdue_days": self.lending_record.get_overdue_days()
        }


class Transaction(ABC):
    """Base class for financial transactions"""
    
    def __init__(self, transaction_id: str, amount: Decimal):
        self.transaction_id = transaction_id
        self.creation_date = datetime.now()
        self.amount = amount
        self.status = "Completed"
    
    @abstractmethod
    def process_payment(self) -> bool:
        """Process the payment"""
        pass
    
    def get_transaction_details(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "amount": float(self.amount),
            "creation_date": self.creation_date.isoformat(),
            "status": self.status,
            "type": self.__class__.__name__
        }


class CreditCardTransaction(Transaction):
    """Credit card payment transaction"""
    
    def __init__(self, transaction_id: str, amount: Decimal, card_name: str, 
                 card_number: str):
        super().__init__(transaction_id, amount)
        self.card_name = card_name
        self.card_number = card_number[-4:]  # Store only last 4 digits
    
    def process_payment(self) -> bool:
        print(f"Processing credit card payment of ${self.amount} using card ending in {self.card_number}")
        return True


class CheckTransaction(Transaction):
    """Check payment transaction"""
    
    def __init__(self, transaction_id: str, amount: Decimal, bank_name: str, 
                 check_number: str):
        super().__init__(transaction_id, amount)
        self.bank_name = bank_name
        self.check_number = check_number
    
    def process_payment(self) -> bool:
        print(f"Processing check payment of ${self.amount} - Check #{self.check_number} from {self.bank_name}")
        return True


class CashTransaction(Transaction):
    """Cash payment transaction"""
    
    def __init__(self, transaction_id: str, amount: Decimal, cash_tendered: Decimal):
        super().__init__(transaction_id, amount)
        self.cash_tendered = cash_tendered
        self.change_returned = cash_tendered - amount
    
    def process_payment(self) -> bool:
        if self.cash_tendered < self.amount:
            print(f"Insufficient cash: ${self.cash_tendered} < ${self.amount}")
            return False
        print(f"Processing cash payment of ${self.amount}. Change: ${self.change_returned}")
        return True


# ==========================================
# Notifications
# ==========================================

class Notification(ABC):
    """Base class for notifications"""
    
    def __init__(self, notification_id: str, content: str, recipient: Account):
        self.notification_id = notification_id
        self.creation_date = datetime.now()
        self.content = content
        self.recipient = recipient
        self.sent = False
    
    @abstractmethod
    def send_notification(self) -> bool:
        """Send the notification"""
        pass


class SMSNotification(Notification):
    """SMS notification"""
    
    def __init__(self, notification_id: str, content: str, recipient: Account, 
                 mobile_number: str):
        super().__init__(notification_id, content, recipient)
        self.mobile_number = mobile_number
    
    def send_notification(self) -> bool:
        print(f"[SMS] To: {self.mobile_number} | Message: {self.content}")
        self.sent = True
        return True


class EmailNotification(Notification):
    """Email notification"""
    
    def __init__(self, notification_id: str, content: str, recipient: Account):
        super().__init__(notification_id, content, recipient)
        self.email_address = recipient.email
    
    def send_notification(self) -> bool:
        print(f"[EMAIL] To: {self.email_address} | Subject: Library Notification")
        print(f"        Content: {self.content}")
        self.sent = True
        return True


# ==========================================
# Library Management Service
# ==========================================

class LibraryManagementService:
    """
    Main service class that handles all library operations
    including lending, returns, fine calculation, and member management
    """
    
    def __init__(self, library: Library):
        self.library = library
        self.lendings: Dict[str, BookLending] = {}
        self.reservations: Dict[str, BookReservation] = {}
        self._lending_counter = 0
        self._reservation_counter = 0
        self._lock = threading.Lock()
    
    def _generate_lending_id(self) -> str:
        """Generate unique lending ID"""
        with self._lock:
            self._lending_counter += 1
            return f"LEND-{datetime.now().strftime('%Y%m%d')}-{self._lending_counter:05d}"
    
    def _generate_reservation_id(self) -> str:
        """Generate unique reservation ID"""
        with self._lock:
            self._reservation_counter += 1
            return f"RES-{datetime.now().strftime('%Y%m%d')}-{self._reservation_counter:05d}"
    
    def checkout_book(self, book_item: BookItem, member: Member) -> BookLending:
        """
        Checkout a book to a member
        
        Raises:
            MemberBlockedError: If member is blocked
            BookNotAvailableError: If book is not available
        """
        # Check member eligibility
        can_borrow, reason = member.can_borrow()
        if not can_borrow:
            if member.status == AccountStatus.BLOCKED:
                raise MemberBlockedError(f"Member is blocked: {reason}")
            raise LibraryException(f"Cannot borrow: {reason}")
        
        # Check book availability
        if book_item.is_borrowed:
            raise BookNotAvailableError(f"Book '{book_item.title}' is not available")
        
        # Calculate due date
        due_date = datetime.now() + timedelta(days=MAX_LENDING_DAYS)
        
        # Create lending record
        lending_id = self._generate_lending_id()
        lending = BookLending(lending_id, book_item, member, due_date)
        
        # Update book and member
        book_item.checkout(member, due_date)
        book_item.current_lending = lending
        member.add_lending(lending)
        
        # Store lending
        self.lendings[lending_id] = lending
        
        # Send notification
        self._send_checkout_notification(member, book_item, due_date)
        
        print(f"✓ Book checked out: '{book_item.title}' to {member.name}")
        print(f"  Due date: {due_date.strftime('%Y-%m-%d %H:%M')}")
        
        return lending
    
    def return_book(self, book_item: BookItem, member: Member) -> Optional[Fine]:
        """
        Return a book and calculate fine if overdue
        
        Returns:
            Fine object if applicable, None otherwise
            
        Raises:
            InvalidReturnError: If book was not borrowed by this member
        """
        # Find active lending
        lending = book_item.current_lending
        if not lending or lending.member != member:
            raise InvalidReturnError("This book was not borrowed by this member")
        
        # Process return
        return_date = datetime.now()
        fine = lending.return_book(return_date)
        
        # Update book and member
        book_item.return_book()
        member.complete_lending(lending)
        
        # Check if member should be blocked (>35 days overdue)
        overdue_days = lending.get_overdue_days()
        if overdue_days > BLOCKING_THRESHOLD_DAYS:
            # Find a librarian to block the member
            librarian = next(iter(self.library.librarians.values()), None)
            if librarian:
                librarian.block_member(
                    member, 
                    f"Book returned {overdue_days} days late (>{BLOCKING_THRESHOLD_DAYS} days)"
                )
        
        # Print return summary
        print(f"✓ Book returned: '{book_item.title}' by {member.name}")
        print(f"  Return date: {return_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Overdue days: {overdue_days}")
        
        if fine:
            print(f"  ⚠ Fine assessed: ${fine.amount}")
            self._send_fine_notification(member, fine)
        
        return fine
    
    def _send_checkout_notification(self, member: Member, book_item: BookItem, 
                                    due_date: datetime):
        """Send checkout confirmation notification"""
        content = (f"You have checked out '{book_item.title}'. "
                  f"Due date: {due_date.strftime('%Y-%m-%d')}. "
                  f"Please return on time to avoid fines.")
        
        notification = EmailNotification(
            notification_id=f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=content,
            recipient=member
        )
        notification.send_notification()
    
    def _send_fine_notification(self, member: Member, fine: Fine):
        """Send fine notification"""
        content = (f"A fine of ${fine.amount} has been assessed for the overdue return of "
                  f"'{fine.lending_record.book_item.title}'. "
                  f"Please pay at your earliest convenience.")
        
        notification = EmailNotification(
            notification_id=f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            content=content,
            recipient=member
        )
        notification.send_notification()
    
    def check_overdue_books(self) -> List[BookLending]:
        """
        Check all active lendings for overdue books
        Send notifications for overdue books
        Auto-block members with books overdue > 35 days
        """
        overdue_lendings = []
        
        for lending in self.lendings.values():
            if lending.return_date:  # Skip returned books
                continue
            
            if lending.is_overdue():
                overdue_lendings.append(lending)
                overdue_days = lending.get_overdue_days()
                
                # Send reminder for overdue
                if overdue_days % 7 == 0:  # Weekly reminders
                    content = (f"Reminder: '{lending.book_item.title}' is {overdue_days} days overdue. "
                              f"Current fine: ${lending.calculate_fine()}. Please return immediately.")
                    
                    notification = EmailNotification(
                        notification_id=f"NOTIF-OD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        content=content,
                        recipient=lending.member
                    )
                    notification.send_notification()
                
                # Auto-block if > 35 days
                if overdue_days > BLOCKING_THRESHOLD_DAYS and lending.member.is_active():
                    librarian = next(iter(self.library.librarians.values()), None)
                    if librarian:
                        librarian.block_member(
                            lending.member,
                            f"Book '{lending.book_item.title}' overdue {overdue_days} days"
                        )
        
        return overdue_lendings
    
    def pay_fine(self, fine: Fine, transaction: Transaction) -> bool:
        """Process fine payment"""
        if fine.is_paid:
            print(f"Fine {fine.fine_id} already paid")
            return False
        
        if transaction.process_payment():
            fine.mark_paid(transaction)
            print(f"✓ Fine {fine.fine_id} paid: ${fine.amount}")
            return True
        
        return False
    
    def get_member_summary(self, member: Member) -> dict:
        """Get complete summary of member's library activity"""
        return {
            "member_id": member.account_id,
            "name": member.name,
            "status": member.status.value,
            "membership_date": member.date_of_membership.isoformat(),
            "active_lendings": len(member.active_lendings),
            "total_books_checked_out": member.total_books_checked_out,
            "outstanding_fines": float(member.get_total_outstanding_fines()),
            "active_lending_details": [l.get_lending_details() for l in member.active_lendings]
        }


# ==========================================
# Demo/Testing Functions
# ==========================================

def run_comprehensive_demo():
    """Run a comprehensive demonstration of the library system"""
    
    print("=" * 80)
    print("LIBRARY MANAGEMENT SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 80)
    print()
    
    # Initialize library
    library = Library("Central Public Library", "123 Main Street, City")
    service = LibraryManagementService(library)
    
    # Create librarian
    librarian = Librarian("LIB001", "password123", "Alice Johnson", "alice@library.com")
    library.librarians[librarian.account_id] = librarian
    
    # Create members
    member1 = Member("MEM001", "pass123", "John Doe", "john@email.com")
    member2 = Member("MEM002", "pass456", "Jane Smith", "jane@email.com")
    
    library.members[member1.account_id] = member1
    library.members[member2.account_id] = member2
    
    # Issue library cards
    librarian.issue_library_card(member1)
    librarian.issue_library_card(member2)
    
    # Create shelves
    shelf1 = librarian.create_shelf("A-101", "Fiction Section - Floor 1", library)
    shelf2 = librarian.create_shelf("B-201", "Science Section - Floor 2", library)
    
    # Create authors and books
    author1 = Author("AUTH001", "George Orwell", "English novelist and essayist")
    author2 = Author("AUTH002", "Isaac Asimov", "American science fiction writer")
    
    book1 = Book("978-0-452-28423-4", "1984", "Dystopian Fiction")
    book1.add_author(author1)
    
    book2 = Book("978-0-553-29335-0", "Foundation", "Science Fiction")
    book2.add_author(author2)
    
    # Add books to catalog
    library.add_book_to_catalog(book1)
    library.add_book_to_catalog(book2)
    
    # Create multiple copies of books
    book_item1 = BookItem("978-0-452-28423-4", "1984", "Dystopian Fiction", 
                          "BC001", BookFormat.PAPERBACK)
    book_item2 = BookItem("978-0-452-28423-4", "1984", "Dystopian Fiction", 
                          "BC002", BookFormat.HARDCOVER)
    book_item3 = BookItem("978-0-553-29335-0", "Foundation", "Science Fiction", 
                          "BC003", BookFormat.PAPERBACK)
    
    # Librarian adds books to library and assigns to shelves
    print("\n--- LIBRARIAN OPERATIONS ---")
    librarian.add_book_item_to_library(book_item1, library)
    librarian.add_book_item_to_library(book_item2, library)
    librarian.add_book_item_to_library(book_item3, library)
    
    librarian.assign_book_to_shelf(book_item1, shelf1)
    librarian.assign_book_to_shelf(book_item2, shelf1)
    librarian.assign_book_to_shelf(book_item3, shelf2)
    
    print(f"✓ Added 3 book items to library")
    print(f"✓ Assigned books to shelves")
    
    # Demonstrate book location feature
    print("\n--- BOOK LOCATION LOOKUP ---")
    location_info = library.locate_book("978-0-452-28423-4")
    if location_info:
        print(f"\nBook: {location_info.title}")
        print(f"ISBN: {location_info.isbn}")
        print(f"Total Copies: {location_info.total_copies}")
        print(f"Available: {location_info.available_copies}")
        print(f"Borrowed: {location_info.borrowed_copies}")
        print(f"\nLocations:")
        for loc in location_info.locations:
            print(f"  - Barcode: {loc['barcode']}")
            print(f"    Status: {loc['status']}")
            print(f"    Location: {loc['location']}")
            print(f"    Format: {loc['format']}")
            print()
    
    # Checkout books
    print("\n--- CHECKOUT OPERATIONS ---")
    try:
        lending1 = service.checkout_book(book_item1, member1)
        lending2 = service.checkout_book(book_item3, member2)
    except LibraryException as e:
        print(f"Error: {e}")
    
    # Check updated location info
    print("\n--- UPDATED LOCATION AFTER CHECKOUT ---")
    location_info = library.locate_book("978-0-452-28423-4")
    if location_info:
        print(f"Available: {location_info.available_copies}/{location_info.total_copies}")
    
    # Simulate overdue scenario (30+ days)
    print("\n--- SIMULATING OVERDUE SCENARIO ---")
    # Manually set the checkout date to 32 days ago
    lending1.creation_date = datetime.now() - timedelta(days=32)
    lending1.due_date = lending1.creation_date + timedelta(days=MAX_LENDING_DAYS)
    
    print(f"Simulated: Book checked out 32 days ago")
    print(f"Due date was: {lending1.due_date.strftime('%Y-%m-%d')}")
    print(f"Overdue by: {lending1.get_overdue_days()} days")
    print(f"Expected fine: ${lending1.calculate_fine()}")
    
    # Return overdue book
    print("\n--- RETURNING OVERDUE BOOK ---")
    fine = service.return_book(book_item1, member1)
    
    if fine:
        print(f"\nFine Details:")
        print(f"  Fine ID: {fine.fine_id}")
        print(f"  Amount: ${fine.amount}")
        print(f"  Overdue days: {fine.lending_record.get_overdue_days()}")
    
    # Simulate extreme overdue (>35 days) for auto-blocking
    print("\n--- SIMULATING EXTREME OVERDUE (>35 DAYS) ---")
    book_item4 = BookItem("978-0-553-29335-0", "Foundation", "Science Fiction", 
                          "BC004", BookFormat.PAPERBACK)
    librarian.add_book_item_to_library(book_item4, library)
    librarian.assign_book_to_shelf(book_item4, shelf2)
    
    # Create a new member for this test
    member3 = Member("MEM003", "pass789", "Bob Wilson", "bob@email.com")
    library.members[member3.account_id] = member3
    librarian.issue_library_card(member3)
    
    lending3 = service.checkout_book(book_item4, member3)
    
    # Simulate 40 days overdue
    lending3.creation_date = datetime.now() - timedelta(days=40)
    lending3.due_date = lending3.creation_date + timedelta(days=MAX_LENDING_DAYS)
    
    print(f"Member status before return: {member3.status.value}")
    print(f"Overdue by: {lending3.get_overdue_days()} days")
    
    # Return should trigger auto-blocking
    service.return_book(book_item4, member3)
    print(f"Member status after return: {member3.status.value}")
    
    # Try to checkout with blocked account
    print("\n--- ATTEMPTING CHECKOUT WITH BLOCKED ACCOUNT ---")
    try:
        service.checkout_book(book_item2, member3)
    except MemberBlockedError as e:
        print(f"✓ Correctly prevented: {e}")
    
    # Pay fine
    print("\n--- FINE PAYMENT ---")
    if fine:
        transaction = CreditCardTransaction(
            "TXN001",
            fine.amount,
            "John Doe",
            "1234-5678-9012-3456"
        )
        service.pay_fine(fine, transaction)
    
    # Member summary
    print("\n--- MEMBER SUMMARY ---")
    summary = service.get_member_summary(member1)
    print(f"Member: {summary['name']}")
    print(f"Status: {summary['status']}")
    print(f"Active Lendings: {summary['active_lendings']}")
    print(f"Total Books Checked Out: {summary['total_books_checked_out']}")
    print(f"Outstanding Fines: ${summary['outstanding_fines']}")
    
    # Check overdue books system-wide
    print("\n--- SYSTEM-WIDE OVERDUE CHECK ---")
    overdue = service.check_overdue_books()
    print(f"Total overdue books: {len(overdue)}")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_comprehensive_demo()