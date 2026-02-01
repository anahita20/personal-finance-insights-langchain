import sqlite3
import csv
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_paths():
    """
    Resolve paths for the database and data file relative to the script location.
    """
    root_folder = Path(__file__).resolve().parent.parent
    db_path = root_folder / 'data' / 'personal_finance' / 'finance.db'
    data_path = root_folder / 'data' / 'personal_finance' / 'personal_finance.csv'
    goals_path = root_folder / 'data' / 'personal_finance' / 'financial_goals.csv'
    budgets_path = root_folder / 'data' / 'personal_finance' / 'monthly_budgets.csv'
    return db_path, data_path, goals_path, budgets_path


def get_db_connection(db_file: Path) -> Optional[sqlite3.Connection]:
    """Create a database connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
    return None


def clean_up() -> None:
    """Deletes the existing database file to start fresh."""
    db_path = get_paths()[0]
    if db_path.exists():
        try:
            db_path.unlink()
            logger.info(f"Deleted database file: {db_path}")
        except Exception as e:
            logger.error(f"Error deleting database file: {e}")
    else:
        logger.info("Database file does not exist, nothing to clean.")


def setup_db() -> None:
    """Reads the CSV and populates the SQLite database."""
    db_path, data_path, goals_path, budgets_path = get_paths()

    if not data_path.exists():
        logger.error(f"Data file not found at: {data_path}")
        return

    conn = get_db_connection(db_path)
    if conn is None:
        return

    try:
        with open(data_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                logger.error("CSV file is empty or missing headers.")
                return

            # Sanitize headers for SQL column names
            original_headers = reader.fieldnames
            sanitized_headers = [h.strip().replace(' ', '_').lower() for h in original_headers]
            
            # Create Table dynamically based on CSV headers
            # We default to TEXT for simplicity in this setup script
            # But for finance data, we want Amount to be REAL and Date to be sortable
            column_defs = []
            for col in sanitized_headers:
                data_type = "REAL" if col == "amount" else "TEXT"
                column_defs.append(f"{col} {data_type}")
            
            columns_def = ", ".join(column_defs)
            create_table_sql = f"CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_def})"
            
            cursor = conn.cursor()
            cursor.execute(create_table_sql)

            # Create Financial Goals Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    target_date TEXT NOT NULL,
                    saved_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'on_track',
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create Monthly Budgets Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL UNIQUE,
                    amount_limit REAL NOT NULL
                )
            """)

            # Create Accounts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    balance REAL NOT NULL
                )
            """)

            # Load Financial Goals from CSV
            if goals_path.exists():
                with open(goals_path, mode='r', encoding='utf-8-sig') as gf:
                    goals_reader = csv.DictReader(gf)
                    goals_rows = []
                    for row in goals_reader:
                        # Convert date from MM/DD/YYYY to YYYY-MM-DD
                        t_date = row['Target_Date']
                        try:
                            t_date = datetime.strptime(t_date, "%m/%d/%Y").strftime("%Y-%m-%d")
                        except ValueError:
                            pass
                        goals_rows.append((
                            row['Name'], float(row['Target_Amount']), t_date, float(row['Saved_Amount']), row['Status']
                        ))
                    cursor.executemany("INSERT INTO financial_goals (name, target_amount, target_date, saved_amount, status) VALUES (?, ?, ?, ?, ?)", goals_rows)
                    logger.info(f"Inserted {len(goals_rows)} goals from CSV.")
            else:
                logger.warning(f"Goals file not found at {goals_path}")

            # Load Monthly Budgets from CSV
            if budgets_path.exists():
                with open(budgets_path, mode='r', encoding='utf-8-sig') as bf:
                    budgets_reader = csv.DictReader(bf)
                    budget_rows = []
                    for row in budgets_reader:
                        budget_rows.append((row['Category'], float(row['Amount_Limit'])))
                    cursor.executemany("INSERT INTO monthly_budgets (category, amount_limit) VALUES (?, ?)", budget_rows)
                    logger.info(f"Inserted {len(budget_rows)} budgets from CSV.")
            else:
                logger.warning(f"Budgets file not found at {budgets_path}")

            # Prepare Insert Statement
            placeholders = ", ".join(["?" for _ in sanitized_headers])
            insert_sql = f"INSERT INTO transactions ({', '.join(sanitized_headers)}) VALUES ({placeholders})"

            # Read all rows to memory to calculate date shift
            all_rows = list(reader)

            # Calculate date shift to bring data to current time
            max_date = None
            date_header = next((h for h, s in zip(original_headers, sanitized_headers) if s == 'date'), None)

            if date_header:
                for row in all_rows:
                    try:
                        dt = datetime.strptime(row[date_header], "%m/%d/%Y")
                        if max_date is None or dt > max_date:
                            max_date = dt
                    except ValueError:
                        pass
            
            shift_delta = datetime.now() - max_date if max_date else timedelta(0)

            # Calculate Balances for Accounts Table
            # Mock starting balances: Checking has cash, Cards start at 0 debt
            account_balances = {
                'checking': 5000.00,
                'platinumcard': 0.00,
                'silvercard': 0.00
            }

            for row in all_rows:
                acc = row.get('Account_Name', '').lower()
                try:
                    amt = float(row.get('Amount', 0))
                except ValueError:
                    continue
                
                t_type = row.get('Transaction_Type', '').lower()

                if acc == 'checking':
                    # Asset: Credit adds, Debit subtracts
                    account_balances[acc] += amt if t_type == 'credit' else -amt
                elif acc in ['platinumcard', 'silvercard']:
                    # Liability: Debit increases debt, Credit reduces debt
                    account_balances[acc] += amt if t_type == 'debit' else -amt

            # Insert Accounts
            cursor.executemany("INSERT INTO accounts (name, type, balance) VALUES (?, ?, ?)", 
                               [(k, 'depository' if k == 'checking' else 'credit', v) for k, v in account_balances.items()])

            # Insert Data
            rows_to_insert = []
            for row in all_rows:
                # Ensure values are ordered correctly according to headers
                row_data = []
                for h, sanitized_h in zip(original_headers, sanitized_headers):
                    val = row[h]
                    if sanitized_h == "date":
                        try:
                            d = datetime.strptime(val, "%m/%d/%Y")
                            val = (d + shift_delta).strftime("%Y-%m-%d")
                        except ValueError:
                            pass
                    elif sanitized_h == "amount":
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                    row_data.append(val)
                rows_to_insert.append(row_data)

            cursor.executemany(insert_sql, rows_to_insert)
            conn.commit()
            logger.info(f"Successfully inserted {len(rows_to_insert)} records into 'transactions' table.")

            # Create a global search index on text fields for faster lookups
            logger.info("Creating global search index...")
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS global_search_index USING fts5(original_text, column_name, table_name, tokenize = 'porter')")

            # Populate the search index from multiple tables
            index_queries = {
                "transaction_description": ("SELECT DISTINCT Description, 'transaction_description', 'transactions' FROM transactions", "INSERT INTO global_search_index (original_text, column_name, table_name) VALUES (?, ?, ?)"),
                "transaction_category": ("SELECT DISTINCT Category, 'transaction_category', 'transactions' FROM transactions", "INSERT INTO global_search_index (original_text, column_name, table_name) VALUES (?, ?, ?)"),
                "transaction_type": ("SELECT DISTINCT transaction_type, 'transaction_type', 'transactions' FROM transactions", "INSERT INTO global_search_index (original_text, column_name, table_name) VALUES (?, ?, ?)"),
                "goal_name": ("SELECT DISTINCT name, 'goal_name', 'financial_goals' FROM financial_goals", "INSERT INTO global_search_index (original_text, column_name, table_name) VALUES (?, ?, ?)"),
                "account_name": ("SELECT DISTINCT name, 'account_name', 'accounts' FROM accounts", "INSERT INTO global_search_index (original_text, column_name, table_name) VALUES (?, ?, ?)")
            }

            for entity_type, (query, insert_sql) in index_queries.items():
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    cursor.executemany(insert_sql, rows)
                    logger.info(f"Indexed {len(rows)} records for entity type '{entity_type}'.")
                except sqlite3.Error as e:
                    logger.error(f"Failed to index '{entity_type}': {e}")

            conn.commit()
            logger.info("Global search index created and populated successfully.")
            
    except Exception as e:
        logger.error(f"An error occurred during setup: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    print("Select one of the options below (1 or 2):\n",
          "\t 1. Clean up database\n",
          "\t 2. Setup database (Clean + Install)\n"
          )
    choice = input("Your option: ")
    if choice == "1":
        clean_up()
    else:
        clean_up()
        setup_db()