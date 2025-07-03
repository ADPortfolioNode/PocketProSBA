"""
LLM Factory for managing different language model implementations.
"""
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    # Fallback for when google-generativeai is not available
    genai = None
    GOOGLE_AI_AVAILABLE = False

from typing import Dict, Any, Optional, List

try:
    from src.utils.config import config
except ImportError:
    # Fallback config
    class Config:
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    config = Config()

try:
    from src.services.model_discovery import get_model_discovery_service
except ImportError:
    # Fallback when model discovery is not available
    def get_model_discovery_service():
        return None


class LLMFactory:
    """Factory class for creating and managing LLM instances."""
    
    _llm_instance = None
    
    @classmethod
    def get_llm(cls):
        """Get singleton LLM instance."""
        if cls._llm_instance is None:
            if GOOGLE_AI_AVAILABLE:
                cls._llm_instance = GeminiLLM()
            else:
                cls._llm_instance = MockLLM()
        return cls._llm_instance
    
    @classmethod
    def refresh_available_models(cls):
        """Refresh the list of available models."""
        if not GOOGLE_AI_AVAILABLE:
            print("Google AI not available - using mock models")
            return [{"name": "mock-model", "display_name": "Mock Model"}]
            
        model_service = get_model_discovery_service()
        if not model_service:
            return [{"name": "mock-model", "display_name": "Mock Model"}]
            
        models = model_service.discover_available_models(force_refresh=True)
        print(f"Refreshed model list: {len(models)} models available")
        return models
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """Get list of available model names."""
        if not GOOGLE_AI_AVAILABLE:
            return ["mock-model"]
            
        model_service = get_model_discovery_service()
        if not model_service:
            return ["mock-model"]
            
        return model_service.list_available_models()


class GeminiLLM:
    """Google Gemini LLM implementation with dynamic model selection."""
    
    def __init__(self):
        """Initialize Gemini LLM with API key and model discovery."""
        if not GOOGLE_AI_AVAILABLE:
            raise ValueError("Google Generative AI library is not available")
            
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Gemini LLM")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Use model discovery service to find the best available model
        self.model_service = get_model_discovery_service()
        self._initialize_model()
        
        # Generation configuration with fallbacks
        try:
            self.generation_config = genai.types.GenerationConfig(
                temperature=getattr(config, 'LLM_TEMPERATURE', 0.7),
                max_output_tokens=getattr(config, 'LLM_MAX_TOKENS', 1024),
            )
        except Exception:
            # Simple fallback config
            self.generation_config = None
    
    def _initialize_model(self):
        """Initialize the model using the best available option."""
        try:
            # First, validate the configured model if available
            configured_model = getattr(config, 'LLM_MODEL', 'gemini-pro')
            
            if self.model_service and hasattr(self.model_service, 'validate_model') and self.model_service.validate_model(configured_model):
                model_name = configured_model
                print(f"Using configured model: {model_name}")
            else:
                if self.model_service and hasattr(self.model_service, 'get_best_model'):
                    model_name = self.model_service.get_best_model("general")
                else:
                    model_name = "gemini-pro"  # Fallback default
                print(f"Using best available model: {model_name}")
            
            # Ensure model name has proper format
            if not model_name.startswith('models/'):
                if '/' not in model_name:
                    model_name = f"models/{model_name}"
            
            self.model_name = model_name
            self.model = genai.GenerativeModel(model_name)
            
            # Log model info if available
            if self.model_service and hasattr(self.model_service, 'get_model_info'):
                model_info = self.model_service.get_model_info(model_name)
                if model_info:
                    print(f"Model initialized: {model_info.get('display_name', model_name)}")
                    print(f"  Description: {model_info.get('description', 'N/A')}")
                    print(f"  Input limit: {model_info.get('input_token_limit', 'N/A')} tokens")
                print(f"  Output limit: {model_info.get('output_token_limit', 'N/A')} tokens")
            
        except Exception as e:
            print(f"Error initializing model: {e}")
            # Fallback to a known working model
            fallback_model = "models/gemini-1.5-flash"
            print(f"Falling back to: {fallback_model}")
            self.model_name = fallback_model
            self.model = genai.GenerativeModel(fallback_model)
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[str] = None,
                         system_prompt: Optional[str] = None) -> str:
        """Generate response using Gemini API."""
        full_prompt = ""  # Initialize to avoid unbound variable
        try:
            # Construct full prompt
            full_prompt = self._construct_prompt(prompt, context, system_prompt)
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating response with Gemini: {e}")
            print(f"Error type: {type(e)}")
            if full_prompt:
                print(f"Full prompt was: {full_prompt[:200]}...")
            return f"I apologize, but I encountered an error while processing your request. Error details: {str(e)}"
    
    def classify_intent(self, message: str, conversation_history: Optional[List] = None) -> str:
        """Classify user message intent."""
        classification_prompt = f"""
        Classify the following user message into one of these categories:
        - simple_query: Direct question that can be answered conversationally
        - document_search: Request to find information in documents
        - task_request: Multi-step task requiring decomposition
        - clarification: User asking for clarification or followup
        - feedback: User providing feedback on previous response
        - meta: Question about the system itself
        
        Message: "{message}"
        
        Return only the category name, nothing else.
        """
        
        try:
            response = self.model.generate_content(classification_prompt)
            return response.text.strip().lower()
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "simple_query"  # Default fallback
    
    def decompose_task(self, task_description: str) -> Dict[str, Any]:
        """Decompose a complex task into steps."""
        decomposition_prompt = f"""
        Break down the following task into clear, actionable steps. 
        For each step, specify the suggested agent type (SearchAgent, FileAgent, or FunctionAgent).
        
        Task: "{task_description}"
        
        Return a JSON object with this structure:
        {{
            "steps": [
                {{
                    "step_number": 1,
                    "instruction": "Clear instruction for the step",
                    "suggested_agent_type": "SearchAgent|FileAgent|FunctionAgent"
                }}
            ]
        }}
        
        Only return valid JSON, nothing else.
        """
        
        try:
            response = self.model.generate_content(decomposition_prompt)
            import json
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"Error decomposing task: {e}")
            return {
                "steps": [{
                    "step_number": 1,
                    "instruction": task_description,
                    "suggested_agent_type": "SearchAgent"
                }]
            }
    
    def _construct_prompt(self, 
                         prompt: str, 
                         context: Optional[str] = None,
                         system_prompt: Optional[str] = None) -> str:
        """Construct full prompt with context and system instructions."""
        parts = []
        
        if system_prompt:
            parts.append(f"SYSTEM: {system_prompt}")
        
        if context:
            parts.append(f"CONTEXT: {context}")
        
        parts.append(f"USER: {prompt}")
        
        return "\n\n".join(parts)


class MockLLM:
    """Mock LLM implementation when Google AI is not available."""
    
    def __init__(self):
        """Initialize mock LLM."""
        self.model = None
        print("MockLLM initialized - Google AI not available")
    
    def generate(self, prompt: str, context: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Mock generate method."""
        return {
            "response": "AI services are temporarily unavailable. Google Generative AI library is not installed.",
            "model": "mock-model",
            "usage": {"tokens": 0},
            "error": "Google AI library not available"
        }
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Mock chat method."""
        return {
            "response": "Chat services are temporarily unavailable. Google Generative AI library is not installed.",
            "model": "mock-model",
            "usage": {"tokens": 0},
            "error": "Google AI library not available"
        }
    
    def decompose_task(self, task_description: str) -> Dict[str, Any]:
        """Mock task decomposition."""
        return {
            "steps": [{
                "step_number": 1,
                "instruction": f"Task decomposition unavailable: {task_description}",
                "suggested_agent_type": "SearchAgent"
            }]
        }
