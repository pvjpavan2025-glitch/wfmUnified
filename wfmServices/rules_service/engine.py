"""
Core rules engine logic for WFM.
"""
from typing import Dict, Any, List, Optional
import json
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class RulesEngine:
    """Core rules engine for evaluating business rules."""
    
    def __init__(self):
        self.operators = {
            "eq": self._equals,
            "ne": self._not_equals,
            "gt": self._greater_than,
            "lt": self._less_than,
            "gte": self._greater_than_or_equal,
            "lte": self._less_than_or_equal,
            "in": self._in_list,
            "not_in": self._not_in_list,
            "contains": self._contains,
            "not_contains": self._not_contains,
            "regex": self._regex_match,
            "exists": self._exists,
            "not_exists": self._not_exists
        }
    
    def evaluate_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate a single condition against data."""
        try:
            field = condition.get("field")
            operator = condition.get("operator", "eq")
            value = condition.get("value")
            
            if field not in data:
                return operator in ["not_exists"]
            
            field_value = data[field]
            
            if operator in self.operators:
                return self.operators[operator](field_value, value)
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    def evaluate_conditions(self, conditions: List[Dict[str, Any]], data: Dict[str, Any]) -> bool:
        """Evaluate multiple conditions with AND/OR logic."""
        try:
            if not conditions:
                return True
            
            # Simple AND logic for now
            for condition in conditions:
                if not self.evaluate_condition(condition, data):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {str(e)}")
            return False
    
    def _equals(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value equals expected value."""
        return field_value == expected_value
    
    def _not_equals(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value does not equal expected value."""
        return field_value != expected_value
    
    def _greater_than(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value is greater than expected value."""
        try:
            return float(field_value) > float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _less_than(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value is less than expected value."""
        try:
            return float(field_value) < float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _greater_than_or_equal(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value is greater than or equal to expected value."""
        try:
            return float(field_value) >= float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _less_than_or_equal(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value is less than or equal to expected value."""
        try:
            return float(field_value) <= float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _in_list(self, field_value: Any, expected_values: List[Any]) -> bool:
        """Check if field value is in the expected list."""
        return field_value in expected_values
    
    def _not_in_list(self, field_value: Any, expected_values: List[Any]) -> bool:
        """Check if field value is not in the expected list."""
        return field_value not in expected_values
    
    def _contains(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value contains expected value."""
        if isinstance(field_value, str) and isinstance(expected_value, str):
            return expected_value in field_value
        return False
    
    def _not_contains(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field value does not contain expected value."""
        if isinstance(field_value, str) and isinstance(expected_value, str):
            return expected_value not in field_value
        return True
    
    def _regex_match(self, field_value: Any, pattern: str) -> bool:
        """Check if field value matches regex pattern."""
        import re
        if isinstance(field_value, str):
            try:
                return bool(re.search(pattern, field_value))
            except re.error:
                return False
        return False
    
    def _exists(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field exists and has a value."""
        return field_value is not None and field_value != ""
    
    def _not_exists(self, field_value: Any, expected_value: Any) -> bool:
        """Check if field does not exist or has no value."""
        return field_value is None or field_value == ""


class ActionExecutor:
    """Execute actions based on rule evaluation results."""
    
    def __init__(self):
        self.action_handlers = {
            "send_notification": self._send_notification,
            "create_task": self._create_task,
            "update_status": self._update_status,
            "log_event": self._log_event,
            "call_api": self._call_api
        }
    
    def execute_action(self, action: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action."""
        try:
            action_type = action.get("type")
            action_params = action.get("params", {})
            
            if action_type in self.action_handlers:
                result = self.action_handlers[action_type](action_params, data)
                return {
                    "type": action_type,
                    "params": action_params,
                    "result": result,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return {
                    "type": action_type,
                    "params": action_params,
                    "status": "unknown_action",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error executing action {action.get('type', 'unknown')}: {str(e)}")
            return {
                "type": action.get("type", "unknown"),
                "params": action.get("params", {}),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def execute_actions(self, actions: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute multiple actions."""
        results = []
        for action in actions:
            result = self.execute_action(action, data)
            results.append(result)
        return results
    
    def _send_notification(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification action."""
        # This would integrate with notification service
        logger.info(f"Sending notification: {params}")
        return {"message": "Notification sent", "recipient": params.get("recipient")}
    
    def _create_task(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task action."""
        # This would integrate with task management service
        logger.info(f"Creating task: {params}")
        return {"message": "Task created", "task_id": "generated_task_id"}
    
    def _update_status(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Update status action."""
        # This would update the status of the current item
        logger.info(f"Updating status: {params}")
        return {"message": "Status updated", "new_status": params.get("status")}
    
    def _log_event(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Log event action."""
        # This would log the event
        logger.info(f"Logging event: {params}")
        return {"message": "Event logged", "event_type": params.get("event_type")}
    
    def _call_api(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Call API action."""
        # This would make an HTTP call to another service
        logger.info(f"Calling API: {params}")
        return {"message": "API called", "url": params.get("url")} 