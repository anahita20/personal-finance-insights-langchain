from flask import request, jsonify, Flask
from flask_cors import CORS
from pathlib import Path
from src.datamodel.finance_db import FinanceDB, SQLQueryRepository, FinanceQueryName
from datetime import datetime, timedelta
from src.finance_sql_pipeline import SQLFinanceQuery
from dateutil.relativedelta import relativedelta
from src.insights_engine import enrich_with_forecast_and_anomalies

app = Flask(__name__)
CORS(app)

INSIGHT_CACHE = {}


@app.route("/", methods=["GET"])
def home():
    return "Flask API is running!", 200

@app.route('/api/message', methods=['POST'])
def chat_response():
    prompt = request.json['prompt']
    resp = None
    eq = SQLFinanceQuery()
    try:
        resp = eq.ask(question=prompt)
    except Exception as e:
        return jsonify({
            "error": "An internal error occoured. Please try again later.",
            "details": str(e)
        }), 500
    return jsonify({"assistant_message": resp}), 200

@app.route('/api/insights', methods=['POST'])
def get_insights():
    try:
        req_data = request.json
        chart_title = req_data.get('chart_title')
        sql_query = req_data.get('sql_query')
        query_params = req_data.get('query_params')
        query_output = req_data.get('query_output')
        
        fq = SQLFinanceQuery()
        insight = _get_insight(fq, chart_title, sql_query, query_params, query_output)
        
        return jsonify({"insight": insight})
    except Exception as e:
        print(f"Error generating insight: {e}")
        return jsonify({"error": str(e)}), 500

# Path to the database file in the root directory
DB_PATH = Path(__file__).parent / 'data/personal_finance/finance.db'

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)

        # Initialize repository to get the SQL query
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        
        with FinanceDB(str(DB_PATH)) as db:
            if page is not None and limit is not None:
                # Pagination logic
                offset = (page - 1) * limit
                query = repo.get_query(FinanceQueryName.GET_TRANSACTIONS_PAGINATED)
                count_query = repo.get_query(FinanceQueryName.GET_TOTAL_TRANSACTIONS_COUNT)
                
                transactions = db.run_query(query, (limit, offset))
                total_count_res = db.run_query(count_query)
                total_count = total_count_res[0]['count'] if total_count_res else 0
                
                return jsonify({
                    "data": transactions,
                    "total": total_count,
                    "page": page,
                    "limit": limit
                })
            else:
                # Default behavior (or simple limit for dashboard)
                query = repo.get_query(FinanceQueryName.GET_TRANSACTIONS_PAGINATED if limit else FinanceQueryName.GET_ALL_TRANSACTIONS)
                params = (limit, 0) if limit else None
                transactions = db.run_query(query, params)
                return jsonify(transactions)
            
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/income-vs-expenses', methods=['GET'])
def get_income_vs_expenses():
    try:
        period = request.args.get('period', 'month')
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        today = datetime.now().date()

        if period == 'week':
            start_date = today - timedelta(days=7)
            query = repo.get_query(FinanceQueryName.GET_DAILY_INCOME_VS_EXPENSE)
            params = (start_date.strftime("%Y-%m-%d"),)
            granularity = "daily"
            horizon = 2
        else:
            start_date = today - timedelta(days=30)
            query = repo.get_query(FinanceQueryName.GET_DAILY_INCOME_VS_EXPENSE)
            params = (start_date.strftime("%Y-%m-%d"),)
            granularity = "daily"
            horizon = 14

        with FinanceDB(str(DB_PATH)) as db:
            raw_data = db.run_query(query, params)

        enriched_data = enrich_with_forecast_and_anomalies(
            data=raw_data,
            date_key="date",
            value_keys=("income", "expense"),
            granularity=granularity,
            horizon=horizon
        )

        return jsonify({
            "data": enriched_data,
            "insight_input": {
                "chart_title": "Income Vs Expenses",
                "sql_query": query,
                "query_params": params,
                "query_output": enriched_data
            }
        })

    except Exception as e:
        print(f"Error fetching income vs expenses: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    try:
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        query = repo.get_query(FinanceQueryName.GET_ALL_ACCOUNTS)
        activity_query = repo.get_query(FinanceQueryName.GET_ACCOUNT_ACTIVITY_BY_MONTH)
        
        current_month_str = datetime.now().strftime('%Y-%m')
        
        with FinanceDB(str(DB_PATH)) as db:
            accounts = db.run_query(query) # List of dicts
            activity = db.run_query(activity_query, (current_month_str,))
            
            # Convert activity to a dict for easier lookup
            activity_map = {row['account_name'].lower(): row for row in activity}
            
            enriched_accounts = []
            for acc in accounts:
                acc_dict = dict(acc)
                name_key = acc_dict['name'].lower()
                
                # Default activity
                credits = 0.0
                debits = 0.0
                
                if name_key in activity_map:
                    credits = activity_map[name_key]['credits']
                    debits = activity_map[name_key]['debits']
                
                # Calculate Net Change for this month based on account type
                # Depository (Checking): Credits increase, Debits decrease
                # Credit (Cards): Debits increase balance (debt), Credits decrease balance
                if acc_dict['type'] == 'depository':
                    net_change = credits - debits
                else:
                    net_change = debits - credits
                
                current_balance = acc_dict['balance']
                prev_balance = current_balance - net_change
                
                if prev_balance == 0:
                    percent_change = 100.0 if current_balance != 0 else 0.0
                else:
                    percent_change = ((current_balance - prev_balance) / prev_balance * 100)
                
                # DEMO MODE: If trend is 0% (e.g. fresh DB), generate deterministic dummy data
                if percent_change == 0:
                    # Create a seed from the account name
                    seed = sum(ord(c) for c in acc_dict['name'])
                    # Generate a float between 1.5 and 11.5
                    dummy_val = (seed % 100) / 10.0 + 1.5
                    # Flip sign based on seed parity to show variety
                    if seed % 2 == 1:
                        dummy_val = -dummy_val
                    percent_change = dummy_val
                
                acc_dict['trend'] = percent_change
                enriched_accounts.append(acc_dict)
                
            return jsonify(enriched_accounts)
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/expense-summary', methods=['GET'])
def get_expense_summary():
    try:
        period = request.args.get('period', 'month')
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        params = None
        today = datetime.now().date()

        if period == 'week':
            start_date = today - timedelta(days=7)
            query = repo.get_query(FinanceQueryName.GET_EXPENSE_CATEGORY_SUMMARY_FILTERED)
            params = (start_date.strftime("%Y-%m-%d"),)
        else:
            # Default to month
            start_date = today - timedelta(days=30)
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        params = (start_date_str,)

        query_category = repo.get_query(FinanceQueryName.GET_EXPENSE_CATEGORY_SUMMARY_FILTERED)
        query_day = repo.get_query(FinanceQueryName.GET_SPENDING_BY_DAY_OF_WEEK)
        query_desc = repo.get_query(FinanceQueryName.GET_TOP_EXPENSE_DESCRIPTIONS)

        # Daily spending always uses month start, ignoring the toggle
        day_params = ((today - timedelta(days=30)).strftime("%Y-%m-%d"),)
        
        with FinanceDB(str(DB_PATH)) as db:
            data_category = db.run_query(query_category, params)
            data_day = db.run_query(query_day, day_params)
            data_desc = db.run_query(query_desc, params)
            
            # Process day data to map 0-6 to names (0 is Sunday in strftime %w)
            days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            day_map = {int(row['day_index']): row['total'] for row in data_day}
            processed_days = [{'day': days[i], 'value': day_map.get(i, 0)} for i in range(7)]

            insight_inputs = {
                "by_category": {
                    "chart_title": "Expense by category",
                    "sql_query": query_category,
                    "query_params": params,
                    "query_output": data_category
                },
                "by_day": {
                    "chart_title": "Expense by day of the week",
                    "sql_query": query_day,
                    "query_params": day_params,
                    "query_output": processed_days
                },
                "top_descriptions": {
                    "chart_title": "Top 3 Expenses",
                    "sql_query": query_desc,
                    "query_params": params,
                    "query_output": data_desc
                }
            }

            return jsonify({
                "by_category": data_category,
                "by_day": processed_days,
                "top_descriptions": data_desc,
                "insight_inputs": insight_inputs
            })
    except Exception as e:
        print(f"Error fetching expense summary: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    try:
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        budget_query = repo.get_query(FinanceQueryName.GET_ALL_BUDGETS)
        spending_query = repo.get_query(FinanceQueryName.GET_MONTHLY_SPENDING_BY_CATEGORY)
        
        month_param = request.args.get('month')
        if month_param:
            current_month = month_param
        else:
            current_month = datetime.now().strftime('%Y-%m')
        
        with FinanceDB(str(DB_PATH)) as db:
            budgets = db.run_query(budget_query)
            spending = db.run_query(spending_query, (current_month,))
            
            spending_map = {row['category']: row['total'] for row in spending}
            
            result = []
            for b in budgets:
                cat = b['category']
                limit = b['amount_limit']
                spent = spending_map.get(cat, 0)
                if spent is None: spent = 0
                
                result.append({
                    "id": b['id'],
                    "category": cat,
                    "limit": limit,
                    "spent": spent,
                    "percentage": min((spent / limit) * 100, 100) if limit > 0 else 0
                })
            
            return jsonify(result)
    except Exception as e:
        print(f"Error fetching budgets: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/goals', methods=['GET'])
def get_goals():
    try:
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        query = repo.get_query(FinanceQueryName.GET_ALL_GOALS)
        
        with FinanceDB(str(DB_PATH)) as db:
            goals = db.run_query(query)
            
        results = []
        for g in goals:
            g_dict = dict(g)
            # Map saved_amount to current_amount for frontend compatibility
            g_dict['current_amount'] = g_dict.pop('saved_amount', 0)
            g_dict['id'] = str(g_dict['id'])
            results.append(g_dict)
            
        return jsonify(results)
    except Exception as e:
        print(f"Error fetching goals: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/goal-forecast', methods=['GET'])
def get_goal_forecast():
    try:
        goal_id = request.args.get('goal_id')
        
        with FinanceDB(str(DB_PATH)) as db:
            if goal_id:
                goals = db.run_query("SELECT * FROM financial_goals WHERE id = ?", (goal_id,))
            else:
                goals = db.run_query("SELECT * FROM financial_goals LIMIT 1")
        
        if not goals:
             return jsonify({"error": "No goals found"}), 404

        goal = dict(goals[0])
        goal['current_amount'] = goal.pop('saved_amount', 0)
        goal['id'] = str(goal['id'])
        
        # 1. Calculate Actual Monthly Savings Rate from last 90 days
        repo = SQLQueryRepository(queries_file='sql_queries.json')
        query = repo.get_query(FinanceQueryName.GET_DAILY_INCOME_VS_EXPENSE)
        start_date_90 = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        with FinanceDB(str(DB_PATH)) as db:
            # Re-using the daily income/expense query to calculate aggregate savings
            data_90 = db.run_query(query, (start_date_90,))
            
        total_income = sum(d['income'] for d in data_90)
        total_expense = sum(d['expense'] for d in data_90)
        # Simple average monthly savings (90 days approx 3 months)
        avg_monthly_savings = (total_income - total_expense) / 3
        
        # 2. Generate Chart Data
        chart_data = []
        today = datetime.now()
        target_date = datetime.strptime(goal['target_date'], "%Y-%m-%d")
        
        # History (Simulated for the past 6 months to reach current_amount)
        # We assume a somewhat linear progression to current amount for visualization
        for i in range(6, -1, -1):
            date = (today - relativedelta(months=i)).strftime("%Y-%m")
            # Simulate history: Current - (Avg * i), but don't go below 0
            simulated_past = max(0, goal['current_amount'] - (avg_monthly_savings * i))
            chart_data.append({
                "date": date,
                "actual": int(simulated_past),
                "forecast": None,
                "ideal": None
            })

        # Future (Forecast vs Ideal)
        months_left = (target_date.year - today.year) * 12 + target_date.month - today.month
        months_left = max(1, months_left)
        
        ideal_monthly_rate = (goal['target_amount'] - goal['current_amount']) / months_left
        
        # Add the "Today" point to start the future lines
        chart_data[-1]["forecast"] = goal['current_amount']
        chart_data[-1]["ideal"] = goal['current_amount']
        
        for i in range(1, months_left + 1):
            future_date = (today + relativedelta(months=i)).strftime("%Y-%m")
            forecast_val = goal['current_amount'] + (avg_monthly_savings * i)
            ideal_val = goal['current_amount'] + (ideal_monthly_rate * i)
            
            chart_data.append({
                "date": future_date,
                "actual": None,
                "forecast": int(forecast_val),
                "ideal": int(ideal_val)
            })

        insight_input = {
            "chart_title": f"Goal Forecast: {goal['name']}",
            "sql_query": "N/A (Derived from Aggregated Savings Rate)",
            "query_params": {"goal": goal['name'], "current_savings_rate": round(avg_monthly_savings, 2)},
            "query_output": {
                "goal_target": goal['target_amount'],
                "current_amount": goal['current_amount'],
                "months_to_target": months_left,
                "projected_amount_at_target_date": chart_data[-1]['forecast'],
                "status": "On Track" if chart_data[-1]['forecast'] >= goal['target_amount'] else "At Risk"
            }
        }

        return jsonify({"data": chart_data, "goal": goal, "insight_input": insight_input})

    except Exception as e:
        print(f"Error generating goal forecast: {e}")
        return jsonify({"error": str(e)}), 500
    
def _get_insight(fq, title, query, p, data):
    key = f"{title}_{str(p)}"
    if key in INSIGHT_CACHE:
        return INSIGHT_CACHE[key]
    try:
        res = fq.generate_chart_insight(title, query, str(p), data)
        INSIGHT_CACHE[key] = res
        return res
    except Exception as e:
        print(f"Error generating insight for {title}: {e}")
        return ""

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:8080")
    app.run(debug=True, port=8080)
