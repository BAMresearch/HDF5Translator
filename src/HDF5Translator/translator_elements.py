from pathlib import Path
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

@define
class LinkElement:
    source_path: str
    destination_path: str
    internal_or_external: str = 'internal'
    soft_or_hard_link: str = "soft"
    alternate_source_file: Optional[Path] = None