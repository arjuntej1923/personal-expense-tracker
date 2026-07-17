"""
Personal Expense Tracker (Console-Based Application) — v2
------------------------------------------------------------
A menu-driven CLI application to manage personal expenses.

Core Features (1-6):
    1. Add New Expense
    2. View All Expenses (tabular, sorted by date)
    3. Search Expense (by ID)
    4. Update Expense
    5. Delete Expense
    6. View Summary Metrics (grand total, category breakdown, highest/lowest/average)

Bonus Features (7-8):
    7. Search by Category
    8. Monthly Summary

    9. Exit & Save Data

Design:
    - Expense: data model class for a single transaction.
    - ExpenseTracker: manager class. Holds the in-memory collection and
      contains ONLY business logic (no input() calls) so it can be tested
      or reused independently of the CLI.
    - All user input/output (prompts, printing) lives in module-level
      "prompt_*" helper functions and in main(). This keeps the tracker
      class clean and unit-testable.
"""

import csv
import os
from datetime import datetime

DATA_FILE = "expenses.csv"
DATE_FORMAT = "%d-%m-%Y"

# Predefined category list — keeps stored data consistent.
CATEGORIES = ["Food", "Travel", "Rent", "Shopping", "Entertainment", "Medical", "Others"]

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# --------------------------------------------------------------------------
# MODEL CLASS
# --------------------------------------------------------------------------
class Expense:
    """Represents a single expense record."""

    def __init__(self, expense_id, title, amount, category, date):
        self.id = expense_id
        self.title = title
        self.amount = amount          # stored as float
        self.category = category
        self.date = date              # stored as string DD-MM-YYYY

    def to_row(self):
        """Convert this Expense into a list suitable for CSV writing."""
        return [self.id, self.title, f"{self.amount:.2f}", self.category, self.date]

    @staticmethod
    def from_row(row):
        """Build an Expense object back from a CSV row."""
        return Expense(
            expense_id=int(row[0]),
            title=row[1],
            amount=float(row[2]),
            category=row[3],
            date=row[4],
        )


# --------------------------------------------------------------------------
# MANAGER CLASS  (business logic only — no input() calls anywhere here)
# --------------------------------------------------------------------------
class ExpenseTracker:
    """Holds the in-memory collection of Expense objects and all CRUD logic."""

    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.expenses = []          # in-memory list of Expense objects
        self.next_id = 101          # starting auto-generated ID
        self.load_message = ""      # populated by load_from_disk(), printed by main()
        self.load_from_disk()

    # ---------------------- Persistence ----------------------
    def load_from_disk(self):
        """Load existing records from the CSV file, if present."""
        if not os.path.exists(self.filename):
            self.load_message = "No existing expense file found. Starting a new tracker."
            return

        try:
            with open(self.filename, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header row
                for row in reader:
                    if not row:
                        continue
                    try:
                        self.expenses.append(Expense.from_row(row))
                    except (ValueError, IndexError):
                        continue  # skip malformed rows instead of crashing

            if self.expenses:
                self.next_id = max(e.id for e in self.expenses) + 1
                self.load_message = f"Loaded {len(self.expenses)} expense record(s) successfully."
            else:
                self.load_message = "Expense file found but it was empty. Starting a new tracker."
        except Exception as e:
            self.load_message = f"[WARNING]: Could not fully load existing data ({e})."

    def save_to_disk(self, silent=True):
        """Persist the entire in-memory collection back to the CSV file."""
        try:
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Title", "Amount", "Category", "Date"])
                for expense in self.expenses:
                    writer.writerow(expense.to_row())
            return True
        except Exception as e:
            print(f"--> [ERROR]: Failed to save data to disk. ({e})")
            return False

    # ---------------------- ID Generation ----------------------
    def generate_id(self):
        """Guarantee a unique, auto-incrementing ID."""
        new_id = self.next_id
        self.next_id += 1
        return new_id

    # ---------------------- Duplicate Check ----------------------
    def has_duplicate(self, title, date, exclude_id=None):
        """Return True if an expense with the same title + date already exists."""
        for e in self.expenses:
            if e.id == exclude_id:
                continue
            if e.title.strip().lower() == title.strip().lower() and e.date == date:
                return True
        return False

    # ---------------------- CRUD Operations (pure logic) ----------------------
    def add_expense(self, title, amount, category, date):
        """Create a new Expense, append it, auto-save, and return it."""
        new_id = self.generate_id()
        expense = Expense(new_id, title, amount, category, date)
        self.expenses.append(expense)
        self.save_to_disk()  # auto-save after Add
        return expense

    def get_all_sorted(self):
        """Return all expenses sorted by date (oldest first)."""
        return sorted(self.expenses, key=lambda x: datetime.strptime(x.date, DATE_FORMAT))

    def find_by_id(self, expense_id):
        for e in self.expenses:
            if e.id == expense_id:
                return e
        return None

    def search_by_category(self, category):
        """Return all expenses matching a category (case-insensitive)."""
        return [e for e in self.expenses if e.category.strip().lower() == category.strip().lower()]

    def update_expense(self, expense_id, title=None, amount=None, category=None, date=None):
        """Update fields on an existing expense. None means 'leave unchanged'."""
        expense = self.find_by_id(expense_id)
        if expense is None:
            return None

        if title is not None:
            expense.title = title
        if amount is not None:
            expense.amount = amount
        if category is not None:
            expense.category = category
        if date is not None:
            expense.date = date

        self.save_to_disk()  # auto-save after Update
        return expense

    def delete_expense(self, expense_id):
        """Remove an expense by ID. Returns the removed Expense, or None."""
        expense = self.find_by_id(expense_id)
        if expense is None:
            return None

        self.expenses.remove(expense)
        self.save_to_disk()  # auto-save after Delete
        return expense

    # ---------------------- Summary / Analytics ----------------------
    def get_summary(self):
        """Return a dict of grand-total statistics and category breakdown."""
        if not self.expenses:
            return {
                "count": 0,
                "total": 0.0,
                "breakdown": {},
                "highest": None,
                "lowest": None,
                "average": 0.0,
            }

        total = sum(e.amount for e in self.expenses)
        breakdown = {}
        for e in self.expenses:
            breakdown[e.category] = breakdown.get(e.category, 0) + e.amount

        highest = max(self.expenses, key=lambda x: x.amount)
        lowest = min(self.expenses, key=lambda x: x.amount)
        average = total / len(self.expenses)

        return {
            "count": len(self.expenses),
            "total": total,
            "breakdown": breakdown,
            "highest": highest,
            "lowest": lowest,
            "average": average,
        }

    def get_monthly_summary(self, month, year):
        """Return category breakdown + total for a given month/year."""
        matches = [
            e for e in self.expenses
            if datetime.strptime(e.date, DATE_FORMAT).month == month
            and datetime.strptime(e.date, DATE_FORMAT).year == year
        ]

        breakdown = {}
        for e in matches:
            breakdown[e.category] = breakdown.get(e.category, 0) + e.amount

        total = sum(e.amount for e in matches)
        return {"count": len(matches), "total": total, "breakdown": breakdown}


# --------------------------------------------------------------------------
# CLI / INPUT LAYER  (all input() and print() formatting lives here)
# --------------------------------------------------------------------------
def prompt_title(current=None):
    prompt = f"Enter Expense Title [{current}]: " if current else "Enter Expense Title: "
    while True:
        value = input(prompt).strip()
        if value:
            return value
        if current is not None:
            return current  # blank keeps current value during update
        print("--> [ERROR]: This field cannot be empty. Please try again.")


def prompt_amount(current=None):
    label = f"Enter Expense Amount [{current:.2f}]: " if current is not None else "Enter Expense Amount: "
    while True:
        raw = input(label).strip()
        if raw == "" and current is not None:
            return current
        try:
            amount = float(raw)
            if amount < 0:
                print("--> [ERROR]: Amount cannot be negative. Please try again.")
                continue
            return amount
        except ValueError:
            print("--> [ERROR]: Invalid monetary value. Please enter a valid numerical decimal amount.")


def prompt_category(current=None):
    print("Select a Category:")
    for i, cat in enumerate(CATEGORIES, start=1):
        print(f"  {i}. {cat}")
    label = f"Enter Category number or name [{current}]: " if current else "Enter Category number or name: "

    while True:
        raw = input(label).strip()
        if raw == "" and current is not None:
            return current
        if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
            return CATEGORIES[int(raw) - 1]
        for cat in CATEGORIES:
            if raw.lower() == cat.lower():
                return cat
        print(f"--> [ERROR]: Invalid category. Please choose one of: {', '.join(CATEGORIES)}.")


def prompt_date(current=None, allow_blank_today=True):
    if current:
        label = f"Enter Date (DD-MM-YYYY) [{current}]: "
    elif allow_blank_today:
        label = "Enter Expense Date (DD-MM-YYYY) or leave blank for today: "
    else:
        label = "Enter Date (DD-MM-YYYY): "

    while True:
        raw = input(label).strip()
        if raw == "":
            if current is not None:
                return current
            if allow_blank_today:
                today_str = datetime.now().strftime(DATE_FORMAT)
                print(f"--> [SYSTEM]: Blank detected. Auto-assigned current timestamp date: {today_str}")
                return today_str
            print("--> [ERROR]: Date is required.")
            continue
        try:
            parsed = datetime.strptime(raw, DATE_FORMAT)
            return parsed.strftime(DATE_FORMAT)
        except ValueError:
            print("--> [ERROR]: Invalid date format/value. Please use strict DD-MM-YYYY (e.g., 17-07-2026).")


def prompt_id(label="Enter Expense ID: "):
    while True:
        raw = input(label).strip()
        try:
            return int(raw)
        except ValueError:
            print("--> [ERROR]: Invalid ID. Please enter a whole number.")


def print_table(expenses):
    """Print expenses in a professional boxed table format."""
    if not expenses:
        print("No records found. The ledger is currently empty.")
        return

    col_widths = {"id": 5, "title": 22, "amount": 12, "category": 14, "date": 12}

    def border():
        return (
            "+" + "-" * (col_widths["id"] + 2)
            + "+" + "-" * (col_widths["title"] + 2)
            + "+" + "-" * (col_widths["amount"] + 2)
            + "+" + "-" * (col_widths["category"] + 2)
            + "+" + "-" * (col_widths["date"] + 2) + "+"
        )

    def row(id_, title, amount, category, date):
        return (
            f"| {str(id_):<{col_widths['id']}} "
            f"| {str(title):<{col_widths['title']}} "
            f"| {str(amount):<{col_widths['amount']}} "
            f"| {str(category):<{col_widths['category']}} "
            f"| {str(date):<{col_widths['date']}} |"
        )

    print(border())
    print(row("ID", "Title", "Amount", "Category", "Date"))
    print(border())
    for e in expenses:
        title = e.title if len(e.title) <= col_widths["title"] else e.title[:col_widths["title"] - 3] + "..."
        print(row(e.id, title, f"Rs.{e.amount:,.2f}", e.category, e.date))
    print(border())
    print(f"Total Records: {len(expenses)}")


def print_menu():
    print("\n=== PERSONAL EXPENSE TRACKER ===")
    print("1. Add New Expense")
    print("2. View All Expenses")
    print("3. Search Expense (by ID)")
    print("4. Update Expense")
    print("5. Delete Expense")
    print("6. View Summary Metrics")
    print("7. Search by Category [Bonus]")
    print("8. Monthly Summary [Bonus]")
    print("9. Exit & Save Data")


# ---------------------- Menu Action Handlers ----------------------
def handle_add(tracker):
    print("\n--- Add New Expense ---")
    title = prompt_title()
    amount = prompt_amount()
    category = prompt_category()
    date = prompt_date()

    if tracker.has_duplicate(title, date):
        confirm = input(
            f"--> [WARNING]: An expense titled '{title}' on {date} already exists. Add anyway? (y/n): "
        ).strip().lower()
        if confirm != "y":
            print("Add cancelled.")
            return

    expense = tracker.add_expense(title, amount, category, date)
    print(f"\nSuccess: New record securely appended and saved! [Generated ID: {expense.id}]")


def handle_view(tracker):
    print("\n--- All Expenses (sorted by date) ---")
    print_table(tracker.get_all_sorted())


def handle_search_by_id(tracker):
    print("\n--- Search Expense (by ID) ---")
    if not tracker.expenses:
        print("No records found. The ledger is currently empty.")
        return

    search_id = prompt_id()
    expense = tracker.find_by_id(search_id)

    if expense is None:
        print(f"--> [NOT FOUND]: No expense exists with ID {search_id}.")
        return

    print("\nRecord Found:")
    print(f"  ID       : {expense.id}")
    print(f"  Title    : {expense.title}")
    print(f"  Amount   : Rs.{expense.amount:,.2f}")
    print(f"  Category : {expense.category}")
    print(f"  Date     : {expense.date}")


def handle_update(tracker):
    print("\n--- Update Expense ---")
    if not tracker.expenses:
        print("No records found. The ledger is currently empty.")
        return

    search_id = prompt_id()
    expense = tracker.find_by_id(search_id)

    if expense is None:
        print(f"--> [NOT FOUND]: No expense exists with ID {search_id}.")
        return

    print(f"Editing record ID {expense.id}. Leave any field blank to keep its current value.")
    title = prompt_title(current=expense.title)
    amount = prompt_amount(current=expense.amount)
    category = prompt_category(current=expense.category)
    date = prompt_date(current=expense.date)

    tracker.update_expense(expense.id, title=title, amount=amount, category=category, date=date)
    print(f"\nSuccess: Record ID {expense.id} updated and saved.")


def handle_delete(tracker):
    print("\n--- Delete Expense ---")
    if not tracker.expenses:
        print("No records found. The ledger is currently empty.")
        return

    search_id = prompt_id()
    expense = tracker.find_by_id(search_id)

    if expense is None:
        print(f"--> [NOT FOUND]: No expense exists with ID {search_id}.")
        return

    confirm = input(f"Are you sure you want to delete '{expense.title}' (ID {expense.id})? (y/n): ").strip().lower()
    if confirm == "y":
        tracker.delete_expense(search_id)
        print(f"Success: Record ID {search_id} deleted and saved.")
    else:
        print("Deletion cancelled.")


def handle_summary(tracker):
    print("\n=================== FINANCIAL TELEMETRY DASHBOARD ===================")
    summary = tracker.get_summary()

    print("\n--- COMPREHENSIVE STATUS SUMMARY ---")
    print(f"Total Expenses                    : {summary['count']}")
    print(f"Grand Combined Total Expenditures  : Rs.{summary['total']:,.2f}")

    if summary["count"] == 0:
        print("\n=======================================================================")
        return

    print(f"Average Expense                    : Rs.{summary['average']:,.2f}")
    print(f"Highest Expense                    : {summary['highest'].title} - Rs.{summary['highest'].amount:,.2f}")
    print(f"Lowest Expense                     : {summary['lowest'].title} - Rs.{summary['lowest'].amount:,.2f}")

    print("\n--- DYNAMIC CATEGORY-WISE BREAKDOWN ---")
    for category, total in sorted(summary["breakdown"].items(), key=lambda x: -x[1]):
        print(f"{category:<15}: Rs.{total:,.2f}")

    print("\n=======================================================================")


def handle_search_by_category(tracker):
    print("\n--- Search by Category ---")
    if not tracker.expenses:
        print("No records found. The ledger is currently empty.")
        return

    category = prompt_category()
    matches = tracker.search_by_category(category)

    print(f"\nExpenses in category '{category}':")
    print_table(matches)


def handle_monthly_summary(tracker):
    print("\n--- Monthly Summary ---")
    if not tracker.expenses:
        print("No records found. The ledger is currently empty.")
        return

    while True:
        raw_month = input("Enter month (1-12): ").strip()
        if raw_month.isdigit() and 1 <= int(raw_month) <= 12:
            month = int(raw_month)
            break
        print("--> [ERROR]: Please enter a valid month number between 1 and 12.")

    while True:
        raw_year = input("Enter year (e.g., 2026): ").strip()
        if raw_year.isdigit() and len(raw_year) == 4:
            year = int(raw_year)
            break
        print("--> [ERROR]: Please enter a valid 4-digit year.")

    result = tracker.get_monthly_summary(month, year)
    print(f"\nExpenses in {MONTH_NAMES[month]} {year}")
    print("-" * 40)
    if result["count"] == 0:
        print("No expenses recorded for this month.")
    else:
        for category, total in sorted(result["breakdown"].items(), key=lambda x: -x[1]):
            print(f"{category:<15}: Rs.{total:,.2f}")
        print("-" * 40)
        print(f"{'Total':<15}: Rs.{result['total']:,.2f}")
    print("-" * 40)


# --------------------------------------------------------------------------
# MAIN LOOP
# --------------------------------------------------------------------------
def main():
    tracker = ExpenseTracker()
    print(f"--> [SYSTEM]: {tracker.load_message}")

    actions = {
        "1": handle_add,
        "2": handle_view,
        "3": handle_search_by_id,
        "4": handle_update,
        "5": handle_delete,
        "6": handle_summary,
        "7": handle_search_by_category,
        "8": handle_monthly_summary,
    }

    while True:
        print_menu()
        choice = input("Choose option (1-9): ").strip()

        if choice == "9":
            tracker.save_to_disk()
            print("--> [SYSTEM]: Data successfully saved. Goodbye!")
            break
        elif choice in actions:
            actions[choice](tracker)
        else:
            print("--> [ERROR]: Invalid menu option. Please choose a number between 1 and 9.")


if __name__ == "__main__":
    main()