"""
Analytics & Reports Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import structlog

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user
from .service import AnalyticsService
from .repository import ReportRepository, DashboardRepository, MetricDefinitionRepository, AlertRuleRepository
from .models import ReportCreate, ReportUpdate, ReportResponse, DashboardCreate, DashboardUpdate, DashboardResponse, AnalyticsRequest, AnalyticsResponse, KPIRequest, KPIResponse, DataExportRequest, DataExportResponse, AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse

logger = setup_logging("analytics-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Analytics & Reports Service...")
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    logger.info("Analytics & Reports Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Analytics & Reports Service...")
    await db_manager.close()
    logger.info("Analytics & Reports Service shutdown complete")


app = FastAPI(
    title="Analytics & Reports Service",
    description="Handles analytics, reporting, and dashboard functionality",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging is now handled by structured logging setup


async def get_analytics_service() -> AnalyticsService:
    """Dependency injection for AnalyticsService."""
    database = db_manager.get_database()
    redis_client = db_manager.get_redis()
    
    report_repo = ReportRepository(database)
    dashboard_repo = DashboardRepository(database)
    metric_repo = MetricDefinitionRepository(database)
    alert_repo = AlertRuleRepository(database)
    
    return AnalyticsService(report_repo, dashboard_repo, metric_repo, alert_repo, redis_client)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0"
    }


# Report endpoints
@app.post("/reports", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a new report."""
    try:
        report = await analytics_service.create_report(report_data, current_user["id"])
        return ReportResponse(**report)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create report: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get report by ID."""
    report = await analytics_service.get_report(report_id, tenant_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportResponse(**report)


@app.put("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report_data: ReportUpdate,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Update report."""
    report = await analytics_service.update_report(report_id, tenant_id, report_data, current_user["id"])
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportResponse(**report)


@app.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Delete report."""
    success = await analytics_service.delete_report(report_id, tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return {"message": "Report deleted successfully"}


@app.get("/reports")
async def list_reports(
    tenant_id: str = Query(..., description="Tenant ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """List reports for tenant."""
    reports = await analytics_service.list_reports(tenant_id, skip, limit)
    return {"reports": reports, "total": len(reports)}


@app.post("/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate a report."""
    try:
        report_data = await analytics_service.generate_report(report_id, tenant_id)
        return report_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Dashboard endpoints
@app.post("/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a new dashboard."""
    try:
        dashboard = await analytics_service.create_dashboard(dashboard_data, current_user["id"])
        return DashboardResponse(**dashboard)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get dashboard by ID."""
    dashboard = await analytics_service.get_dashboard(dashboard_id, tenant_id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return DashboardResponse(**dashboard)


@app.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    dashboard_data: DashboardUpdate,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Update dashboard."""
    dashboard = await analytics_service.update_dashboard(dashboard_id, tenant_id, dashboard_data, current_user["id"])
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return DashboardResponse(**dashboard)


@app.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Delete dashboard."""
    success = await analytics_service.delete_dashboard(dashboard_id, tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return {"message": "Dashboard deleted successfully"}


@app.get("/dashboards")
async def list_dashboards(
    tenant_id: str = Query(..., description="Tenant ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """List dashboards for tenant."""
    dashboards = await analytics_service.list_dashboards(tenant_id, skip, limit)
    return {"dashboards": dashboards, "total": len(dashboards)}


@app.get("/dashboards/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get dashboard data with widget data."""
    try:
        dashboard_data = await analytics_service.get_dashboard_data(dashboard_id, tenant_id)
        return dashboard_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Analytics endpoints
@app.post("/analytics", response_model=AnalyticsResponse)
async def analyze_metrics(
    request: AnalyticsRequest,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Analyze metrics."""
    try:
        result = await analytics_service.analyze_metrics(request)
        return AnalyticsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze metrics: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.post("/kpi", response_model=KPIResponse)
async def calculate_kpi(
    request: KPIRequest,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Calculate KPI."""
    try:
        result = await analytics_service.calculate_kpi(request)
        return KPIResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate KPI: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.post("/export", response_model=DataExportResponse)
async def export_data(
    request: DataExportRequest,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Export data."""
    try:
        result = await analytics_service.export_data(request)
        return DataExportResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export data: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Alert rule endpoints
@app.post("/alerts", response_model=AlertRuleResponse)
async def create_alert_rule(
    alert_data: AlertRuleCreate,
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a new alert rule."""
    try:
        alert = await analytics_service.create_alert_rule(alert_data, current_user["id"])
        return AlertRuleResponse(**alert)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert rule: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/alerts/{alert_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    alert_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get alert rule by ID."""
    alert = await analytics_service.get_alert_rule(alert_id, tenant_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return AlertRuleResponse(**alert)


@app.put("/alerts/{alert_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    alert_id: str,
    alert_data: AlertRuleUpdate,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Update alert rule."""
    alert = await analytics_service.update_alert_rule(alert_id, tenant_id, alert_data, current_user["id"])
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return AlertRuleResponse(**alert)


@app.delete("/alerts/{alert_id}")
async def delete_alert_rule(
    alert_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Delete alert rule."""
    success = await analytics_service.delete_alert_rule(alert_id, tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return {"message": "Alert rule deleted successfully"}


@app.get("/alerts")
async def list_alert_rules(
    tenant_id: str = Query(..., description="Tenant ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """List alert rules for tenant."""
    alerts = await analytics_service.list_alert_rules(tenant_id, skip, limit)
    return {"alerts": alerts, "total": len(alerts)}


@app.post("/alerts/check")
async def check_alerts(
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Check and trigger alerts."""
    try:
        triggered_alerts = await analytics_service.check_alerts(tenant_id)
        return {"triggered_alerts": triggered_alerts, "total": len(triggered_alerts)}
    except Exception as e:
        logger.error(f"Failed to check alerts: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "analytics_service.main:app",
        host="0.0.0.0",
        port=int(os.getenv("SERVICE_PORT", 8006)),
        reload=True
    ) 