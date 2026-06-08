from enum import Enum
from typing import NamedTuple

class DuplicateRemoveMode(Enum):
    NONE = -1
    OLDEST = 0
    NEWEST = 1
    UPDATE = 2

class AnkiConfig(NamedTuple):
    col_path: str
    dupl_resolve: DuplicateRemoveMode
