from attrs import define, field
from typing import Optional, Callable

@define
class TranslationElement:
    source: str
    destination: str
    datatype: Optional[str] = None
    source_units: Optional[str] = None
    destination_units: Optional[str] = None
    transformation: Optional[Callable] = None
    minimum_dimensionality: Optional[int] = None
    attributes: dict = field(factory=dict)
    default_value: Optional[str|int|float|bool] = None
    compression: Optional[str] = None

