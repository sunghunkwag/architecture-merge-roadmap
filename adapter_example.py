"""Python Adapter Class for API Bridging

This module demonstrates a realistic adapter pattern implementation that bridges
two different agent APIs. It shows data translation, method adaptation, and
error handling between the legacy AgentAPI and modern AgentAPI v2.

Author: Architecture Integration Team
Date: October 2025
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegacyAgentAPI:
    """Simulates a legacy agent API with old-style methods and data structures."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://legacy-api.example.com"
        logger.info(f"Initialized LegacyAgentAPI with base URL: {self.base_url}")
    
    def execute_task(self, task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using legacy format.
        
        Args:
            task_id: Unique identifier for the task
            params: Dictionary with keys: 'action', 'priority', 'data'
            
        Returns:
            Dict with keys: 'status', 'result_code', 'output', 'timestamp'
        """
        logger.info(f"Executing legacy task: {task_id}")
        return {
            "status": "completed",
            "result_code": 200,
            "output": f"Task {task_id} executed with action {params.get('action')}",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_status(self, task_id: str) -> str:
        """Get task status in legacy format (simple string)."""
        return "RUNNING|COMPLETED|FAILED"


class ModernAgentAPI:
    """Simulates a modern agent API with updated methods and data structures."""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.endpoint = "https://api-v2.example.com"
        logger.info(f"Initialized ModernAgentAPI with endpoint: {self.endpoint}")
    
    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a job using modern format.
        
        Args:
            job: Dictionary with keys: 'id', 'type', 'priority', 'payload', 'metadata'
            
        Returns:
            Dict with keys: 'success', 'code', 'data', 'created_at', 'completed_at'
        """
        logger.info(f"Running modern job: {job.get('id')}")
        return {
            "success": True,
            "code": 200,
            "data": {
                "job_id": job.get("id"),
                "result": f"Job {job.get('id')} processed successfully",
                "metrics": {"duration_ms": 150, "cpu_usage": 0.45}
            },
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
    
    def query_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status in modern format (structured object)."""
        return {
            "job_id": job_id,
            "state": "processing",
            "progress": 0.75,
            "message": "Job in progress"
        }


class AgentAPIAdapter:
    """Adapter class that bridges LegacyAgentAPI to ModernAgentAPI interface.
    
    This adapter allows clients expecting the modern API to work seamlessly
    with the legacy system by translating data structures and method calls.
    
    Design Pattern: Adapter (Wrapper)
    Purpose: Provide interface compatibility between two incompatible APIs
    """
    
    def __init__(self, legacy_api: LegacyAgentAPI):
        """Initialize adapter with legacy API instance.
        
        Args:
            legacy_api: Instance of LegacyAgentAPI to be adapted
        """
        self.legacy_api = legacy_api
        self._job_task_mapping = {}  # Maps modern job IDs to legacy task IDs
        logger.info("AgentAPIAdapter initialized successfully")
    
    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt modern 'run' method to legacy 'execute_task'.
        
        Translates the modern job format to legacy task format and converts
        the response back to modern format.
        
        Args:
            job: Modern job dictionary with structure:
                {
                    'id': str,
                    'type': str,
                    'priority': int,
                    'payload': dict,
                    'metadata': dict
                }
                
        Returns:
            Modern response dictionary with structure:
                {
                    'success': bool,
                    'code': int,
                    'data': dict,
                    'created_at': str,
                    'completed_at': str
                }
        """
        job_id = job.get("id", "unknown")
        logger.info(f"Adapting modern job {job_id} to legacy task")
        
        # Step 1: Translate modern job format to legacy task format
        legacy_params = self._translate_job_to_task(job)
        
        # Store mapping for status queries
        self._job_task_mapping[job_id] = job_id
        
        # Step 2: Call legacy API
        try:
            legacy_response = self.legacy_api.execute_task(job_id, legacy_params)
        except Exception as e:
            logger.error(f"Legacy API call failed: {str(e)}")
            return self._create_error_response(job_id, str(e))
        
        # Step 3: Translate legacy response to modern format
        modern_response = self._translate_task_result_to_job(legacy_response, job_id)
        
        logger.info(f"Successfully adapted job {job_id}")
        return modern_response
    
    def query_status(self, job_id: str) -> Dict[str, Any]:
        """Adapt modern 'query_status' to legacy 'get_status'.
        
        Args:
            job_id: Modern job identifier
            
        Returns:
            Modern status dictionary with detailed structure
        """
        logger.info(f"Querying status for job {job_id}")
        
        # Get corresponding task ID
        task_id = self._job_task_mapping.get(job_id, job_id)
        
        try:
            # Call legacy status method
            legacy_status = self.legacy_api.get_status(task_id)
            
            # Translate legacy status string to modern status object
            modern_status = self._translate_status(legacy_status, job_id)
            
            return modern_status
        except Exception as e:
            logger.error(f"Status query failed: {str(e)}")
            return {
                "job_id": job_id,
                "state": "error",
                "progress": 0.0,
                "message": f"Failed to query status: {str(e)}"
            }
    
    def _translate_job_to_task(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Translate modern job structure to legacy task parameters.
        
        Args:
            job: Modern job dictionary
            
        Returns:
            Legacy task parameters dictionary
        """
        return {
            "action": job.get("type", "default_action"),
            "priority": job.get("priority", 5),
            "data": json.dumps({
                "payload": job.get("payload", {}),
                "metadata": job.get("metadata", {})
            })
        }
    
    def _translate_task_result_to_job(self, legacy_result: Dict[str, Any], 
                                       job_id: str) -> Dict[str, Any]:
        """Translate legacy task result to modern job response.
        
        Args:
            legacy_result: Legacy API response
            job_id: Modern job identifier
            
        Returns:
            Modern job response dictionary
        """
        # Map legacy result_code to success boolean
        success = legacy_result.get("result_code", 500) == 200
        
        return {
            "success": success,
            "code": legacy_result.get("result_code", 500),
            "data": {
                "job_id": job_id,
                "result": legacy_result.get("output", "No output"),
                "metrics": {
                    "duration_ms": 0,  # Legacy API doesn't provide this
                    "cpu_usage": 0.0   # Legacy API doesn't provide this
                }
            },
            "created_at": legacy_result.get("timestamp", datetime.now().isoformat()),
            "completed_at": datetime.now().isoformat()
        }
    
    def _translate_status(self, legacy_status: str, job_id: str) -> Dict[str, Any]:
        """Translate legacy status string to modern status object.
        
        Args:
            legacy_status: Pipe-separated status string from legacy API
            job_id: Modern job identifier
            
        Returns:
            Modern status dictionary
        """
        # Legacy returns "RUNNING|COMPLETED|FAILED" format
        status_map = {
            "RUNNING": ("processing", 0.5),
            "COMPLETED": ("completed", 1.0),
            "FAILED": ("failed", 0.0)
        }
        
        # Parse first status from pipe-separated string
        first_status = legacy_status.split("|")[0] if "|" in legacy_status else legacy_status
        state, progress = status_map.get(first_status, ("unknown", 0.0))
        
        return {
            "job_id": job_id,
            "state": state,
            "progress": progress,
            "message": f"Job {state}"
        }
    
    def _create_error_response(self, job_id: str, error_msg: str) -> Dict[str, Any]:
        """Create a standardized error response in modern format.
        
        Args:
            job_id: Job identifier
            error_msg: Error message
            
        Returns:
            Modern error response dictionary
        """
        return {
            "success": False,
            "code": 500,
            "data": {
                "job_id": job_id,
                "result": f"Error: {error_msg}",
                "metrics": {"duration_ms": 0, "cpu_usage": 0.0}
            },
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }


# Example usage demonstration
if __name__ == "__main__":
    print("=" * 70)
    print("Agent API Adapter Example")
    print("=" * 70)
    
    # Initialize legacy API
    legacy_api = LegacyAgentAPI(api_key="legacy_key_12345")
    
    # Create adapter
    adapter = AgentAPIAdapter(legacy_api)
    
    # Create a modern-style job
    modern_job = {
        "id": "job_2025_001",
        "type": "data_processing",
        "priority": 3,
        "payload": {
            "input_file": "data.csv",
            "operations": ["filter", "transform", "aggregate"]
        },
        "metadata": {
            "user": "admin",
            "department": "analytics"
        }
    }
    
    # Execute job through adapter (which uses legacy API internally)
    print("\nExecuting modern job through adapter...")
    result = adapter.run(modern_job)
    print("\nModern API Response:")
    print(json.dumps(result, indent=2))
    
    # Query job status
    print("\nQuerying job status...")
    status = adapter.query_status("job_2025_001")
    print("\nStatus Response:")
    print(json.dumps(status, indent=2))
    
    print("\n" + "=" * 70)
    print("Adapter successfully bridged legacy API to modern interface!")
    print("=" * 70)
