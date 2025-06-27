"""
LLM Factory for managing different language model implementations.
"""
import google.generativeai as genai
from typing import Dict, Any, Optional, List
from src.utils.config import config


class LLMFactory:
    """Factory class for creating and managing LLM instances."""
    
    _llm_instance = None
    
    @classmethod
    def get_llm(cls):
        """Get singleton LLM instance."""
        if cls._llm_instance is None:
            cls._llm_instance = GeminiLLM()
        return cls._llm_instance


class GeminiLLM:
    """Google Gemini LLM implementation."""
    
    def __init__(self):
        """Initialize Gemini LLM with API key."""
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Gemini LLM")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.LLM_MODEL)
        
        # Generation configuration
        self.generation_config = genai.types.GenerationConfig(
            temperature=config.LLM_TEMPERATURE,
            max_output_tokens=config.LLM_MAX_TOKENS,
        )
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[str] = None,
                         system_prompt: Optional[str] = None) -> str:
        """Generate response using Gemini API."""
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
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
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
