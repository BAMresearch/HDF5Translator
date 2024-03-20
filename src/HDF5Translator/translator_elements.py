import logging
from pathlib import Path
from attrs import define, field
from typing import Optional, Callable, Type
import numpy as np
import builtins


def evaluate_type(name: str) -> Type:
    # do some preformatting on the name to make it easier to match
    name = name.lower().strip()
    if name == "string":
        name = "str"

    if isinstance(getattr(builtins, name, None), type):
        # print(f"found {name=} in builtins")
        return getattr(builtins, name)
    # If it's not in builtins, it's probably a numpy type:
    elif isinstance(getattr(np, name, None), type):
        return getattr(np, name)
    # If it's not in numpy, it's probably a custom type:
    else:
        raise ValueError(name)


@define
class TranslationElement:
    source: str
    destination: str
    data_type: Optional[str | Type] = None
    source_units: Optional[str] = None
    destination_units: Optional[str] = None
    transformation: Optional[Callable] = None
    minimum_dimensionality: Optional[int] = None
    attributes: dict = field(factory=dict)
    default_value: Optional[str | int | float | bool] = None
    compression: Optional[str] = None

    def __attrs_post_init__(self):
        if isinstance(self.data_type, type):
            return  # nothing to do

        if self.data_type is None:
            self.data_type = str
        try:
            self.data_type = evaluate_type(self.data_type)
        except ValueError:
            logging.warning(
                f"Could not convert {self.data_type=} to an actual type, setting to string, but it will probably not work the way you expect"
            )
            self.data_type = str


@define
class LinkElement:
    source_path: str
    destination_path: str
    internal_or_external: str = "internal"
    soft_or_hard_link: str = "soft"
    alternate_source_file: Optional[Path] = None
