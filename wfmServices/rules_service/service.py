"""
Business logic layer for Rules Engine Service.
"""
from typing import Optional, List, Dict, Any
import json
import structlog
import httpx
import redis.asyncio as redis
from .repository import RulesRepository
from .models import RuleCreate, RuleUpdate, RuleEvaluationRequest, Process, Task
from .clients import SchedulerClient

logger = structlog.get_logger(__name__)


class RulesService:
    """Rules engine service business logic."""
    
    def __init__(self, rules_repo: RulesRepository, redis_client: redis.Redis):
        self.rules_repo = rules_repo
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
        self.process_service_url = "http://localhost:8008"  # process service
        self.vendor_service_url = "http://localhost:8007"  # vendor service
    
    async def create_rule(self, rule_data: RuleCreate, created_by: str) -> Dict[str, Any]:
        """Create a new rule."""
        try:
            # Check if rule name already exists for tenant
            existing_rule = await self.rules_repo.get_rule_by_name(
                rule_data.name, rule_data.tenant_id
            )
            
            if existing_rule:
                raise ValueError(f"Rule name '{rule_data.name}' already exists for this tenant")
            
            # Validate rule conditions and actions
            self._validate_rule(rule_data.conditions, rule_data.actions)
            
            # Prepare rule data
            rule_dict = rule_data.dict()
            rule_dict["created_by"] = created_by
            rule_dict["updated_by"] = created_by
            
            # Create rule
            rule = await self.rules_repo.create_rule(rule_dict)
            
            # Invalidate cache
            await self._invalidate_cache(rule_data.tenant_id)
            
            logger.info(f"Rule '{rule_data.name}' created successfully for tenant {rule_data.tenant_id}")
            return rule
            
        except Exception as e:
            logger.error(f"Failed to create rule {rule_data.name}: {str(e)}")
            raise
    
    async def get_rule(self, rule_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get rule by ID."""
        try:
            rule = await self.rules_repo.get_rule_by_id(rule_id, tenant_id)
            return rule
            
        except Exception as e:
            logger.error(f"Failed to get rule {rule_id}: {str(e)}")
            return None
    
    async def update_rule(self, rule_id: str, tenant_id: str, rule_data: RuleUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update rule."""
        try:
            # Check if rule exists
            existing_rule = await self.rules_repo.get_rule_by_id(rule_id, tenant_id)
            if not existing_rule:
                return None
            
            # Validate rule if conditions or actions are being updated
            if rule_data.conditions is not None or rule_data.actions is not None:
                conditions = rule_data.conditions or existing_rule["conditions"]
                actions = rule_data.actions or existing_rule["actions"]
                self._validate_rule(conditions, actions)
            
            # Prepare update data
            update_data = rule_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update rule
            rule = await self.rules_repo.update_rule(rule_id, tenant_id, update_data)
            
            if rule:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Rule '{rule['name']}' updated successfully")
            
            return rule
            
        except Exception as e:
            logger.error(f"Failed to update rule {rule_id}: {str(e)}")
            raise
    
    async def delete_rule(self, rule_id: str, tenant_id: str) -> bool:
        """Delete rule."""
        try:
            success = await self.rules_repo.delete_rule(rule_id, tenant_id)
            
            if success:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Rule {rule_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete rule {rule_id}: {str(e)}")
            return False
    
    async def list_rules(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List rules for tenant."""
        try:
            rules = await self.rules_repo.list_rules(tenant_id, skip, limit)
            return rules
            
        except Exception as e:
            logger.error(f"Failed to list rules for tenant {tenant_id}: {str(e)}")
            return []
    
    async def evaluate_rules(self, data: Dict[str, Any], tenant_id: str, rule_ids: Optional[List[str]] = None, category: Optional[str] = None, orchestrate: bool = False, auto_schedule: bool = True) -> Dict[str, Any]:
        """Evaluate rules against input data."""
        try:
            import time
            start_time = time.time()
            
            # Get rules to evaluate
            if rule_ids:
                rules = await self.rules_repo.get_rules_by_ids(rule_ids, tenant_id)
            elif category:
                rules = await self.rules_repo.get_rules_by_category(category, tenant_id)
            else:
                rules = await self.rules_repo.get_active_rules(tenant_id)
            
            # Filter active rules
            active_rules = [rule for rule in rules if rule["status"] == "active"]
            
            # Sort by priority (higher priority first)
            active_rules.sort(key=lambda x: x["priority"], reverse=True)
            
            matched_rules = []
            executed_actions = []
            
            # Evaluate each rule
            for rule in active_rules:
                try:
                    if self._evaluate_conditions(rule["conditions"], data):
                        matched_rules.append({
                            "rule_id": rule["id"],
                            "rule_name": rule["name"],
                            "category": rule["category"],
                            "priority": rule["priority"]
                        })
                        
                        # Execute actions
                        rule_actions = self._execute_actions(rule["actions"], data)
                        executed_actions.extend(rule_actions)
                        
                        # Stop if rule has stop_on_match flag
                        if rule.get("stop_on_match", False):
                            break
                            
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule['name']}: {str(e)}")
                    continue
            
            evaluation_time = time.time() - start_time
            
            response = {
                "matched_rules": matched_rules,
                "executed_actions": executed_actions,
                "evaluation_time": evaluation_time,
                "total_rules_evaluated": len(active_rules),
                "jobs": [],
                "schedules": [],
            }

            # Orchestrate process and task creation
            if orchestrate:
                try:
                    await self._orchestrate_processes(data, tenant_id, matched_rules, response, auto_schedule)
                except Exception as e:
                    logger.error(f"Orchestration failed: {str(e)}")

            return response
            
        except Exception as e:
            logger.error(f"Rule evaluation failed: {str(e)}")
            raise
    
    def _validate_rule(self, conditions: Dict[str, Any], actions: List[Dict[str, Any]]) -> None:
        """Validate rule conditions and actions."""
        if not conditions:
            raise ValueError("Rule must have at least one condition")
        
        if not actions:
            raise ValueError("Rule must have at least one action")
        
        # Validate conditions structure
        if not isinstance(conditions, dict):
            raise ValueError("Conditions must be a dictionary")
        
        # Validate actions structure
        if not isinstance(actions, list):
            raise ValueError("Actions must be a list")
        
        for action in actions:
            if not isinstance(action, dict):
                raise ValueError("Each action must be a dictionary")
            if "type" not in action:
                raise ValueError("Each action must have a 'type' field")
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against input data."""
        try:
            # Simple condition evaluation
            # This can be extended with more complex logic
            
            for field, condition in conditions.items():
                if field not in data:
                    return False
                
                value = data[field]
                
                if isinstance(condition, dict):
                    # Complex condition with operators
                    for operator, expected_value in condition.items():
                        if operator == "eq" and value != expected_value:
                            return False
                        elif operator == "ne" and value == expected_value:
                            return False
                        elif operator == "gt" and value <= expected_value:
                            return False
                        elif operator == "lt" and value >= expected_value:
                            return False
                        elif operator == "in" and value not in expected_value:
                            return False
                        elif operator == "not_in" and value in expected_value:
                            return False
                else:
                    # Simple equality check
                    if value != condition:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {str(e)}")
            return False
    
    def _execute_actions(self, actions: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute rule actions."""
        executed_actions = []
        
        for action in actions:
            try:
                action_type = action.get("type")
                action_params = action.get("params", {})
                
                executed_action = {
                    "type": action_type,
                    "params": action_params,
                    "status": "executed"
                }
                
                # Here you would implement actual action execution
                # For now, we just log the action
                logger.info(f"Executing action: {action_type} with params: {action_params}")
                
                executed_actions.append(executed_action)
                
            except Exception as e:
                logger.error(f"Error executing action {action.get('type', 'unknown')}: {str(e)}")
                executed_actions.append({
                    "type": action.get("type", "unknown"),
                    "params": action.get("params", {}),
                    "status": "failed",
                    "error": str(e)
                })
        
        return executed_actions
    
    async def _orchestrate_processes(self, data: Dict[str, Any], tenant_id: str, matched_rules: List[Dict[str, Any]], response: Dict[str, Any], auto_schedule: bool) -> None:
        """Orchestrate process and task creation based on matched rules."""
        order_id = data.get("order_id") or data.get("externalId")
        
        # Identify processes based on matched rules and order data
        processes_to_create = await self._identify_processes(data, matched_rules, tenant_id)
        
        for process_config in processes_to_create:
            try:
                # Execute process via process service
                async with httpx.AsyncClient() as client:
                    process_response = await client.post(
                        f"{self.process_service_url}/processes/execute",
                        json={
                            "order_id": order_id,
                            "process_definition_key": process_config["process_definition_key"],
                            "bpmn_xml": process_config["bpmn_xml"],
                            "input_data": data,
                            "tenant_id": tenant_id,
                            "auto_assign_tasks": auto_schedule
                        }
                    )
                    
                    if process_response.status_code == 200:
                        process_result = process_response.json()
                        response["jobs"].append({
                            "process_id": process_result.get("id"),
                            "process_name": process_config["name"],
                            "status": "started",
                            "tasks_created": len(process_result.get("tasks", []))
                        })
                        
                        logger.info(f"Process {process_config['name']} started for order {order_id}")
                    else:
                        logger.error(f"Failed to start process {process_config['name']}: {process_response.text}")
                        
            except Exception as e:
                logger.error(f"Failed to execute process {process_config['name']}: {str(e)}")
    
    async def _identify_processes(self, data: Dict[str, Any], matched_rules: List[Dict[str, Any]], tenant_id: str) -> List[Dict[str, Any]]:
        """Identify which processes should be created based on order data and matched rules."""
        processes = []
        
        # Example process identification logic
        # This would be customized based on your business rules
        
        order_type = data.get("type", "standard")
        priority = data.get("priority", "medium")
        source = data.get("source", "unknown")
        
        # Standard order processing workflow
        if order_type in ["standard", "service_order"]:
            processes.append({
                "name": "Order Validation Process",
                "process_definition_key": "order_validation",
                "bpmn_xml": self._get_order_validation_bpmn(),
                "priority": "high" if priority == "urgent" else "medium"
            })
        
        # High priority orders get expedited processing
        if priority == "urgent":
            processes.append({
                "name": "Expedited Processing",
                "process_definition_key": "expedited_process",
                "bpmn_xml": self._get_expedited_process_bpmn(),
                "priority": "high"
            })
        
        # Service orders require technical assessment
        if order_type == "service_order":
            processes.append({
                "name": "Technical Assessment",
                "process_definition_key": "technical_assessment",
                "bpmn_xml": self._get_technical_assessment_bpmn(),
                "priority": "medium"
            })
        
        # External orders need additional validation
        if source == "external":
            processes.append({
                "name": "External Order Verification",
                "process_definition_key": "external_verification",
                "bpmn_xml": self._get_external_verification_bpmn(),
                "priority": "medium"
            })
        
        return processes
    
    def _get_order_validation_bpmn(self) -> str:
        """Get BPMN XML for order validation process."""
        return '''
        <?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="order_validation">
          <bpmn:process id="order_validation" name="Order Validation Process">
            <bpmn:startEvent id="start" name="Start" />
            <bpmn:userTask id="validate_order" name="Validate Order Data" />
            <bpmn:userTask id="check_inventory" name="Check Inventory" />
            <bpmn:userTask id="verify_customer" name="Verify Customer" />
            <bpmn:endEvent id="end" name="End" />
            <bpmn:sequenceFlow sourceRef="start" targetRef="validate_order" />
            <bpmn:sequenceFlow sourceRef="validate_order" targetRef="check_inventory" />
            <bpmn:sequenceFlow sourceRef="check_inventory" targetRef="verify_customer" />
            <bpmn:sequenceFlow sourceRef="verify_customer" targetRef="end" />
          </bpmn:process>
        </bpmn:definitions>
        '''
    
    def _get_expedited_process_bpmn(self) -> str:
        """Get BPMN XML for expedited processing."""
        return '''
        <?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="expedited_process">
          <bpmn:process id="expedited_process" name="Expedited Processing">
            <bpmn:startEvent id="start" name="Start" />
            <bpmn:userTask id="priority_review" name="Priority Review" />
            <bpmn:userTask id="fast_track" name="Fast Track Processing" />
            <bpmn:endEvent id="end" name="End" />
            <bpmn:sequenceFlow sourceRef="start" targetRef="priority_review" />
            <bpmn:sequenceFlow sourceRef="priority_review" targetRef="fast_track" />
            <bpmn:sequenceFlow sourceRef="fast_track" targetRef="end" />
          </bpmn:process>
        </bpmn:definitions>
        '''
    
    def _get_technical_assessment_bpmn(self) -> str:
        """Get BPMN XML for technical assessment process."""
        return '''
        <?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="technical_assessment">
          <bpmn:process id="technical_assessment" name="Technical Assessment">
            <bpmn:startEvent id="start" name="Start" />
            <bpmn:userTask id="technical_review" name="Technical Review" />
            <bpmn:userTask id="resource_allocation" name="Resource Allocation" />
            <bpmn:userTask id="schedule_work" name="Schedule Work" />
            <bpmn:endEvent id="end" name="End" />
            <bpmn:sequenceFlow sourceRef="start" targetRef="technical_review" />
            <bpmn:sequenceFlow sourceRef="technical_review" targetRef="resource_allocation" />
            <bpmn:sequenceFlow sourceRef="resource_allocation" targetRef="schedule_work" />
            <bpmn:sequenceFlow sourceRef="schedule_work" targetRef="end" />
          </bpmn:process>
        </bpmn:definitions>
        '''
    
    def _get_external_verification_bpmn(self) -> str:
        """Get BPMN XML for external order verification."""
        return '''
        <?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="external_verification">
          <bpmn:process id="external_verification" name="External Order Verification">
            <bpmn:startEvent id="start" name="Start" />
            <bpmn:userTask id="verify_source" name="Verify Source" />
            <bpmn:userTask id="validate_format" name="Validate Format" />
            <bpmn:userTask id="security_check" name="Security Check" />
            <bpmn:endEvent id="end" name="End" />
            <bpmn:sequenceFlow sourceRef="start" targetRef="verify_source" />
            <bpmn:sequenceFlow sourceRef="verify_source" targetRef="validate_format" />
            <bpmn:sequenceFlow sourceRef="validate_format" targetRef="security_check" />
            <bpmn:sequenceFlow sourceRef="security_check" targetRef="end" />
          </bpmn:process>
        </bpmn:definitions>
        '''
    
    async def _invalidate_cache(self, tenant_id: str) -> None:
        """Invalidate cache for tenant."""
        try:
            cache_key = f"rules:{tenant_id}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Cache invalidated for tenant {tenant_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for tenant {tenant_id}: {str(e)}") 