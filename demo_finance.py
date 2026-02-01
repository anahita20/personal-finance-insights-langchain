from src.finance_sql_pipeline import SQLFinanceQuery
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true', help='enable verbose mode')
args = parser.parse_args()

fq = SQLFinanceQuery()
while True:
    print('Enter exit to stop')
    question = input('Enter your question: ')
    if question == 'exit':
        break
    try:
        resp = fq.ask(question=question, verbose=True)
        print('\n', 'Answer:', resp, '\n\n')
    except Exception as e:
        print(e)
