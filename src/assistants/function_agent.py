"""
FunctionAgent - Specialized assistant for function execution and API integrations.
"""
import json
from typing import Dict, Any, Optional, List, Callable
from src.assistants.base_assistant import BaseAssistant
from src.services.llm_factory import LLMFactory


class FunctionAgent(BaseAssistant):
    """Specialized assistant for executing functions and API integrations."""
    
    def __init__(self):
        super().__init__("FunctionAgent")
        self.llm = LLMFactory.get_llm()
        self.available_functions = self._initialize_functions()
        
        # System prompt for function execution
        self.system_prompt = """You are a function execution specialist that runs operations safely based on user needs.
        You can execute predefined functions, transform data formats, and integrate with external services.
        Always validate inputs and provide clear feedback about function execution results."""
    
    def handle_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle function execution requests."""
        try:
            self._update_status("running", 10, "Analyzing function request...")
            
            # Try to extract function call from message
            function_call = self._extract_function_call(message)
            
            if not function_call:
                return self._list_available_functions()
            
            function_name = function_call.get("name")
            if function_name not in self.available_functions:
                return self.report_failure(
                    f"Function '{function_name}' is not available. Use 'list functions' to see available functions."
                )
            
            self._update_status("running", 50, f"Executing function: {function_name}")
            
            # Execute the function
            result = self._execute_function(function_call)
            
            return self.report_success(
                text=result,
                additional_data={
                    "function_name": function_name,
                    "function_parameters": function_call.get("parameters", {})
                }
            )
            
        except Exception as e:
            return self.report_failure(f"Error executing function: {str(e)}")
    
    def _initialize_functions(self) -> Dict[str, Callable]:
        """Initialize available functions."""
        return {
            "get_system_info": self._get_system_info,
            "format_text": self._format_text,
            "calculate": self._calculate,
            "timestamp": self._get_timestamp,
            "uuid_generate": self._generate_uuid,
            "validate_email": self._validate_email,
            "url_encode": self._url_encode,
            "base64_encode": self._base64_encode,
            "base64_decode": self._base64_decode,
            "json_format": self._format_json,
            "list_functions": self._list_available_functions
        }
    
    def _extract_function_call(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract function call from user message."""
        message_lower = message.lower()
        
        # Simple pattern matching for function calls
        for func_name in self.available_functions.keys():
            if func_name in message_lower:
                # Try to extract parameters
                parameters = self._extract_parameters(message, func_name)
                return {
                    "name": func_name,
                    "parameters": parameters
                }
        
        # Check for common function patterns
        if "calculate" in message_lower or "compute" in message_lower:
            return {"name": "calculate", "parameters": {"expression": message}}
        
        if "timestamp" in message_lower or "time" in message_lower:
            return {"name": "timestamp", "parameters": {}}
        
        if "uuid" in message_lower or "id" in message_lower:
            return {"name": "uuid_generate", "parameters": {}}
        
        return None
    
    def _extract_parameters(self, message: str, function_name: str) -> Dict[str, Any]:
        """Extract parameters for a function from the message."""
        # This is a simplified implementation
        # In a real system, you might use more sophisticated NLP
        parameters = {}
        
        if function_name == "format_text":
            # Look for format specifications
            if "uppercase" in message.lower():
                parameters["format"] = "uppercase"
            elif "lowercase" in message.lower():
                parameters["format"] = "lowercase"
            elif "title" in message.lower():
                parameters["format"] = "title"
            
            # Extract text to format (simple approach)
            import re
            quotes = re.findall(r'"([^"]*)"', message)
            if quotes:
                parameters["text"] = quotes[0]
        
        elif function_name == "calculate":
            # Extract mathematical expression
            import re
            # Look for mathematical expressions
            math_pattern = r'[\d\+\-\*\/\(\)\.\s]+'
            matches = re.findall(math_pattern, message)
            if matches:
                parameters["expression"] = matches[0].strip()
        
        return parameters
    
    def _execute_function(self, function_call: Dict[str, Any]) -> str:
        """Execute a function with given parameters."""
        function_name = function_call["name"]
        parameters = function_call.get("parameters", {})
        
        function = self.available_functions[function_name]
        
        try:
            result = function(**parameters)
            return f"Function '{function_name}' executed successfully:\n{result}"
        except Exception as e:
            return f"Error executing function '{function_name}': {str(e)}"
    
    # Available Functions Implementation
    
    def _get_system_info(self) -> str:
        """Get basic system information."""
        import platform
        import psutil
        
        info = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        }
        
        return json.dumps(info, indent=2)
    
    def _format_text(self, text: str = "", format: str = "title") -> str:
        """Format text according to specified format."""
        if not text:
            return "Please provide text to format"
        
        if format == "uppercase":
            return text.upper()
        elif format == "lowercase":
            return text.lower()
        elif format == "title":
            return text.title()
        else:
            return f"Unknown format: {format}"
    
    def _calculate(self, expression: str = "") -> str:
        """Safely calculate mathematical expressions."""
        if not expression:
            return "Please provide a mathematical expression"
        
        try:
            # Simple and safe evaluation
            # Remove any non-mathematical characters
            import re
            safe_expr = re.sub(r'[^0-9\+\-\*\/\(\)\.\s]', '', expression)
            
            if not safe_expr:
                return "Invalid mathematical expression"
            
            result = eval(safe_expr)
            return f"{safe_expr} = {result}"
        except Exception as e:
            return f"Error calculating expression: {str(e)}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _generate_uuid(self) -> str:
        """Generate a UUID."""
        import uuid
        return str(uuid.uuid4())
    
    def _validate_email(self, email: str = "") -> str:
        """Validate email address format."""
        if not email:
            return "Please provide an email address to validate"
        
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        
        return f"Email '{email}' is {'valid' if is_valid else 'invalid'}"
    
    def _url_encode(self, text: str = "") -> str:
        """URL encode text."""
        if not text:
            return "Please provide text to URL encode"
        
        import urllib.parse
        return urllib.parse.quote(text)
    
    def _base64_encode(self, text: str = "") -> str:
        """Base64 encode text."""
        if not text:
            return "Please provide text to encode"
        
        import base64
        encoded = base64.b64encode(text.encode()).decode()
        return encoded
    
    def _base64_decode(self, encoded_text: str = "") -> str:
        """Base64 decode text."""
        if not encoded_text:
            return "Please provide encoded text to decode"
        
        try:
            import base64
            decoded = base64.b64decode(encoded_text).decode()
            return decoded
        except Exception as e:
            return f"Error decoding: {str(e)}"
    
    def _format_json(self, json_text: str = "") -> str:
        """Format JSON text."""
        if not json_text:
            return "Please provide JSON text to format"
        
        try:
            parsed = json.loads(json_text)
            formatted = json.dumps(parsed, indent=2)
            return formatted
        except Exception as e:
            return f"Error formatting JSON: {str(e)}"
    
    def _list_available_functions(self) -> Dict[str, Any]:
        """List all available functions."""
        functions_info = """**Available Functions:**

• **get_system_info** - Get system information
• **format_text** - Format text (uppercase, lowercase, title)
• **calculate** - Perform mathematical calculations
• **timestamp** - Get current timestamp
• **uuid_generate** - Generate a unique identifier
• **validate_email** - Validate email address format
• **url_encode** - URL encode text
• **base64_encode** - Base64 encode text
• **base64_decode** - Base64 decode text
• **json_format** - Format JSON text
• **list_functions** - Show this list

**Usage Examples:**
- "Calculate 2 + 2"
- "Format text 'hello world' to uppercase"
- "Generate a UUID"
- "Get timestamp"
- "Validate email user@example.com"

What function would you like me to execute?"""
        
        return self.report_success(text=functions_info)


# Factory function for creating FunctionAgent instances
def create_function_agent() -> FunctionAgent:
    """Create a new FunctionAgent assistant instance."""
    return FunctionAgent()
