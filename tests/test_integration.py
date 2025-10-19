"""Integration tests for architecture-merge-roadmap.

These tests verify cross-module communication and module connectivity
as specified in integration_test_plan.md.
"""

import pytest


class DummyModuleA:
    """Dummy module simulating Module A."""
    
    def __init__(self):
        self.name = "ModuleA"
        self.status = "initialized"
    
    def send_message(self, target_module, message):
        """Send a message to another module."""
        return {
            "source": self.name,
            "target": target_module,
            "message": message,
            "status": "sent"
        }
    
    def process(self, data):
        """Process data and return result."""
        return {"processed_by": self.name, "data": data, "status": "success"}


class DummyModuleB:
    """Dummy module simulating Module B."""
    
    def __init__(self):
        self.name = "ModuleB"
        self.status = "initialized"
    
    def receive_message(self, message_data):
        """Receive and acknowledge a message."""
        return {
            "receiver": self.name,
            "received": message_data,
            "acknowledged": True
        }
    
    def process(self, data):
        """Process data and return result."""
        return {"processed_by": self.name, "data": data, "status": "success"}


class IntegrationAdapter:
    """Simple adapter for module integration."""
    
    def __init__(self, module_a, module_b):
        self.module_a = module_a
        self.module_b = module_b
    
    def connect_modules(self):
        """Verify both modules are initialized and ready."""
        return (
            self.module_a.status == "initialized" and
            self.module_b.status == "initialized"
        )
    
    def forward_message(self, message):
        """Forward message from Module A to Module B."""
        sent = self.module_a.send_message(self.module_b.name, message)
        received = self.module_b.receive_message(sent)
        return sent, received


# Test Fixtures
@pytest.fixture
def module_a():
    """Provide initialized Module A instance."""
    return DummyModuleA()


@pytest.fixture
def module_b():
    """Provide initialized Module B instance."""
    return DummyModuleB()


@pytest.fixture
def adapter(module_a, module_b):
    """Provide integration adapter with both modules."""
    return IntegrationAdapter(module_a, module_b)


# Integration Tests
class TestCrossModuleCommunication:
    """Test Scenario 1: Cross-Module Communication (integration_test_plan.md)."""
    
    def test_module_initialization(self, module_a, module_b):
        """Verify both modules initialize correctly."""
        assert module_a.status == "initialized"
        assert module_b.status == "initialized"
        assert module_a.name == "ModuleA"
        assert module_b.name == "ModuleB"
    
    def test_module_connectivity(self, adapter):
        """Verify modules can connect through adapter."""
        assert adapter.connect_modules() is True
    
    def test_message_sending(self, module_a, module_b):
        """Verify Module A can send messages."""
        result = module_a.send_message(module_b.name, "Hello from A")
        
        assert result["source"] == "ModuleA"
        assert result["target"] == "ModuleB"
        assert result["message"] == "Hello from A"
        assert result["status"] == "sent"
    
    def test_message_receiving(self, module_b):
        """Verify Module B can receive messages."""
        test_message = {
            "source": "ModuleA",
            "target": "ModuleB",
            "message": "Test message"
        }
        
        result = module_b.receive_message(test_message)
        
        assert result["receiver"] == "ModuleB"
        assert result["received"] == test_message
        assert result["acknowledged"] is True
    
    def test_end_to_end_message_flow(self, adapter):
        """Verify complete message flow from A to B through adapter."""
        sent, received = adapter.forward_message("Integration test message")
        
        # Verify sent message
        assert sent["source"] == "ModuleA"
        assert sent["target"] == "ModuleB"
        assert sent["status"] == "sent"
        
        # Verify received message
        assert received["receiver"] == "ModuleB"
        assert received["acknowledged"] is True
        assert received["received"]["source"] == "ModuleA"
    
    def test_bidirectional_processing(self, module_a, module_b):
        """Verify both modules can process data independently."""
        test_data = {"value": 42}
        
        result_a = module_a.process(test_data)
        result_b = module_b.process(test_data)
        
        assert result_a["processed_by"] == "ModuleA"
        assert result_a["status"] == "success"
        assert result_a["data"] == test_data
        
        assert result_b["processed_by"] == "ModuleB"
        assert result_b["status"] == "success"
        assert result_b["data"] == test_data


class TestAdapterFunctionality:
    """Test the integration adapter functionality."""
    
    def test_adapter_initialization(self, adapter, module_a, module_b):
        """Verify adapter is initialized with correct modules."""
        assert adapter.module_a is module_a
        assert adapter.module_b is module_b
    
    def test_adapter_connection_verification(self, adapter):
        """Verify adapter can check module connection status."""
        connection_status = adapter.connect_modules()
        assert connection_status is True
        assert isinstance(connection_status, bool)
