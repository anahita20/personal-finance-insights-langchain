import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to sys.path to allow imports from src
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from src.datamodel.finance_db import FinanceDB, SQLQueryRepository, FinanceQueryName

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_queries():
    db_path = root_path / 'data' / 'personal_finance' / 'finance.db'
    
    # 1. Initialize Repository
    # We must provide the queries_file name. examples_file is optional.
    try:
        repo = SQLQueryRepository(queries_file='sql_queries.json')
    except Exception as e:
        logger.error(f"Failed to initialize Query Repository: {e}")
        return

    if not db_path.exists():
        logger.error(f"Database not found at {db_path}. Please run 'python scripts/setup_sqlite.py' first.")
        return

    logger.info(f"Connecting to database at {db_path}...")
    
    with FinanceDB(str(db_path)) as db:
        # 2. Test: Get All Accounts
        logger.info("\n--- Testing GET_ALL_ACCOUNTS ---")
        query = repo.get_query(FinanceQueryName.GET_ALL_ACCOUNTS)
        results = db.run_query(query)
        if results:
            for row in results:
                print(dict(row))
        else:
            logger.warning("No accounts found.")

        # 3. Test: Get Transactions (Limit 5)
        logger.info("\n--- Testing GET_ALL_TRANSACTIONS (First 5) ---")
        query = repo.get_query(FinanceQueryName.GET_ALL_TRANSACTIONS)
        results = db.run_query(query)
        if results:
            for row in results[:5]:
                print(dict(row))
        else:
            logger.warning("No transactions found.")

        # 4. Test: Get All Goals
        logger.info("\n--- Testing GET_ALL_GOALS ---")
        query = repo.get_query(FinanceQueryName.GET_ALL_GOALS)
        results = db.run_query(query)
        if results:
            for row in results:
                print(dict(row))
        else:
            logger.warning("No goals found.")

        # 5. Test: Get All Budgets
        logger.info("\n--- Testing GET_ALL_BUDGETS ---")
        query = repo.get_query(FinanceQueryName.GET_ALL_BUDGETS)
        results = db.run_query(query)
        if results:
            for row in results:
                print(dict(row))
        else:
            logger.warning("No budgets found.")

        # 6. Test: Monthly Spending Analytics
        logger.info("\n--- Testing GET_MONTHLY_SPENDING_BY_CATEGORY (Current Month) ---")
        # Since setup_sqlite.py shifts dates to end 'today', we use the current month
        current_month = datetime.now().strftime('%Y-%m')
        
        query = repo.get_query(FinanceQueryName.GET_MONTHLY_SPENDING_BY_CATEGORY)
        params = [current_month]
        results = db.run_query(query, params)
        
        if not results:
             print(f"No spending data found for {current_month}.")
        
        for row in results:
            print(f"Category: {row['category']}, Total: ${row['total']:.2f}")

        # 7. Test: Full-text search
        logger.info("\n--- Testing entity_db_fulltext_search ---")
        query = repo.get_query("entity_db_fulltext_search")
        
        search_term = "paycheck"
        params = {"value": search_term}
        results = db.run_query(query, params)
        
        if results:
            logger.info(f"Found results for '{search_term}':")
            for row in results:
                print(dict(row))
        else:
            logger.warning(f"No results found for '{search_term}'.")

if __name__ == "__main__":
    test_queries()

