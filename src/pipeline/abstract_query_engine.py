import json
from pathlib import Path

from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Dict


# This Module has the following:
# Abstract Class which can be used to write pipelines for different backend systems
# Pydantic templates used within the pipeline
# Prompt Repository that manages the LLM prompts (uses app_config.yaml)

class AbstractQueryEngine(ABC):
    """
    Abstract class for Q&A Pipeline, defines the core methods that need to be implemented by any subclass.
    """

    # Constants for constructing prompts
    SYSTEM_MESSAGE = 'system'
    HUMAN_MESSAGE = 'human'

    @abstractmethod
    def ask(self, question: str, verbose: bool = False) -> str:
        """
        Processes a natural language question through the query pipeline and returns the response.
        If `verbose` is set to True, it provides detailed output of each step.
        """
        pass

    @abstractmethod
    def prepare_ner_chain(self) -> Any:
        """
        Step 1: Prepares a Named Entity Recognition chain using prompts and the LLM.
        Returns a chain that processes the input question to identify entities.
        """
        pass

    @abstractmethod
    def map_to_database(self, values: List[str]) -> str:
        """
        Step 2: Matches the provided list of entity names to values in database.
        Returns a formatted string describing the mapping results for each entity.
        """
        pass

    @abstractmethod
    def prepare_db_query_response(self, entity_chain: Any) -> Any:
        """
        Step 3: Prepares the databse query response chain based on the identified entities and database matches.
        It generates a database query and processes it with the LLM.
        """
        pass

    @abstractmethod
    def prepare_response_chain(self, db_query_response: Any) -> Any:
        """
        Step 4: Validates the generated database query response and prepares the final response chain.
        Integrates validation and response generation steps to produce the output.
        """
        pass

    @abstractmethod
    def prepare_app_query_chain(self) -> Any:
        """
        Combines the NER chain, database query generation, and response preparation into one pipeline.
        """
        pass


class PromptRepository:
    """
    Repository for storing and managing LLM prompts used in the pipeline.
    This is a Singleton Class.
    """
    _instance = None

    def __new__(cls, prompts_file: str = None):
        if cls._instance is None:
            cls._instance = super(PromptRepository, cls).__new__(cls)
            cls._instance._initialize(prompts_file)
        return cls._instance

    def _initialize(self, prompts_file: str = None) -> None:
        if prompts_file is None:
            raise ValueError("Prompts File should be passed the first time to initialize the PromptRepository")

        self.prompts = self._load_prompts(prompts_file)

    def get_ner_prompt(self) -> Tuple[str, str]:
        """
        Returns the prompt for Named Entity Recognition
        """
        return self._prepare_prompt('entityRecognition')

    def get_db_prompt(self) -> Tuple[str, str]:
        """
        Returns the prompt used for creating Database Query
        """
        return self._prepare_prompt('dbPrompt')
    def get_response_prompt(self) -> Tuple[str, str]:
        """
        Returns the prompt for generating the final response
        """
        return self._prepare_prompt('responsePrompt')

    def get_chart_insight_prompt(self) -> Tuple[str, str]:
        """
        Returns the prompt for generating chart insights
        """
        return self._prepare_prompt('chartInsight')

    def _load_prompts(self, prompts_file: str = None) -> Dict[str, Any]:
        file_path = Path(__file__).resolve().parent / 'prompts' / prompts_file
        with open(file_path, 'r') as file:
            return json.load(file)

    def _prepare_prompt(self, key: str) -> Tuple[str, str]:
        def _concat(lines: list) -> str:
            return ' \n '.join(lines)

        system = _concat(self.prompts[key]["system"])
        human = _concat(self.prompts[key]["human"])
        return system, human
