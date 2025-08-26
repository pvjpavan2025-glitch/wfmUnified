"""
Repository layer for Analytics & Reports Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId
from .models import Report, Dashboard, MetricDefinition, AlertRule

logger = structlog.get_logger(__name__)


class ReportRepository:
    """Repository for report operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.reports
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new report."""
        try:
            report_data["created_at"] = datetime.utcnow()
            report_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(report_data)
            report_data["_id"] = result.inserted_id
            
            return self._convert_id(report_data)
        except Exception as e:
            logger.error(f"Failed to create report: {str(e)}")
            raise
    
    async def get_report_by_id(self, report_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID and tenant."""
        try:
            report = await self.collection.find_one({
                "_id": ObjectId(report_id),
                "tenant_id": tenant_id
            })
            
            if report:
                return self._convert_id(report)
            return None
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {str(e)}")
            return None
    
    async def update_report(self, report_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update report."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(report_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_report_by_id(report_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {str(e)}")
            return None
    
    async def delete_report(self, report_id: str, tenant_id: str) -> bool:
        """Delete report."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(report_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {str(e)}")
            return False
    
    async def list_reports(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List reports for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            reports = await cursor.to_list(length=limit)
            
            return [self._convert_id(report) for report in reports]
        except Exception as e:
            logger.error(f"Failed to list reports for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_reports_by_type(self, report_type: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get reports by type."""
        try:
            cursor = self.collection.find({
                "report_type": report_type,
                "tenant_id": tenant_id
            })
            
            reports = await cursor.to_list(length=1000)
            return [self._convert_id(report) for report in reports]
        except Exception as e:
            logger.error(f"Failed to get reports by type {report_type}: {str(e)}")
            return []


class DashboardRepository:
    """Repository for dashboard operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.dashboards
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard."""
        try:
            dashboard_data["created_at"] = datetime.utcnow()
            dashboard_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(dashboard_data)
            dashboard_data["_id"] = result.inserted_id
            
            return self._convert_id(dashboard_data)
        except Exception as e:
            logger.error(f"Failed to create dashboard: {str(e)}")
            raise
    
    async def get_dashboard_by_id(self, dashboard_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get dashboard by ID and tenant."""
        try:
            dashboard = await self.collection.find_one({
                "_id": ObjectId(dashboard_id),
                "tenant_id": tenant_id
            })
            
            if dashboard:
                return self._convert_id(dashboard)
            return None
        except Exception as e:
            logger.error(f"Failed to get dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def update_dashboard(self, dashboard_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update dashboard."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(dashboard_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_dashboard_by_id(dashboard_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def delete_dashboard(self, dashboard_id: str, tenant_id: str) -> bool:
        """Delete dashboard."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(dashboard_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete dashboard {dashboard_id}: {str(e)}")
            return False
    
    async def list_dashboards(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List dashboards for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            dashboards = await cursor.to_list(length=limit)
            
            return [self._convert_id(dashboard) for dashboard in dashboards]
        except Exception as e:
            logger.error(f"Failed to list dashboards for tenant {tenant_id}: {str(e)}")
            return []


class MetricDefinitionRepository:
    """Repository for metric definition operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.metric_definitions
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_metric_definition(self, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new metric definition."""
        try:
            metric_data["created_at"] = datetime.utcnow()
            metric_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(metric_data)
            metric_data["_id"] = result.inserted_id
            
            return self._convert_id(metric_data)
        except Exception as e:
            logger.error(f"Failed to create metric definition: {str(e)}")
            raise
    
    async def get_metric_definition_by_id(self, metric_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get metric definition by ID and tenant."""
        try:
            metric = await self.collection.find_one({
                "_id": ObjectId(metric_id),
                "tenant_id": tenant_id
            })
            
            if metric:
                return self._convert_id(metric)
            return None
        except Exception as e:
            logger.error(f"Failed to get metric definition {metric_id}: {str(e)}")
            return None
    
    async def get_metric_definition_by_name(self, name: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get metric definition by name and tenant."""
        try:
            metric = await self.collection.find_one({
                "name": name,
                "tenant_id": tenant_id
            })
            
            if metric:
                return self._convert_id(metric)
            return None
        except Exception as e:
            logger.error(f"Failed to get metric definition by name {name}: {str(e)}")
            return None
    
    async def update_metric_definition(self, metric_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update metric definition."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(metric_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_metric_definition_by_id(metric_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update metric definition {metric_id}: {str(e)}")
            return None
    
    async def delete_metric_definition(self, metric_id: str, tenant_id: str) -> bool:
        """Delete metric definition."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(metric_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete metric definition {metric_id}: {str(e)}")
            return False
    
    async def list_metric_definitions(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List metric definitions for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            metrics = await cursor.to_list(length=limit)
            
            return [self._convert_id(metric) for metric in metrics]
        except Exception as e:
            logger.error(f"Failed to list metric definitions for tenant {tenant_id}: {str(e)}")
            return []


class AlertRuleRepository:
    """Repository for alert rule operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.alert_rules
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_alert_rule(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert rule."""
        try:
            alert_data["created_at"] = datetime.utcnow()
            alert_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(alert_data)
            alert_data["_id"] = result.inserted_id
            
            return self._convert_id(alert_data)
        except Exception as e:
            logger.error(f"Failed to create alert rule: {str(e)}")
            raise
    
    async def get_alert_rule_by_id(self, alert_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get alert rule by ID and tenant."""
        try:
            alert = await self.collection.find_one({
                "_id": ObjectId(alert_id),
                "tenant_id": tenant_id
            })
            
            if alert:
                return self._convert_id(alert)
            return None
        except Exception as e:
            logger.error(f"Failed to get alert rule {alert_id}: {str(e)}")
            return None
    
    async def update_alert_rule(self, alert_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update alert rule."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(alert_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_alert_rule_by_id(alert_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update alert rule {alert_id}: {str(e)}")
            return None
    
    async def delete_alert_rule(self, alert_id: str, tenant_id: str) -> bool:
        """Delete alert rule."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(alert_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete alert rule {alert_id}: {str(e)}")
            return False
    
    async def list_alert_rules(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List alert rules for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            alerts = await cursor.to_list(length=limit)
            
            return [self._convert_id(alert) for alert in alerts]
        except Exception as e:
            logger.error(f"Failed to list alert rules for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_active_alert_rules(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active alert rules for tenant."""
        try:
            cursor = self.collection.find({
                "tenant_id": tenant_id,
                "status": "active"
            })
            
            alerts = await cursor.to_list(length=1000)
            return [self._convert_id(alert) for alert in alerts]
        except Exception as e:
            logger.error(f"Failed to get active alert rules for tenant {tenant_id}: {str(e)}")
            return []
    
    async def update_last_triggered(self, alert_id: str, tenant_id: str) -> bool:
        """Update last triggered time for alert rule."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(alert_id), "tenant_id": tenant_id},
                {"$set": {"last_triggered": datetime.utcnow(), "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update last triggered for alert rule {alert_id}: {str(e)}")
            return False 