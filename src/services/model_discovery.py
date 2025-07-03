"""
Model Discovery Service for dynamically finding available Gemini models.
"""
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    # Fallback for when google-generativeai is not available
    genai = None
    GOOGLE_AI_AVAILABLE = False

from typing import List, Dict, Any, Optional
import json
import os

try:
    from src.utils.config import config
except ImportError:
    # Fallback config
    class Config:
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    config = Config()


class ModelDiscoveryService:
    """Service for discovering and managing available Gemini models."""
    
    _instance = None
    _available_models = None
    _models_cache_file = "available_models.json"
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ModelDiscoveryService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the model discovery service."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._load_cached_models()
    
    def discover_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover available Gemini models.
        
        Args:
            force_refresh: If True, bypass cache and query API directly
            
        Returns:
            List of available model information
        """
        if not force_refresh and self._available_models is not None:
            return self._available_models
        
        # Check if Google AI library is available
        if not GOOGLE_AI_AVAILABLE:
            print("Google Generative AI library not available - using default model list")
            return self._get_default_models()
        
        try:
            if not config.GEMINI_API_KEY:
                print("No Gemini API key configured - using default model list")
                return self._get_default_models()
            
            # Configure API
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Query available models
            print("Querying Gemini API for available models...")
            models = []
            
            try:
                # List all available models
                available_models = genai.list_models()
                
                for model in available_models:
                    # Only include generative models
                    if 'generateContent' in model.supported_generation_methods:
                        model_info = {
                            'name': model.name,
                            'display_name': model.display_name,
                            'description': getattr(model, 'description', ''),
                            'supported_methods': model.supported_generation_methods,
                            'input_token_limit': getattr(model, 'input_token_limit', None),
                            'output_token_limit': getattr(model, 'output_token_limit', None)
                        }
                        models.append(model_info)
                        
                print(f"Found {len(models)} available generative models")
                
            except Exception as e:
                print(f"Error querying Gemini API: {e}")
                return self._get_default_models()
            
            # Cache the results
            self._available_models = models
            self._cache_models(models)
            
            return models
            
        except Exception as e:
            print(f"Error discovering models: {e}")
            return self._get_default_models()
    
    def get_best_model(self, task_type: str = "general") -> str:
        """
        Get the best available model for a specific task type.
        
        Args:
            task_type: Type of task ("general", "code", "conversation", etc.)
            
        Returns:
            Model name to use
        """
        models = self.discover_available_models()
        
        if not models:
            return "gemini-1.5-flash"  # Fallback
        
        # Define preferences based on task type
        task_preferences = {
            "general": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            "code": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            "conversation": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
            "analysis": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        }
        
        preferred_models = task_preferences.get(task_type, task_preferences["general"])
        available_model_names = [m['name'] for m in models]
        
        # Find the first preferred model that's available
        for preferred in preferred_models:
            for available_name in available_model_names:
                if preferred in available_name:
                    print(f"Selected model '{available_name}' for task type '{task_type}'")
                    return available_name
        
        # If no preferred model found, use the first available model
        if available_model_names:
            selected = available_model_names[0]
            print(f"Using first available model '{selected}' for task type '{task_type}'")
            return selected
        
        # Final fallback
        return "gemini-1.5-flash"
    
    def validate_model(self, model_name: str) -> bool:
        """
        Validate if a model is available.
        
        Args:
            model_name: Name of the model to validate
            
        Returns:
            True if model is available, False otherwise
        """
        models = self.discover_available_models()
        available_names = [m['name'] for m in models]
        
        # Check exact match or partial match
        for name in available_names:
            if model_name == name or model_name in name:
                return True
        
        return False
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        models = self.discover_available_models()
        
        for model in models:
            if model_name == model['name'] or model_name in model['name']:
                return model
        
        return None
    
    def list_available_models(self) -> List[str]:
        """Get a simple list of available model names."""
        models = self.discover_available_models()
        return [m['name'] for m in models]
    
    def _get_default_models(self) -> List[Dict[str, Any]]:
        """Get default model list when API is not available."""
        return [
            {
                'name': 'models/gemini-1.5-flash',
                'display_name': 'Gemini 1.5 Flash',
                'description': 'Fast and efficient model for general tasks',
                'supported_methods': ['generateContent'],
                'input_token_limit': 1000000,
                'output_token_limit': 8192
            },
            {
                'name': 'models/gemini-1.5-pro',
                'display_name': 'Gemini 1.5 Pro',
                'description': 'Most capable model for complex tasks',
                'supported_methods': ['generateContent'],
                'input_token_limit': 2000000,
                'output_token_limit': 8192
            },
            {
                'name': 'models/gemini-pro',
                'display_name': 'Gemini Pro',
                'description': 'Previous generation model',
                'supported_methods': ['generateContent'],
                'input_token_limit': 30720,
                'output_token_limit': 2048
            }
        ]
    
    def _cache_models(self, models: List[Dict[str, Any]]):
        """Cache models to file for faster loading."""
        try:
            cache_path = os.path.join(".", self._models_cache_file)
            with open(cache_path, 'w') as f:
                json.dump({
                    'models': models,
                    'timestamp': __import__('time').time()
                }, f, indent=2)
            print(f"Cached {len(models)} models to {cache_path}")
        except Exception as e:
            print(f"Error caching models: {e}")
    
    def _load_cached_models(self):
        """Load models from cache if available and not too old."""
        try:
            cache_path = os.path.join(".", self._models_cache_file)
            if not os.path.exists(cache_path):
                return
            
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Check if cache is less than 24 hours old
            cache_age = __import__('time').time() - data.get('timestamp', 0)
            if cache_age < 24 * 3600:  # 24 hours
                self._available_models = data.get('models', [])
                print(f"Loaded {len(self._available_models)} models from cache")
            else:
                print("Model cache is too old, will refresh")
                
        except Exception as e:
            print(f"Error loading cached models: {e}")


def get_model_discovery_service() -> ModelDiscoveryService:
    """Get singleton model discovery service instance."""
    return ModelDiscoveryService()
