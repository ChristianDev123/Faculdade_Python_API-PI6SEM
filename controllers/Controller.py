from abc import ABC, abstractmethod

class Controller(ABC):
    @abstractmethod
    def get_data(self, params:dict):
        return NotImplementedError()
