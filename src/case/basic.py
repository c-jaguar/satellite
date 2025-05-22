import pathlib
import time
from collections.abc import Callable, Iterable, Iterator
from functools import wraps
from itertools import zip_longest
from typing import Any

from definitions import SOURCE_DIR
from skyfield.api import EarthSatellite


def grouper(iterable: Iterable, n: int, fillvalue: str | None = None) -> Iterator:
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def get_satellites_from_txt(filename: str) -> tuple:
    with open(pathlib.Path(SOURCE_DIR, "tle", filename)) as f:
        return tuple(EarthSatellite(line[1], line[2], line[0].strip()) for line in grouper(f, 3, ""))

def timing(f: Callable) -> Callable:
    @wraps(f)
    def wrap(*args, **kw) -> Any:  # noqa: ANN002, ANN003, ANN401
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print(f"func:{f.__name__!r} args:[{args!r}, {kw!r}] took: {te-ts:2.4f} sec")
        return result
    return wrap
