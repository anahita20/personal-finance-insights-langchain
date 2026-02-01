from pathlib import Path
from typing import Dict, Any, List
import yaml
import logging
import json

from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.callbacks.tracers import ConsoleCallbackHandler
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from src.pipeline.llm import LLMFactory
from src.pipeline.abstract_query_engine import AbstractQueryEngine, PromptRepository
from src.datamodel.finance_db import SQLQueryRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Entities(BaseModel):
    """Identifying information about entities."""

    names: List[str] = Field(
        ...,
        description="All the Transactions, Categories, Dates, or Account Names appearing in the text",
    )


class SQLFinanceQuery(AbstractQueryEngine):
    """
    FinanceQuery pipeline which uses SQLite database as the backend
    """

    def __init__(self) -> None:
        self.config = self._load_config()
        self.db = self._load_db()
        self.llm = LLMFactory().get_LLM(
            llm_provider=self.config['use_llm'],
            cfg=self.config['llm'][self.config['use_llm']]
        )
        # Assuming config has a 'sqlite' section similar to 'neo4j'
        self.prompt_repo = PromptRepository(
            prompts_file=self.config['db']['sqlite']['prompts_file']
        )
        self.query_repo = SQLQueryRepository(
            examples_file=self.config['db']['sqlite']['examples_file'],
            queries_file=self.config['db']['sqlite']['queries_file']
        )
        self.chain = None

    # Step 1: Named Entity Recognition
    def prepare_ner_chain(self):
        system, human = self.prompt_repo.get_ner_prompt()
        dict_schema = convert_to_openai_function(Entities)  # Output Format
        ner_prompt = ChatPromptTemplate.from_messages(
            [(self.SYSTEM_MESSAGE, system), (self.HUMAN_MESSAGE, human)]
        )
        entity_chain = ner_prompt | self.llm.with_structured_output(dict_schema)
        return entity_chain

    # Step 2: Matching Entities with Database Values
    def map_to_database(self, values: List[str]) -> str:
        match_query = self.query_repo.get_query('entity_db_fulltext_search')
        result = ""
        for value in values:
            try:
                # self.db.run can execute a query with parameters
                response = self.db.run(match_query, parameters={"value": value})
                if response:
                    result += f"'{value}' maps to database values: {response}\n"
            except Exception as e:
                logger.warning(f"Failed to map entity {value}: {e}")
                pass
        return result


    # Step 3: Prepare SQL query based on identified entities and db match
    def prepare_db_query_response(self, entity_chain):

        # 1. Few-shot Examples - pull examples from the repository
        example_prompt = ChatPromptTemplate.from_messages(
            [(self.HUMAN_MESSAGE, "{question}"), (self.SYSTEM_MESSAGE, "{query}")]
        )

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            examples=self.query_repo.getExamples(),
            example_prompt=example_prompt,
        )

        # 2. Create Prompt
        # Note: Ensure 'sqlPrompt' key exists in your sql_prompts.json
        system, human = self.prompt_repo.get_db_prompt()
        sql_prompt = ChatPromptTemplate.from_messages([(self.SYSTEM_MESSAGE, system), (self.HUMAN_MESSAGE, human)])

        # 3. Prepare chain
        sql_response = (
                RunnablePassthrough.assign(names=entity_chain)
                | RunnablePassthrough.assign(
            entities_list=lambda x: self.map_to_database(self._extract_names(x['names'])),
            schema=lambda _: self.db.get_table_info()) # LangChain method to get CREATE TABLE statements
                | RunnablePassthrough.assign(
            examples=lambda _: few_shot_prompt.format()
        )
                | sql_prompt
                | self.llm.bind(stop=["\nSQLResult:"])
                | self._clean_sql_output
        )
        return sql_response

    # Step 4. Validate SQL and Create Final Response
    def prepare_response_chain(self, sql_response):
        system, human = self.prompt_repo.get_response_prompt()
        response_prompt = ChatPromptTemplate.from_messages(
            [(self.SYSTEM_MESSAGE, system), (self.HUMAN_MESSAGE, human)]
        )

        chain = (
                RunnablePassthrough.assign(query=sql_response)
                | RunnablePassthrough.assign(
            response=lambda x: self.db.run(x["query"]),
        )
                | response_prompt
                | self.llm
                | StrOutputParser()
        )
        return chain

    # Putting it all together
    def prepare_app_query_chain(self):
        entity_chain = self.prepare_ner_chain()  # Step 1
        sql_response = self.prepare_db_query_response(entity_chain)  # Step 2, 3
        finance_query_chain = self.prepare_response_chain(sql_response)  # Step 4
        return finance_query_chain

    def ask(self, question: str, verbose: bool = False) -> str:
        if self.chain is None:
            self.chain = self.prepare_app_query_chain()

        if verbose:
            return self.chain.invoke({"question": question}, config={'callbacks': [ConsoleCallbackHandler()]})

        return self.chain.invoke({"question": question})

    def generate_chart_insight(self, chart_title: str, sql_query: str, query_params: Any, query_output: Any) -> str:
        system, human = self.prompt_repo.get_chart_insight_prompt()
        prompt = ChatPromptTemplate.from_messages([(self.SYSTEM_MESSAGE, system), (self.HUMAN_MESSAGE, human)])
        chain = prompt | self.llm | StrOutputParser()

        return chain.invoke({
            "chart_title": chart_title,
            "sql_query": sql_query,
            "query_params": json.dumps(query_params, default=str),
            "query_output": json.dumps(query_output, default=str)
        })

    def _load_config(self) -> Dict[str, Any]:
        llm_config_path = Path(__file__).resolve().parent.parent / 'config' / 'app_config.yaml'
        with open(llm_config_path, 'r') as file:
            return yaml.safe_load(file)

    def _load_db(self) -> SQLDatabase:
        # Constructing the SQLite URI. 
        # Assuming the DB is located where setup_sqlite.py created it.
        db_path = Path(__file__).resolve().parent.parent / 'data' / 'personal_finance' / 'finance.db'
        return SQLDatabase.from_uri(
            f"sqlite:///{db_path}",
            include_tables=['transactions', 'financial_goals', 'monthly_budgets', 'accounts']
        )

    def _clean_sql_output(self, ai_message: AIMessage) -> str:
        # Remove markdown SQL tags
        clean_sql = (ai_message.content
                        .replace("```sql", "")
                        .replace("```", "")
                        .replace("\n", " ")
                        .strip())
        logger.info(f"Generated SQL: {clean_sql}")
        return clean_sql
    
    def _extract_names(self, res: Any) -> List[str]:
        """Hack: Helper to safely extract names from varied LLM outputs (Pydantic, dict, list)."""
        try:
            # Case 1: Pydantic Object
            if hasattr(res, 'names'):
                return res.names
            # Case 2: Dictionary (Raw tool call)
            if isinstance(res, dict):
                if 'args' in res and isinstance(res['args'], dict) and 'names' in res['args']:
                    return res['args']['names']
                if 'names' in res:
                    return res['names']
            # Case 3: List (List of tool calls or objects)
            if isinstance(res, list) and len(res) > 0:
                if hasattr(res[0], 'names'):
                    return res[0].names
                if isinstance(res[0], dict) and 'args' in res[0] and 'names' in res[0]['args']:
                    return res[0]['args']['names']
        except Exception as e:
            logger.warning(f"Error extracting names: {e}")
        return []