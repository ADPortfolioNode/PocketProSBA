import pytest
from app.services.base_assistant import BaseAssistant
from app.services.concierge import Concierge

def test_base_assistant():
    """Test the BaseAssistant class."""
    assistant = BaseAssistant("TestAssistant")
    assert assistant.name == "TestAssistant"
    assert assistant.status == "idle"

def test_concierge_initialization():
    """Test the Concierge initialization."""
    concierge = Concierge()
    assert concierge.name == "Concierge"
    assert hasattr(concierge, 'llm')
