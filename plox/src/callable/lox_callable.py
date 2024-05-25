from abc import ABC, abstractmethod


class LoxCallable(ABC):
    @abstractmethod
    def arity(self):
        raise NotImplementedError

    @abstractmethod
    def call(self, interpreter, arguments):
        raise NotImplementedError

    @abstractmethod
    def __str__(self):
        raise NotImplementedError
