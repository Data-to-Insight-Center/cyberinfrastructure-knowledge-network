from abc import ABC, abstractmethod

class BaseModel(ABC):
    @abstractmethod
    def pre_process(self, filename):
        """
        Pre-process the input file and return the input in the appropriate tensor format.
        """
        pass

    @abstractmethod
    def predict(self, input):
        """
        Run the model on the pre-processed input and return a prediction and its probability.
        """
        pass
