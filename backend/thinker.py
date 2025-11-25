
from abc import ABC, abstractmethod
import spacy


class Thinker(ABC):
    def __init__(self, name: str):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None
        self.__name = name
        self.__current_thought = ""
        self.__next_thought = ""

    @abstractmethod
    async def think(self, thought: str) -> str:
        raise NotImplementedError

    def set_current_thought(self, thought: str):
        self.__current_thought = thought

    def get_next_thought(self) -> str:
        return self.__next_thought

    def get_name(self) -> str:
        return self.__name