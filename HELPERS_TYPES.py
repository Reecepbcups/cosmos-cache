from enum import Enum


class Mode(Enum):
    NO_CACHE = 0
    DISABLED = -1
    FOR_BLOCK_TIME = -2
