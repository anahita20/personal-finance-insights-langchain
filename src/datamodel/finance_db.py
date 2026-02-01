import sqlite3
import logging
from pathlib import Path
from typing import List, Any, Dict, Optional, Union
import json

logger = logging.getLogger(__name__)


class FinanceQueryName:
    """
    This class has the keys for the queries that are stored in JSON file 
    """
    # Transactions
    GET_ALL_TRANSACTIONS = 'get_all_transactions'
    GET_TRANSACTIONS_PAGINATED = 'get_transactions_paginated'
    GET_TOTAL_TRANSACTIONS_COUNT = 'get_total_transactions_count'
    GET_MONTHLY_INCOME_VS_EXPENSE = 'get_monthly_income_vs_expense'
    GET_WEEKLY_INCOME_VS_EXPENSE = 'get_weekly_income_vs_expense'
    GET_DAILY_INCOME_VS_EXPENSE = 'get_daily_income_vs_expense'
    GET_EXPENSE_CATEGORY_SUMMARY = 'get_expense_category_summary'
    GET_EXPENSE_CATEGORY_SUMMARY_FILTERED = 'get_expense_category_summary_filtered'
    GET_SPENDING_BY_DAY_OF_WEEK = 'get_spending_by_day_of_week'
    GET_TOP_EXPENSE_DESCRIPTIONS = 'get_top_expense_descriptions'
    GET_CHECKING_DAILY_CHANGE = 'get_checking_daily_change'
    GET_TRANSACTIONS_BY_CATEGORY = 'get_transactions_by_category'
    GET_TRANSACTIONS_BY_DATE_RANGE = 'get_transactions_by_date_range'
    GET_ALL_ACCOUNTS = 'get_all_accounts'
    GET_ACCOUNT_ACTIVITY_BY_MONTH = 'get_account_activity_by_month'
    
    # Goals
    GET_ALL_GOALS = 'get_all_goals'
    GET_GOAL_BY_NAME = 'get_goal_by_name'
    CREATE_GOAL = 'create_goal'
    UPDATE_GOAL_SAVED_AMOUNT = 'update_goal_saved_amount'
    UPDATE_GOAL_STATUS = 'update_goal_status'
    DELETE_GOAL = 'delete_goal'
    
    # Budgets
    GET_ALL_BUDGETS = 'get_all_budgets'
    GET_BUDGET_BY_CATEGORY = 'get_budget_by_category'
    CREATE_BUDGET = 'create_budget'
    UPDATE_BUDGET = 'update_budget'
    DELETE_BUDGET = 'delete_budget'
    
    # Analytics
    GET_MONTHLY_SPENDING_BY_CATEGORY = 'get_monthly_spending_by_category'


class SQLQueryRepository:
    """
    Repository for storing and managing SQL queries for interacting with SQLite.
    This is a Singleton Class.
    """
    _instance = None

    def __new__(cls, examples_file: str = None, queries_file: str = None):
        if cls._instance is None:
            cls._instance = super(SQLQueryRepository, cls).__new__(cls)
            cls._instance._initialize(examples_file, queries_file)
        return cls._instance

    def _initialize(self, examples_file: str, queries_file: str) -> None:
        if queries_file is None:
            raise ValueError('Queries file name must be provided on the first instantiation.')

        query_folder_path = Path(__file__).resolve().parent / 'queries'
        self.queries = self._load_json(query_folder_path / queries_file)
        
        if examples_file:
            self.examples = self._load_json(query_folder_path / examples_file)
        else:
            self.examples = []

    def get_query(self, query_name: str) -> str:
        """
        Retrieve a SQL query by name.
        """
        try:
            return self.queries[query_name]
        except KeyError:
            logger.error(f'Query: {query_name} not found in the repository.')
            raise KeyError(f'Query: {query_name} not found in the repository.')

    def getExamples(self) -> List[Dict[str, str]]:
        return self.examples

    def _load_json(self, file_path: Path) -> Any:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except Exception as e:
            logger.error(f'An unexpected error occurred while loading JSON from file: {file_path}')
            raise e


class FinanceDB:
    """
    This Class is used to perform CRUD operations on SQLite Database
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = None

    def close(self):
        if self.conn:
            self.conn.close()

    # Context Management 
    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Set row_factory to sqlite3.Row to allow dictionary-like access
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f'Failed to initialize SQLite DB {e}')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def run_query(self, query: str, parameters: Union[Dict[str, Any], List[Any], tuple] = None) -> List[Dict[str, Any]]:
        with self.conn:
            cursor = self.conn.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return [dict(row) for row in cursor.fetchall()]
            return []