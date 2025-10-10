from abc import abstractmethod
from typing import Any
from hyperpipe_core import Step
from ..models import GraphBuilderResult
import logging


class Exporter(Step):
    """Base class for all data exporters in hyperpipe"""
    
    def __init__(self, name: str = None, logger: logging.Logger = None):
        self.name = name or self.__class__.__name__
        self._logger = logger
    
    def execute(self, input_data: GraphBuilderResult) -> None:
        """Execute the data exporting step"""
        
        # Extract data to export from result
        data_to_export = self._extract_data(input_data)
        
        # Perform the actual export
        self._export_data(data_to_export)
        
    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult) -> None:
        pass
    
    @abstractmethod
    def _extract_data(self, result: GraphBuilderResult) -> Any:
        """Extract data to export from the pipeline result"""
        raise NotImplementedError
    
    @abstractmethod
    def _export_data(self, data: Any) -> int:
        """Export data, return count of exported items"""
        raise NotImplementedError 