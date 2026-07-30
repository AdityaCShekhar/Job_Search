import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def with_retries(operation: Callable[[], T], attempts: int = 3) -> T:
    last_error = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as error:  # network clients commonly expose varied exceptions
            last_error = error
            if attempt + 1 == attempts:
                break
            time.sleep(2**attempt)
    raise last_error  # type: ignore[misc]

