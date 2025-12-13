
from dataclasses import dataclass
from typing import Any, Optional, Generic, TypeVar

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """
    Railway Oriented Programming: A container for Success or Failure.
    Forces the caller to check for errors, eliminating hidden crashes.
    """
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    
    @classmethod
    def Ok(cls, value: T) -> 'Result[T]':
        return cls(success=True, value=value)

    @classmethod
    def Fail(cls, error: str) -> 'Result[T]':
        return cls(success=False, error=error)

    def unwrap(self) -> T:
        if not self.success:
            raise ValueError(f"Called unwrap on Failure: {self.error}")
        return self.value
