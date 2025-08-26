"""
Core analytics logic for WFM.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
import json

logger = structlog.get_logger(__name__)


class AnalyticsEngine:
    """Core analytics engine for data analysis and reporting."""
    
    def __init__(self):
        self.aggregation_functions = {
            "sum": self._sum_aggregation,
            "avg": self._avg_aggregation,
            "count": self._count_aggregation,
            "min": self._min_aggregation,
            "max": self._max_aggregation,
            "median": self._median_aggregation
        }
    
    def analyze_data(self, data: List[Dict[str, Any]], analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data based on configuration."""
        try:
            analysis_type = analysis_config.get("type", "basic")
            
            if analysis_type == "time_series":
                return self._analyze_time_series(data, analysis_config)
            elif analysis_type == "aggregation":
                return self._analyze_aggregation(data, analysis_config)
            elif analysis_type == "trend":
                return self._analyze_trend(data, analysis_config)
            elif analysis_type == "distribution":
                return self._analyze_distribution(data, analysis_config)
            else:
                return self._analyze_basic(data, analysis_config)
                
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_time_series(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze time series data."""
        try:
            time_field = config.get("time_field", "timestamp")
            value_field = config.get("value_field", "value")
            interval = config.get("interval", "day")
            
            # Group data by time interval
            grouped_data = self._group_by_time_interval(data, time_field, interval)
            
            # Calculate statistics for each interval
            series_data = []
            for interval_key, interval_data in grouped_data.items():
                values = [item.get(value_field, 0) for item in interval_data]
                
                series_data.append({
                    "interval": interval_key,
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                })
            
            return {
                "type": "time_series",
                "data": series_data,
                "summary": self._calculate_series_summary(series_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time series: {str(e)}")
            return {"type": "time_series", "data": [], "summary": {}}
    
    def _analyze_aggregation(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data with aggregations."""
        try:
            group_by = config.get("group_by", [])
            aggregations = config.get("aggregations", [])
            
            if not group_by:
                # Single aggregation without grouping
                return self._single_aggregation(data, aggregations)
            else:
                # Grouped aggregation
                return self._grouped_aggregation(data, group_by, aggregations)
                
        except Exception as e:
            logger.error(f"Error analyzing aggregation: {str(e)}")
            return {"type": "aggregation", "data": [], "summary": {}}
    
    def _analyze_trend(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trend in data."""
        try:
            time_field = config.get("time_field", "timestamp")
            value_field = config.get("value_field", "value")
            
            # Sort data by time
            sorted_data = sorted(data, key=lambda x: x.get(time_field, ""))
            
            if len(sorted_data) < 2:
                return {"type": "trend", "trend": "insufficient_data", "slope": 0}
            
            # Calculate trend using linear regression
            x_values = list(range(len(sorted_data)))
            y_values = [item.get(value_field, 0) for item in sorted_data]
            
            slope = self._calculate_slope(x_values, y_values)
            
            # Determine trend direction
            if slope > 0.1:
                trend = "increasing"
            elif slope < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "type": "trend",
                "trend": trend,
                "slope": slope,
                "data_points": len(sorted_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {str(e)}")
            return {"type": "trend", "trend": "error", "slope": 0}
    
    def _analyze_distribution(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze distribution of data."""
        try:
            value_field = config.get("value_field", "value")
            bins = config.get("bins", 10)
            
            values = [item.get(value_field, 0) for item in data]
            
            if not values:
                return {"type": "distribution", "bins": [], "summary": {}}
            
            # Calculate histogram
            min_val = min(values)
            max_val = max(values)
            bin_width = (max_val - min_val) / bins if max_val != min_val else 1
            
            histogram = [0] * bins
            for value in values:
                bin_index = min(int((value - min_val) / bin_width), bins - 1)
                histogram[bin_index] += 1
            
            # Create bin labels
            bin_labels = []
            for i in range(bins):
                start_val = min_val + i * bin_width
                end_val = min_val + (i + 1) * bin_width
                bin_labels.append(f"{start_val:.2f}-{end_val:.2f}")
            
            return {
                "type": "distribution",
                "bins": [{"range": label, "count": count} for label, count in zip(bin_labels, histogram)],
                "summary": {
                    "min": min_val,
                    "max": max_val,
                    "mean": sum(values) / len(values),
                    "median": self._calculate_median(values),
                    "std_dev": self._calculate_std_dev(values)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing distribution: {str(e)}")
            return {"type": "distribution", "bins": [], "summary": {}}
    
    def _analyze_basic(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Basic data analysis."""
        try:
            value_field = config.get("value_field", "value")
            values = [item.get(value_field, 0) for item in data]
            
            if not values:
                return {"type": "basic", "summary": {}}
            
            return {
                "type": "basic",
                "summary": {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "median": self._calculate_median(values)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in basic analysis: {str(e)}")
            return {"type": "basic", "summary": {}}
    
    def _group_by_time_interval(self, data: List[Dict[str, Any]], time_field: str, interval: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by time interval."""
        grouped = {}
        
        for item in data:
            timestamp = item.get(time_field)
            if not timestamp:
                continue
            
            # Convert to datetime if string
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    continue
            
            # Create interval key
            if interval == "hour":
                interval_key = timestamp.strftime("%Y-%m-%d %H:00")
            elif interval == "day":
                interval_key = timestamp.strftime("%Y-%m-%d")
            elif interval == "week":
                week_start = timestamp - timedelta(days=timestamp.weekday())
                interval_key = week_start.strftime("%Y-%m-%d")
            elif interval == "month":
                interval_key = timestamp.strftime("%Y-%m")
            else:
                interval_key = timestamp.strftime("%Y-%m-%d")
            
            if interval_key not in grouped:
                grouped[interval_key] = []
            grouped[interval_key].append(item)
        
        return grouped
    
    def _single_aggregation(self, data: List[Dict[str, Any]], aggregations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform single aggregation without grouping."""
        try:
            results = {}
            
            for agg in aggregations:
                field = agg.get("field", "value")
                function = agg.get("function", "sum")
                alias = agg.get("alias", f"{function}_{field}")
                
                values = [item.get(field, 0) for item in data]
                
                if function in self.aggregation_functions:
                    results[alias] = self.aggregation_functions[function](values)
                else:
                    results[alias] = 0
            
            return {
                "type": "aggregation",
                "data": results,
                "summary": {"total_records": len(data)}
            }
            
        except Exception as e:
            logger.error(f"Error in single aggregation: {str(e)}")
            return {"type": "aggregation", "data": {}, "summary": {}}
    
    def _grouped_aggregation(self, data: List[Dict[str, Any]], group_by: List[str], aggregations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform grouped aggregation."""
        try:
            # Group data
            grouped_data = {}
            for item in data:
                group_key = tuple(item.get(field, "") for field in group_by)
                if group_key not in grouped_data:
                    grouped_data[group_key] = []
                grouped_data[group_key].append(item)
            
            # Calculate aggregations for each group
            results = []
            for group_key, group_items in grouped_data.items():
                group_result = {
                    "group": dict(zip(group_by, group_key))
                }
                
                for agg in aggregations:
                    field = agg.get("field", "value")
                    function = agg.get("function", "sum")
                    alias = agg.get("alias", f"{function}_{field}")
                    
                    values = [item.get(field, 0) for item in group_items]
                    
                    if function in self.aggregation_functions:
                        group_result[alias] = self.aggregation_functions[function](values)
                    else:
                        group_result[alias] = 0
                
                results.append(group_result)
            
            return {
                "type": "aggregation",
                "data": results,
                "summary": {"total_groups": len(results), "total_records": len(data)}
            }
            
        except Exception as e:
            logger.error(f"Error in grouped aggregation: {str(e)}")
            return {"type": "aggregation", "data": [], "summary": {}}
    
    def _calculate_series_summary(self, series_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary for time series data."""
        try:
            if not series_data:
                return {}
            
            all_values = []
            for item in series_data:
                all_values.extend([item.get("sum", 0), item.get("avg", 0)])
            
            return {
                "total_intervals": len(series_data),
                "total_sum": sum(item.get("sum", 0) for item in series_data),
                "avg_per_interval": sum(item.get("avg", 0) for item in series_data) / len(series_data),
                "min_interval": min(item.get("sum", 0) for item in series_data),
                "max_interval": max(item.get("sum", 0) for item in series_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating series summary: {str(e)}")
            return {}
    
    def _calculate_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate slope using linear regression."""
        try:
            n = len(x_values)
            if n != len(y_values) or n < 2:
                return 0
            
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            return slope
            
        except Exception as e:
            logger.error(f"Error calculating slope: {str(e)}")
            return 0
    
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median of values."""
        try:
            if not values:
                return 0
            
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            if n % 2 == 0:
                return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            else:
                return sorted_values[n // 2]
                
        except Exception as e:
            logger.error(f"Error calculating median: {str(e)}")
            return 0
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        try:
            if not values:
                return 0
            
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return variance ** 0.5
            
        except Exception as e:
            logger.error(f"Error calculating standard deviation: {str(e)}")
            return 0
    
    # Aggregation functions
    def _sum_aggregation(self, values: List[float]) -> float:
        """Sum aggregation."""
        return sum(values)
    
    def _avg_aggregation(self, values: List[float]) -> float:
        """Average aggregation."""
        return sum(values) / len(values) if values else 0
    
    def _count_aggregation(self, values: List[float]) -> int:
        """Count aggregation."""
        return len(values)
    
    def _min_aggregation(self, values: List[float]) -> float:
        """Minimum aggregation."""
        return min(values) if values else 0
    
    def _max_aggregation(self, values: List[float]) -> float:
        """Maximum aggregation."""
        return max(values) if values else 0
    
    def _median_aggregation(self, values: List[float]) -> float:
        """Median aggregation."""
        return self._calculate_median(values)


class ReportGenerator:
    """Generate various types of reports."""
    
    def __init__(self):
        self.report_templates = {
            "performance": self._generate_performance_report,
            "issues": self._generate_issues_report,
            "scheduling": self._generate_scheduling_report,
            "analytics": self._generate_analytics_report
        }
    
    def generate_report(self, report_type: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report based on type."""
        try:
            if report_type in self.report_templates:
                return self.report_templates[report_type](data, config)
            else:
                return self._generate_custom_report(data, config)
                
        except Exception as e:
            logger.error(f"Error generating report {report_type}: {str(e)}")
            return {"error": str(e)}
    
    def _generate_performance_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance report."""
        try:
            return {
                "type": "performance",
                "title": "Performance Report",
                "generated_at": datetime.utcnow().isoformat(),
                "sections": [
                    {
                        "title": "Job Completion Summary",
                        "data": data.get("job_summary", {})
                    },
                    {
                        "title": "Analyst Performance",
                        "data": data.get("analyst_performance", {})
                    },
                    {
                        "title": "SLA Compliance",
                        "data": data.get("sla_compliance", {})
                    }
                ],
                "summary": {
                    "total_jobs": data.get("total_jobs", 0),
                    "avg_completion_time": data.get("avg_completion_time", 0),
                    "sla_compliance_rate": data.get("sla_compliance_rate", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {"type": "performance", "error": str(e)}
    
    def _generate_issues_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate issues report."""
        try:
            return {
                "type": "issues",
                "title": "Issues Report",
                "generated_at": datetime.utcnow().isoformat(),
                "sections": [
                    {
                        "title": "Issue Summary",
                        "data": data.get("issue_summary", {})
                    },
                    {
                        "title": "Issue Categories",
                        "data": data.get("issue_categories", {})
                    },
                    {
                        "title": "Resolution Times",
                        "data": data.get("resolution_times", {})
                    }
                ],
                "summary": {
                    "total_issues": data.get("total_issues", 0),
                    "resolved_issues": data.get("resolved_issues", 0),
                    "avg_resolution_time": data.get("avg_resolution_time", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating issues report: {str(e)}")
            return {"type": "issues", "error": str(e)}
    
    def _generate_scheduling_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scheduling report."""
        try:
            return {
                "type": "scheduling",
                "title": "Scheduling Report",
                "generated_at": datetime.utcnow().isoformat(),
                "sections": [
                    {
                        "title": "Schedule Summary",
                        "data": data.get("schedule_summary", {})
                    },
                    {
                        "title": "Analyst Utilization",
                        "data": data.get("analyst_utilization", {})
                    },
                    {
                        "title": "Job Distribution",
                        "data": data.get("job_distribution", {})
                    }
                ],
                "summary": {
                    "total_scheduled_jobs": data.get("total_scheduled_jobs", 0),
                    "avg_utilization": data.get("avg_utilization", 0),
                    "efficiency_score": data.get("efficiency_score", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating scheduling report: {str(e)}")
            return {"type": "scheduling", "error": str(e)}
    
    def _generate_analytics_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analytics report."""
        try:
            return {
                "type": "analytics",
                "title": "Analytics Report",
                "generated_at": datetime.utcnow().isoformat(),
                "sections": [
                    {
                        "title": "Key Metrics",
                        "data": data.get("key_metrics", {})
                    },
                    {
                        "title": "Trends",
                        "data": data.get("trends", {})
                    },
                    {
                        "title": "Insights",
                        "data": data.get("insights", {})
                    }
                ],
                "summary": {
                    "metrics_analyzed": data.get("metrics_analyzed", 0),
                    "trends_identified": data.get("trends_identified", 0),
                    "insights_generated": data.get("insights_generated", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating analytics report: {str(e)}")
            return {"type": "analytics", "error": str(e)}
    
    def _generate_custom_report(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom report."""
        try:
            return {
                "type": "custom",
                "title": config.get("title", "Custom Report"),
                "generated_at": datetime.utcnow().isoformat(),
                "data": data,
                "config": config
            }
            
        except Exception as e:
            logger.error(f"Error generating custom report: {str(e)}")
            return {"type": "custom", "error": str(e)} 