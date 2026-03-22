"""
base_extractor.py
-----------------
Defines the contract every extractor must follow:
  - Receives a file path on construction
  - Exposes a single public method: extract() → pd.DataFrame

All specific extractors inherit from this class and implement extract().
This keeps the pipeline code simple: it can treat every extractor the same way.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class BaseExtractor(ABC):
    """
    Abstract base for all data source extractors.

    Each subclass is responsible for exactly one data source and must:
      1. Accept the file path in __init__
      2. Return a clean, flat pd.DataFrame from extract()
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """
        Load and clean the source file.
        Returns a flat pd.DataFrame ready for merging or analysis.
        """
        raise NotImplementedError
