"""
Business logic layer for Rules Engine Service.
"""
from typing import Optional, List, Dict, Any
import json
import structlog
import redis.asyncio as redis
from .repository import RulesRepository
from .models import RuleCreate, RuleUpdate, RuleEvaluationRequest
from .clients import SchedulerClient

logger = structlog.get_logger(__name__)


class RulesService:
    """Rules engine service business logic."""
    
    def __init__(self, rules_repo: RulesRepository, redis_client: redis.Redis):
        self.rules_repo = rules_repo
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
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
    
    async def evaluate_rules(self, data: Dict[str, Any], tenant_id: str, rule_ids: Optional[List[str]] = None, category: Optional[str] = None, orchestrate: bool = False, split_jobs: bool = False, auto_schedule: bool = True) -> Dict[str, Any]:
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

            # Orchestrate downstream job creation/scheduling
            if orchestrate:
                try:
                    sched = SchedulerClient(tenant_id=tenant_id)
                    items = data.get("serviceOrderItems") or data.get("items") or []
                    # Prefer canonical DB order_id when provided; fall back to externalId
                    order_id = data.get("order_id") or data.get("externalId")
                    if split_jobs and items:
                        for idx, item in enumerate(items):
                            job_payload = {
                                "name": f"Order {data.get('externalId','')}-{item.get('id',idx+1)}",
                                "description": data.get("description"),
                                "tasks": [item.get("id", f"task-{idx+1}")],
                                "priority": "medium",
                                "sla_hours": 24,
                                "tenant_id": tenant_id,
                                "status": "pending",
                                "order_id": order_id,
                            }
                            job = await sched.create_job(job_payload)
                            response["jobs"].append(job)
                            if auto_schedule:
                                job_id = job.get("id") or job.get("_id") or job.get("job_id")
                                if job_id:
                                    sch = await sched.schedule_job(job_id)
                                    response["schedules"].append(sch)
                    else:
                        job_payload = {
                            "name": f"Order {data.get('externalId','')}",
                            "description": data.get("description"),
                            "tasks": [i.get("id", f"task-{n+1}") for n,i in enumerate(items)] or ["task-1"],
                            "priority": "medium",
                            "sla_hours": 24,
                            "tenant_id": tenant_id,
                            "status": "pending",
                            "order_id": order_id,
                        }
                        job = await sched.create_job(job_payload)
                        response["jobs"].append(job)
                        if auto_schedule:
                            job_id = job.get("id") or job.get("_id") or job.get("job_id")
                            if job_id:
                                sch = await sched.schedule_job(job_id)
                                response["schedules"].append(sch)
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
    
    async def _invalidate_cache(self, tenant_id: str) -> None:
        """Invalidate cache for tenant."""
        try:
            cache_key = f"rules:{tenant_id}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Cache invalidated for tenant {tenant_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for tenant {tenant_id}: {str(e)}") 