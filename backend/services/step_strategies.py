"""
Step Strategies Service

Implements the Strategy Pattern for different approaches to executing task steps.
"""

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class StepStrategy(ABC):
    """Abstract base class for step execution strategies"""

    @abstractmethod
    def execute(self, step) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

class DefaultStrategy(StepStrategy):
    """Default strategy for step execution"""

    @property
    def name(self) -> str:
        return "default"

    def execute(self, step) -> Dict[str, Any]:
        """Execute step using default approach"""
        try:
            from services.api_service import execute_step_service
            result = execute_step_service(step.data)
            return {
                'success': result.get('success', False),
                'data': result.get('data', {}),
                'error': result.get('error')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ConservativeStrategy(StepStrategy):
    """Conservative strategy with extra validation"""

    @property
    def name(self) -> str:
        return "conservative"

    def execute(self, step) -> Dict[str, Any]:
        """Execute step with conservative approach"""
        try:
            from services.api_service import execute_step_service
            result = execute_step_service(step.data)
            return {
                'success': result.get('success', False),
                'data': result.get('data', {}),
                'error': result.get('error')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

class AggressiveStrategy(StepStrategy):
    """Aggressive strategy optimized for speed"""

    @property
    def name(self) -> str:
        return "aggressive"

    def execute(self, step) -> Dict[str, Any]:
        """Execute step with aggressive approach"""
        try:
            from services.api_service import execute_step_service
            result = execute_step_service(step.data)
            return {
                'success': result.get('success', False),
                'data': result.get('data', {}),
                'error': result.get('error')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

class StepStrategyFactory:
    """Factory for creating step strategy instances"""

    _strategies = {
        'default': DefaultStrategy,
        'conservative': ConservativeStrategy,
        'aggressive': AggressiveStrategy
    }

    @classmethod
    def get_strategy(cls, strategy_name: str) -> StepStrategy:
        strategy_class = cls._strategies.get(strategy_name, cls._strategies['default'])
        return strategy_class()

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())
