"""
Core scheduling logic for WFM.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class Scheduler:
    """Core scheduling algorithm for job assignment."""
    
    def __init__(self):
        self.scheduling_strategies = {
            "round_robin": self._round_robin_schedule,
            "least_loaded": self._least_loaded_schedule,
            "skill_based": self._skill_based_schedule,
            "priority_based": self._priority_based_schedule
        }
    
    def schedule_job(self, job: Dict[str, Any], analysts: List[Dict[str, Any]], strategy: str = "skill_based") -> Optional[Dict[str, Any]]:
        """Schedule a job using the specified strategy."""
        try:
            if strategy in self.scheduling_strategies:
                return self.scheduling_strategies[strategy](job, analysts)
            else:
                logger.warning(f"Unknown scheduling strategy: {strategy}, using skill_based")
                return self.scheduling_strategies["skill_based"](job, analysts)
                
        except Exception as e:
            logger.error(f"Error scheduling job: {str(e)}")
            return None
    
    def _round_robin_schedule(self, job: Dict[str, Any], analysts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Round-robin scheduling strategy."""
        try:
            # Filter available analysts
            available_analysts = [
                analyst for analyst in analysts
                if analyst["status"] == "active" and 
                analyst["current_job_count"] < analyst["max_concurrent_jobs"]
            ]
            
            if not available_analysts:
                return None
            
            # Simple round-robin: pick the analyst with the least current jobs
            best_analyst = min(available_analysts, key=lambda x: x["current_job_count"])
            
            return self._create_schedule(job, best_analyst)
            
        except Exception as e:
            logger.error(f"Error in round-robin scheduling: {str(e)}")
            return None
    
    def _least_loaded_schedule(self, job: Dict[str, Any], analysts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Least-loaded scheduling strategy."""
        try:
            # Filter available analysts
            available_analysts = [
                analyst for analyst in analysts
                if analyst["status"] == "active" and 
                analyst["current_job_count"] < analyst["max_concurrent_jobs"]
            ]
            
            if not available_analysts:
                return None
            
            # Find analyst with lowest workload percentage
            best_analyst = min(
                available_analysts,
                key=lambda x: x["current_job_count"] / x["max_concurrent_jobs"]
            )
            
            return self._create_schedule(job, best_analyst)
            
        except Exception as e:
            logger.error(f"Error in least-loaded scheduling: {str(e)}")
            return None
    
    def _skill_based_schedule(self, job: Dict[str, Any], analysts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Skill-based scheduling strategy."""
        try:
            # Filter available analysts
            available_analysts = [
                analyst for analyst in analysts
                if analyst["status"] == "active" and 
                analyst["current_job_count"] < analyst["max_concurrent_jobs"]
            ]
            
            if not available_analysts:
                return None
            
            # Calculate skill match scores
            scored_analysts = []
            for analyst in available_analysts:
                score = self._calculate_skill_match(job, analyst)
                scored_analysts.append((analyst, score))
            
            # Sort by skill match score (highest first)
            scored_analysts.sort(key=lambda x: x[1], reverse=True)
            
            if scored_analysts and scored_analysts[0][1] > 0:
                return self._create_schedule(job, scored_analysts[0][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error in skill-based scheduling: {str(e)}")
            return None
    
    def _priority_based_schedule(self, job: Dict[str, Any], analysts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Priority-based scheduling strategy."""
        try:
            # Filter available analysts
            available_analysts = [
                analyst for analyst in analysts
                if analyst["status"] == "active" and 
                analyst["current_job_count"] < analyst["max_concurrent_jobs"]
            ]
            
            if not available_analysts:
                return None
            
            # For high priority jobs, prefer analysts with higher skill levels
            if job.get("priority") in ["high", "critical"]:
                return self._skill_based_schedule(job, analysts)
            else:
                return self._least_loaded_schedule(job, analysts)
            
        except Exception as e:
            logger.error(f"Error in priority-based scheduling: {str(e)}")
            return None
    
    def _calculate_skill_match(self, job: Dict[str, Any], analyst: Dict[str, Any]) -> float:
        """Calculate skill match between job and analyst."""
        try:
            # This is a simplified skill matching algorithm
            # In a real implementation, you would:
            # 1. Extract required skills from job tasks
            # 2. Compare with analyst skills
            # 3. Calculate a weighted score
            
            analyst_skills = set(analyst.get("skills", []))
            
            # Placeholder: assume job requires some skills
            required_skills = ["data_analysis", "reporting"]  # This would come from job tasks
            
            if not required_skills:
                return 0.5  # Default score if no skills specified
            
            matched_skills = len(set(required_skills) & analyst_skills)
            total_skills = len(required_skills)
            
            if total_skills == 0:
                return 0.0
            
            return matched_skills / total_skills
            
        except Exception as e:
            logger.error(f"Error calculating skill match: {str(e)}")
            return 0.0
    
    def _create_schedule(self, job: Dict[str, Any], analyst: Dict[str, Any]) -> Dict[str, Any]:
        """Create a schedule for job and analyst."""
        try:
            # Calculate start time (next available slot)
            start_time = datetime.utcnow() + timedelta(hours=1)
            
            # Calculate end time based on SLA
            sla_hours = job.get("sla_hours", 24)
            end_time = start_time + timedelta(hours=sla_hours)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(job, analyst)
            
            return {
                "analyst_id": analyst["id"],
                "analyst_name": analyst["name"],
                "start_time": start_time,
                "end_time": end_time,
                "confidence_score": confidence_score,
                "scheduling_reason": f"Selected based on availability and skills"
            }
            
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            return None
    
    def _calculate_confidence_score(self, job: Dict[str, Any], analyst: Dict[str, Any]) -> float:
        """Calculate confidence score for the schedule."""
        try:
            score = 0.0
            
            # Workload factor (30% weight)
            workload_factor = 1.0 - (analyst["current_job_count"] / analyst["max_concurrent_jobs"])
            score += workload_factor * 0.3
            
            # Skill match factor (40% weight)
            skill_match = self._calculate_skill_match(job, analyst)
            score += skill_match * 0.4
            
            # Availability factor (20% weight)
            availability_factor = 0.8  # Placeholder - would check actual availability
            score += availability_factor * 0.2
            
            # Performance history factor (10% weight)
            performance_factor = 0.8  # Placeholder - would check historical performance
            score += performance_factor * 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5


class AvailabilityChecker:
    """Check analyst availability and working hours."""
    
    def __init__(self):
        self.working_hours = {
            "monday": {"start": "09:00", "end": "17:00"},
            "tuesday": {"start": "09:00", "end": "17:00"},
            "wednesday": {"start": "09:00", "end": "17:00"},
            "thursday": {"start": "09:00", "end": "17:00"},
            "friday": {"start": "09:00", "end": "17:00"},
            "saturday": {"start": "10:00", "end": "14:00"},
            "sunday": {"start": "00:00", "end": "00:00"}  # Not working
        }
    
    def is_available(self, analyst: Dict[str, Any], start_time: datetime, end_time: datetime) -> bool:
        """Check if analyst is available during the specified time period."""
        try:
            # Check if analyst is active
            if analyst["status"] != "active":
                return False
            
            # Check current workload
            if analyst["current_job_count"] >= analyst["max_concurrent_jobs"]:
                return False
            
            # Check working hours
            if not self._is_within_working_hours(start_time, end_time):
                return False
            
            # Check for schedule conflicts
            if self._has_schedule_conflict(analyst, start_time, end_time):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return False
    
    def _is_within_working_hours(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if time period is within working hours."""
        try:
            # This is a simplified check
            # In a real implementation, you would check against analyst's specific schedule
            
            # For now, assume standard business hours
            start_hour = start_time.hour
            end_hour = end_time.hour
            
            # Check if it's a weekday
            if start_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            # Check if within business hours (9 AM to 5 PM)
            return 9 <= start_hour < 17 and 9 <= end_hour <= 17
            
        except Exception as e:
            logger.error(f"Error checking working hours: {str(e)}")
            return False
    
    def _has_schedule_conflict(self, analyst: Dict[str, Any], start_time: datetime, end_time: datetime) -> bool:
        """Check if there's a schedule conflict for the analyst."""
        try:
            # This would check against existing schedules
            # For now, return False (no conflicts)
            return False
            
        except Exception as e:
            logger.error(f"Error checking schedule conflicts: {str(e)}")
            return True  # Assume conflict if error 