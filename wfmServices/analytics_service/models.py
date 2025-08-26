"""
Data models for Analytics & Reports Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum


class ReportCreate(BaseModel):
    """Report creation model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: str = Field(..., description="Type of report")
    parameters: Dict[str, Any] = Field(default={}, description="Report parameters")
    schedule: Optional[str] = Field(None, description="Cron schedule for automated reports")
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class ReportUpdate(BaseModel):
    """Report update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    status: Optional[StatusEnum] = None


class ReportResponse(BaseEntity):
    """Report response model."""
    name: str
    description: Optional[str] = None
    report_type: str
    parameters: Dict[str, Any]
    schedule: Optional[str] = None
    status: StatusEnum
    last_generated: Optional[datetime] = None
    download_url: Optional[str] = None


class Report(BaseEntity):
    """Report entity model."""
    name: str
    description: Optional[str] = None
    report_type: str
    parameters: Dict[str, Any]
    schedule: Optional[str] = None
    status: StatusEnum
    last_generated: Optional[datetime] = None
    file_path: Optional[str] = None


class AnalyticsRequest(BaseModel):
    """Analytics request model."""
    metric_type: str = Field(..., description="Type of metric to analyze")
    time_range: Dict[str, Any] = Field(..., description="Time range for analysis")
    filters: Dict[str, Any] = Field(default={}, description="Additional filters")
    tenant_id: str


class AnalyticsResponse(BaseModel):
    """Analytics response model."""
    metric_type: str
    time_range: Dict[str, Any]
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: datetime


class DashboardCreate(BaseModel):
    """Dashboard creation model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    layout: Dict[str, Any] = Field(..., description="Dashboard layout configuration")
    widgets: List[Dict[str, Any]] = Field(..., description="Dashboard widgets")
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class DashboardUpdate(BaseModel):
    """Dashboard update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    status: Optional[StatusEnum] = None


class DashboardResponse(BaseEntity):
    """Dashboard response model."""
    name: str
    description: Optional[str] = None
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    status: StatusEnum


class Dashboard(BaseEntity):
    """Dashboard entity model."""
    name: str
    description: Optional[str] = None
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    status: StatusEnum


class MetricDefinition(BaseModel):
    """Metric definition model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    metric_type: str = Field(..., description="Type of metric")
    calculation: Dict[str, Any] = Field(..., description="Calculation logic")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    tenant_id: str


class MetricDefinitionResponse(BaseEntity):
    """Metric definition response model."""
    name: str
    description: Optional[str] = None
    metric_type: str
    calculation: Dict[str, Any]
    unit: Optional[str] = None


class MetricDefinition(BaseEntity):
    """Metric definition entity model."""
    name: str
    description: Optional[str] = None
    metric_type: str
    calculation: Dict[str, Any]
    unit: Optional[str] = None


class KPIRequest(BaseModel):
    """KPI request model."""
    kpi_name: str = Field(..., description="Name of the KPI")
    time_period: str = Field(..., description="Time period for KPI calculation")
    filters: Dict[str, Any] = Field(default={}, description="Additional filters")
    tenant_id: str


class KPIResponse(BaseModel):
    """KPI response model."""
    kpi_name: str
    value: float
    target: Optional[float] = None
    unit: str
    status: str = Field(..., description="KPI status (on_track, at_risk, off_track)")
    trend: str = Field(..., description="Trend direction (up, down, stable)")
    calculated_at: datetime


class DataExportRequest(BaseModel):
    """Data export request model."""
    export_type: str = Field(..., description="Type of data to export")
    format: str = Field(..., description="Export format (csv, excel, json)")
    filters: Dict[str, Any] = Field(default={}, description="Data filters")
    tenant_id: str


class DataExportResponse(BaseModel):
    """Data export response model."""
    export_id: str
    export_type: str
    format: str
    status: str = Field(..., description="Export status (pending, processing, completed, failed)")
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AlertRuleCreate(BaseModel):
    """Alert rule creation model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    metric_name: str = Field(..., description="Metric to monitor")
    condition: Dict[str, Any] = Field(..., description="Alert condition")
    threshold: float = Field(..., description="Alert threshold")
    notification_channels: List[str] = Field(default=[], description="Notification channels")
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class AlertRuleUpdate(BaseModel):
    """Alert rule update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    metric_name: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    threshold: Optional[float] = None
    notification_channels: Optional[List[str]] = None
    status: Optional[StatusEnum] = None


class AlertRuleResponse(BaseEntity):
    """Alert rule response model."""
    name: str
    description: Optional[str] = None
    metric_name: str
    condition: Dict[str, Any]
    threshold: float
    notification_channels: List[str]
    status: StatusEnum
    last_triggered: Optional[datetime] = None


class AlertRule(BaseEntity):
    """Alert rule entity model."""
    name: str
    description: Optional[str] = None
    metric_name: str
    condition: Dict[str, Any]
    threshold: float
    notification_channels: List[str]
    status: StatusEnum
    last_triggered: Optional[datetime] = None 