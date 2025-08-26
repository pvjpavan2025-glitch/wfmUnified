"""
Business logic layer for Analytics & Reports Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis
from .repository import ReportRepository, DashboardRepository, MetricDefinitionRepository, AlertRuleRepository
from .models import ReportCreate, ReportUpdate, DashboardCreate, DashboardUpdate, AnalyticsRequest, KPIRequest, DataExportRequest, AlertRuleCreate, AlertRuleUpdate

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """Analytics and reports service business logic."""
    
    def __init__(self, report_repo: ReportRepository, dashboard_repo: DashboardRepository,
                 metric_repo: MetricDefinitionRepository, alert_repo: AlertRuleRepository,
                 redis_client: redis.Redis):
        self.report_repo = report_repo
        self.dashboard_repo = dashboard_repo
        self.metric_repo = metric_repo
        self.alert_repo = alert_repo
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def create_report(self, report_data: ReportCreate, created_by: str) -> Dict[str, Any]:
        """Create a new report."""
        try:
            # Prepare report data
            report_dict = report_data.dict()
            report_dict["created_by"] = created_by
            report_dict["updated_by"] = created_by
            
            # Create report
            report = await self.report_repo.create_report(report_dict)
            
            # Invalidate cache
            await self._invalidate_cache(report_data.tenant_id)
            
            logger.info(f"Report '{report_data.name}' created successfully for tenant {report_data.tenant_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to create report {report_data.name}: {str(e)}")
            raise
    
    async def get_report(self, report_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        try:
            report = await self.report_repo.get_report_by_id(report_id, tenant_id)
            return report
            
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {str(e)}")
            return None
    
    async def update_report(self, report_id: str, tenant_id: str, report_data: ReportUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update report."""
        try:
            # Check if report exists
            existing_report = await self.report_repo.get_report_by_id(report_id, tenant_id)
            if not existing_report:
                return None
            
            # Prepare update data
            update_data = report_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update report
            report = await self.report_repo.update_report(report_id, tenant_id, update_data)
            
            if report:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Report '{report['name']}' updated successfully")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {str(e)}")
            raise
    
    async def delete_report(self, report_id: str, tenant_id: str) -> bool:
        """Delete report."""
        try:
            success = await self.report_repo.delete_report(report_id, tenant_id)
            
            if success:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Report {report_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {str(e)}")
            return False
    
    async def list_reports(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List reports for tenant."""
        try:
            reports = await self.report_repo.list_reports(tenant_id, skip, limit)
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports for tenant {tenant_id}: {str(e)}")
            return []
    
    async def generate_report(self, report_id: str, tenant_id: str) -> Dict[str, Any]:
        """Generate a report."""
        try:
            # Get report definition
            report = await self.report_repo.get_report_by_id(report_id, tenant_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Generate report based on type
            report_data = await self._generate_report_data(report)
            
            # Update report with generation time
            await self.report_repo.update_report(
                report_id, 
                tenant_id, 
                {"last_generated": datetime.utcnow()}
            )
            
            logger.info(f"Report {report_id} generated successfully")
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate report {report_id}: {str(e)}")
            raise
    
    async def create_dashboard(self, dashboard_data: DashboardCreate, created_by: str) -> Dict[str, Any]:
        """Create a new dashboard."""
        try:
            # Prepare dashboard data
            dashboard_dict = dashboard_data.dict()
            dashboard_dict["created_by"] = created_by
            dashboard_dict["updated_by"] = created_by
            
            # Create dashboard
            dashboard = await self.dashboard_repo.create_dashboard(dashboard_dict)
            
            # Invalidate cache
            await self._invalidate_cache(dashboard_data.tenant_id)
            
            logger.info(f"Dashboard '{dashboard_data.name}' created successfully for tenant {dashboard_data.tenant_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to create dashboard {dashboard_data.name}: {str(e)}")
            raise
    
    async def get_dashboard(self, dashboard_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get dashboard by ID."""
        try:
            dashboard = await self.dashboard_repo.get_dashboard_by_id(dashboard_id, tenant_id)
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to get dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def update_dashboard(self, dashboard_id: str, tenant_id: str, dashboard_data: DashboardUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update dashboard."""
        try:
            # Check if dashboard exists
            existing_dashboard = await self.dashboard_repo.get_dashboard_by_id(dashboard_id, tenant_id)
            if not existing_dashboard:
                return None
            
            # Prepare update data
            update_data = dashboard_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update dashboard
            dashboard = await self.dashboard_repo.update_dashboard(dashboard_id, tenant_id, update_data)
            
            if dashboard:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Dashboard '{dashboard['name']}' updated successfully")
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to update dashboard {dashboard_id}: {str(e)}")
            raise
    
    async def delete_dashboard(self, dashboard_id: str, tenant_id: str) -> bool:
        """Delete dashboard."""
        try:
            success = await self.dashboard_repo.delete_dashboard(dashboard_id, tenant_id)
            
            if success:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Dashboard {dashboard_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete dashboard {dashboard_id}: {str(e)}")
            return False
    
    async def list_dashboards(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List dashboards for tenant."""
        try:
            dashboards = await self.dashboard_repo.list_dashboards(tenant_id, skip, limit)
            return dashboards
            
        except Exception as e:
            logger.error(f"Failed to list dashboards for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_dashboard_data(self, dashboard_id: str, tenant_id: str) -> Dict[str, Any]:
        """Get dashboard data with widget data."""
        try:
            dashboard = await self.dashboard_repo.get_dashboard_by_id(dashboard_id, tenant_id)
            if not dashboard:
                raise ValueError(f"Dashboard {dashboard_id} not found")
            
            # Get data for each widget
            widget_data = []
            for widget in dashboard["widgets"]:
                widget_info = await self._get_widget_data(widget, tenant_id)
                widget_data.append(widget_info)
            
            return {
                "dashboard": dashboard,
                "widget_data": widget_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data {dashboard_id}: {str(e)}")
            raise
    
    async def analyze_metrics(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze metrics based on request."""
        try:
            # Get metric definition
            metric_def = await self.metric_repo.get_metric_definition_by_name(request.metric_type, request.tenant_id)
            if not metric_def:
                raise ValueError(f"Metric definition for {request.metric_type} not found")
            
            # Calculate metric data
            data = await self._calculate_metric_data(metric_def, request.time_range, request.filters)
            
            # Generate summary
            summary = await self._generate_metric_summary(data)
            
            return {
                "metric_type": request.metric_type,
                "time_range": request.time_range,
                "data": data,
                "summary": summary,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze metrics: {str(e)}")
            raise
    
    async def calculate_kpi(self, request: KPIRequest) -> Dict[str, Any]:
        """Calculate KPI value."""
        try:
            # Get KPI definition
            kpi_def = await self.metric_repo.get_metric_definition_by_name(request.kpi_name, request.tenant_id)
            if not kpi_def:
                raise ValueError(f"KPI definition for {request.kpi_name} not found")
            
            # Calculate KPI value
            value = await self._calculate_kpi_value(kpi_def, request.time_period, request.filters)
            
            # Determine status and trend
            status = await self._determine_kpi_status(value, kpi_def)
            trend = await self._determine_kpi_trend(request.kpi_name, request.tenant_id)
            
            return {
                "kpi_name": request.kpi_name,
                "value": value,
                "target": kpi_def.get("target"),
                "unit": kpi_def.get("unit", ""),
                "status": status,
                "trend": trend,
                "calculated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate KPI: {str(e)}")
            raise
    
    async def export_data(self, request: DataExportRequest) -> Dict[str, Any]:
        """Export data in specified format."""
        try:
            # Generate export ID
            export_id = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Start export process (this would be async in production)
            export_data = await self._generate_export_data(request)
            
            return {
                "export_id": export_id,
                "export_type": request.export_type,
                "format": request.format,
                "status": "completed",
                "download_url": f"/exports/{export_id}",
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to export data: {str(e)}")
            raise
    
    async def create_alert_rule(self, alert_data: AlertRuleCreate, created_by: str) -> Dict[str, Any]:
        """Create a new alert rule."""
        try:
            # Prepare alert data
            alert_dict = alert_data.dict()
            alert_dict["created_by"] = created_by
            alert_dict["updated_by"] = created_by
            
            # Create alert rule
            alert = await self.alert_repo.create_alert_rule(alert_dict)
            
            # Invalidate cache
            await self._invalidate_cache(alert_data.tenant_id)
            
            logger.info(f"Alert rule '{alert_data.name}' created successfully for tenant {alert_data.tenant_id}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert rule {alert_data.name}: {str(e)}")
            raise
    
    async def get_alert_rule(self, alert_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get alert rule by ID."""
        try:
            alert = await self.alert_repo.get_alert_rule_by_id(alert_id, tenant_id)
            return alert
            
        except Exception as e:
            logger.error(f"Failed to get alert rule {alert_id}: {str(e)}")
            return None
    
    async def update_alert_rule(self, alert_id: str, tenant_id: str, alert_data: AlertRuleUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update alert rule."""
        try:
            # Check if alert rule exists
            existing_alert = await self.alert_repo.get_alert_rule_by_id(alert_id, tenant_id)
            if not existing_alert:
                return None
            
            # Prepare update data
            update_data = alert_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update alert rule
            alert = await self.alert_repo.update_alert_rule(alert_id, tenant_id, update_data)
            
            if alert:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Alert rule '{alert['name']}' updated successfully")
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to update alert rule {alert_id}: {str(e)}")
            raise
    
    async def delete_alert_rule(self, alert_id: str, tenant_id: str) -> bool:
        """Delete alert rule."""
        try:
            success = await self.alert_repo.delete_alert_rule(alert_id, tenant_id)
            
            if success:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Alert rule {alert_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete alert rule {alert_id}: {str(e)}")
            return False
    
    async def list_alert_rules(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List alert rules for tenant."""
        try:
            alerts = await self.alert_repo.list_alert_rules(tenant_id, skip, limit)
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to list alert rules for tenant {tenant_id}: {str(e)}")
            return []
    
    async def check_alerts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Check and trigger alerts."""
        try:
            # Get active alert rules
            alert_rules = await self.alert_repo.get_active_alert_rules(tenant_id)
            
            triggered_alerts = []
            for alert in alert_rules:
                # Check if alert should be triggered
                should_trigger = await self._check_alert_condition(alert)
                
                if should_trigger:
                    # Update last triggered time
                    await self.alert_repo.update_last_triggered(alert["id"], tenant_id)
                    
                    triggered_alerts.append({
                        "alert_id": alert["id"],
                        "alert_name": alert["name"],
                        "metric_name": alert["metric_name"],
                        "threshold": alert["threshold"],
                        "current_value": 0.0,  # This would be calculated
                        "triggered_at": datetime.utcnow()
                    })
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to check alerts for tenant {tenant_id}: {str(e)}")
            return []
    
    async def _generate_report_data(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report data based on report type."""
        try:
            report_type = report["report_type"]
            
            # This would integrate with other services to get actual data
            # For now, return mock data
            if report_type == "performance":
                return {
                    "type": "performance",
                    "data": [
                        {"date": "2024-01-01", "jobs_completed": 150, "avg_time": 2.5},
                        {"date": "2024-01-02", "jobs_completed": 165, "avg_time": 2.3},
                        {"date": "2024-01-03", "jobs_completed": 140, "avg_time": 2.8}
                    ],
                    "summary": {"total_jobs": 455, "avg_completion_time": 2.53}
                }
            elif report_type == "issues":
                return {
                    "type": "issues",
                    "data": [
                        {"category": "technical", "count": 25, "resolved": 20},
                        {"category": "process", "count": 15, "resolved": 12},
                        {"category": "user", "count": 10, "resolved": 8}
                    ],
                    "summary": {"total_issues": 50, "resolution_rate": 0.8}
                }
            else:
                return {"type": report_type, "data": [], "summary": {}}
                
        except Exception as e:
            logger.error(f"Error generating report data: {str(e)}")
            return {"type": "unknown", "data": [], "summary": {}}
    
    async def _get_widget_data(self, widget: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Get data for a specific widget."""
        try:
            widget_type = widget.get("type", "unknown")
            
            # This would calculate actual widget data
            # For now, return mock data
            if widget_type == "chart":
                return {
                    "type": "chart",
                    "data": [{"x": "Jan", "y": 100}, {"x": "Feb", "y": 120}, {"x": "Mar", "y": 90}]
                }
            elif widget_type == "metric":
                return {
                    "type": "metric",
                    "value": 85.5,
                    "unit": "%",
                    "trend": "up"
                }
            else:
                return {"type": widget_type, "data": {}}
                
        except Exception as e:
            logger.error(f"Error getting widget data: {str(e)}")
            return {"type": "error", "data": {}}
    
    async def _calculate_metric_data(self, metric_def: Dict[str, Any], time_range: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate metric data based on definition."""
        try:
            # This would integrate with other services to get actual data
            # For now, return mock data
            return [
                {"timestamp": "2024-01-01T00:00:00Z", "value": 100},
                {"timestamp": "2024-01-02T00:00:00Z", "value": 120},
                {"timestamp": "2024-01-03T00:00:00Z", "value": 90}
            ]
        except Exception as e:
            logger.error(f"Error calculating metric data: {str(e)}")
            return []
    
    async def _generate_metric_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for metric data."""
        try:
            if not data:
                return {"count": 0, "avg": 0, "min": 0, "max": 0}
            
            values = [item.get("value", 0) for item in data]
            return {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        except Exception as e:
            logger.error(f"Error generating metric summary: {str(e)}")
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
    
    async def _calculate_kpi_value(self, kpi_def: Dict[str, Any], time_period: str, filters: Dict[str, Any]) -> float:
        """Calculate KPI value."""
        try:
            # This would calculate actual KPI value
            # For now, return mock value
            return 85.5
        except Exception as e:
            logger.error(f"Error calculating KPI value: {str(e)}")
            return 0.0
    
    async def _determine_kpi_status(self, value: float, kpi_def: Dict[str, Any]) -> str:
        """Determine KPI status."""
        try:
            target = kpi_def.get("target", 100)
            if value >= target * 0.9:
                return "on_track"
            elif value >= target * 0.7:
                return "at_risk"
            else:
                return "off_track"
        except Exception as e:
            logger.error(f"Error determining KPI status: {str(e)}")
            return "unknown"
    
    async def _determine_kpi_trend(self, kpi_name: str, tenant_id: str) -> str:
        """Determine KPI trend."""
        try:
            # This would compare current value with historical data
            # For now, return mock trend
            return "up"
        except Exception as e:
            logger.error(f"Error determining KPI trend: {str(e)}")
            return "stable"
    
    async def _generate_export_data(self, request: DataExportRequest) -> Dict[str, Any]:
        """Generate export data."""
        try:
            # This would generate actual export data
            # For now, return mock data
            return {
                "export_type": request.export_type,
                "format": request.format,
                "data": []
            }
        except Exception as e:
            logger.error(f"Error generating export data: {str(e)}")
            return {"export_type": "unknown", "format": "unknown", "data": []}
    
    async def _check_alert_condition(self, alert: Dict[str, Any]) -> bool:
        """Check if alert condition is met."""
        try:
            # This would check actual metric values against thresholds
            # For now, return False (no alerts triggered)
            return False
        except Exception as e:
            logger.error(f"Error checking alert condition: {str(e)}")
            return False
    
    async def _invalidate_cache(self, tenant_id: str) -> None:
        """Invalidate cache for tenant."""
        try:
            cache_key = f"analytics:{tenant_id}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Cache invalidated for tenant {tenant_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for tenant {tenant_id}: {str(e)}") 