import logging
from pathlib import Path
from attrs import define, field
from typing import Optional, Callable, Type

def evaluate_type(name: str):
    t = globals().get(name)
    if t:
        return t
    else:
        try:
            t = getattr(__builtins__, name)
            if isinstance(t, type):
                return t
            else:
                raise ValueError(name)
        except:
            raise ValueError(name)

@define
class TranslationElement:
    source: str
    destination: str
    data_type: Optional[str|Type] = None
    source_units: Optional[str] = None
    destination_units: Optional[str] = None
    transformation: Optional[Callable] = None
    minimum_dimensionality: Optional[int] = None
    attributes: dict = field(factory=dict)
    default_value: Optional[str|int|float|bool] = None
    compression: Optional[str] = None

    def __attrs_post_init__(self):
        try: 
            self.data_type = evaluate_type(self.data_type)
        except ValueError:
            logging.warning(f'Could not convert {self.data_type=} to an actual type, setting to string, but it will probably not work the way you expect')
            self.data_type=str
        except:
            raise

@define
class LinkElement:
    source_path: str
    destination_path: str
    internal_or_external: str = 'internal'
    soft_or_hard_link: str = "soft"
    alternate_source_file: Optional[Path] = None