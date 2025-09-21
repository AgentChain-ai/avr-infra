"""
Analytics API endpoints
Dashboard analytics and reporting
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Student, CallLog, ContextInfo, FieldConfiguration, CallStatus
from .auth import get_current_user, UserInfo

# Pydantic models for analytics responses
class DashboardSummary(BaseModel):
    total_students: int
    total_calls: int
    completion_rate: float
    active_context_items: int
    configured_fields: int
    system_health: str

class CallMetrics(BaseModel):
    total_calls: int
    successful_calls: int
    failed_calls: int
    completion_rate: float
    average_duration: float
    calls_by_status: Dict[str, int]

class StudentMetrics(BaseModel):
    total_students: int
    students_by_status: Dict[str, int]
    high_priority_students: int
    recent_additions: int
    completion_distribution: Dict[str, int]

class TimeSeriesData(BaseModel):
    date: str
    calls: int
    completed: int
    failed: int
    students_added: int

class TrendAnalysis(BaseModel):
    period: str
    daily_data: List[TimeSeriesData]
    trends: Dict[str, float]
    insights: List[str]

# Router setup
router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get overall dashboard summary statistics"""
    
    # Student counts
    total_students = db.query(Student).count()
    
    # Call counts
    total_calls = db.query(CallLog).count()
    completed_calls = db.query(CallLog).filter(CallLog.call_status == CallStatus.COMPLETED).count()
    
    # Completion rate
    completion_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    
    # Context and configuration counts
    active_context = db.query(ContextInfo).filter(ContextInfo.is_active.is_(True)).count()
    configured_fields = db.query(FieldConfiguration).filter(FieldConfiguration.is_active.is_(True)).count()
    
    # System health (simplified check)
    system_health = "healthy"  # Would check AVR services, database performance, etc.
    
    return DashboardSummary(
        total_students=total_students,
        total_calls=total_calls,
        completion_rate=round(completion_rate, 2),
        active_context_items=active_context,
        configured_fields=configured_fields,
        system_health=system_health
    )

@router.get("/calls/metrics", response_model=CallMetrics)
async def get_call_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get detailed call performance metrics"""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Base query for date range
    calls_query = db.query(CallLog).filter(
        CallLog.created_at >= start_date,
        CallLog.created_at <= end_date
    )
    
    # Total counts
    total_calls = calls_query.count()
    
    # Status breakdown
    calls_by_status = {}
    successful_calls = 0
    failed_calls = 0
    
    for status in CallStatus:
        count = calls_query.filter(CallLog.call_status == status).count()
        calls_by_status[status.value] = count
        
        if status in [CallStatus.COMPLETED]:
            successful_calls += count
        elif status in [CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.BUSY]:
            failed_calls += count
    
    # Completion rate
    completion_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
    
    # Average duration (completed calls only)
    completed_calls_query = calls_query.filter(CallLog.call_status == CallStatus.COMPLETED)
    avg_duration = 0
    if successful_calls > 0:
        durations = [call.call_duration for call in completed_calls_query.all()]
        avg_duration = sum(durations) / len(durations) if durations else 0
    
    return CallMetrics(
        total_calls=total_calls,
        successful_calls=successful_calls,
        failed_calls=failed_calls,
        completion_rate=round(completion_rate, 2),
        average_duration=round(avg_duration, 2),
        calls_by_status=calls_by_status
    )

@router.get("/students/metrics", response_model=StudentMetrics)
async def get_student_metrics(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get student-related metrics"""
    
    # Total students
    total_students = db.query(Student).count()
    
    # Status breakdown
    students_by_status = {}
    for status in CallStatus:
        count = db.query(Student).filter(Student.call_status == status).count()
        students_by_status[status.value] = count
    
    # High priority students
    high_priority = db.query(Student).filter(Student.priority >= 5).count()
    
    # Recent additions (last 7 days)
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_additions = db.query(Student).filter(Student.created_at >= recent_cutoff).count()
    
    # Call completion distribution
    completion_distribution = {}
    call_count_query = db.query(Student.call_count, func.count(Student.id)).group_by(Student.call_count)
    for call_count, student_count in call_count_query.all():
        completion_distribution[f"{call_count} calls"] = student_count
    
    return StudentMetrics(
        total_students=total_students,
        students_by_status=students_by_status,
        high_priority_students=high_priority,
        recent_additions=recent_additions,
        completion_distribution=completion_distribution
    )

@router.get("/trends", response_model=TrendAnalysis)
async def get_trend_analysis(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get trend analysis with daily breakdown"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    daily_data = []
    
    # Generate daily data
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        # Calls for this day
        day_calls = db.query(CallLog).filter(
            CallLog.created_at >= day_start,
            CallLog.created_at < day_end
        ).count()
        
        # Completed calls for this day
        day_completed = db.query(CallLog).filter(
            CallLog.created_at >= day_start,
            CallLog.created_at < day_end,
            CallLog.call_status == CallStatus.COMPLETED
        ).count()
        
        # Failed calls for this day
        day_failed = db.query(CallLog).filter(
            CallLog.created_at >= day_start,
            CallLog.created_at < day_end,
            CallLog.call_status.in_([CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.BUSY])
        ).count()
        
        # Students added this day
        day_students = db.query(Student).filter(
            Student.created_at >= day_start,
            Student.created_at < day_end
        ).count()
        
        daily_data.append(TimeSeriesData(
            date=day_start.date().isoformat(),
            calls=day_calls,
            completed=day_completed,
            failed=day_failed,
            students_added=day_students
        ))
    
    # Calculate trends (simple linear trend)
    if len(daily_data) >= 7:
        # Calculate weekly trends
        recent_week = daily_data[-7:]
        prev_week = daily_data[-14:-7] if len(daily_data) >= 14 else daily_data[:7]
        
        recent_avg_calls = sum(d.calls for d in recent_week) / 7
        prev_avg_calls = sum(d.calls for d in prev_week) / 7
        
        call_trend = ((recent_avg_calls - prev_avg_calls) / prev_avg_calls * 100) if prev_avg_calls > 0 else 0
        
        recent_completion = sum(d.completed for d in recent_week)
        recent_total = sum(d.calls for d in recent_week)
        completion_rate = (recent_completion / recent_total * 100) if recent_total > 0 else 0
    else:
        call_trend = 0
        completion_rate = 0
    
    # Generate insights
    insights = []
    
    if call_trend > 10:
        insights.append("📈 Call volume has increased significantly in the past week")
    elif call_trend < -10:
        insights.append("📉 Call volume has decreased in the past week")
    else:
        insights.append("📊 Call volume is stable")
    
    if completion_rate > 80:
        insights.append("✅ High call completion rate - excellent performance")
    elif completion_rate > 60:
        insights.append("🎯 Good call completion rate")
    else:
        insights.append("⚠️ Call completion rate could be improved")
    
    # Check for busy periods
    peak_day = max(daily_data, key=lambda x: x.calls)
    if peak_day.calls > 0:
        insights.append(f"📅 Highest activity on {peak_day.date} with {peak_day.calls} calls")
    
    return TrendAnalysis(
        period=f"{days} days",
        daily_data=daily_data,
        trends={
            "call_volume_change_percent": round(call_trend, 2),
            "completion_rate_percent": round(completion_rate, 2)
        },
        insights=insights
    )

@router.get("/performance/hourly")
async def get_hourly_performance(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get hourly call performance breakdown"""
    
    # Parse date or use today
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.utcnow().date()
    
    # Get calls for the target date
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)
    
    hourly_data = []
    
    for hour in range(24):
        hour_start = day_start + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_calls = db.query(CallLog).filter(
            CallLog.created_at >= hour_start,
            CallLog.created_at < hour_end
        ).count()
        
        hour_completed = db.query(CallLog).filter(
            CallLog.created_at >= hour_start,
            CallLog.created_at < hour_end,
            CallLog.call_status == CallStatus.COMPLETED
        ).count()
        
        hourly_data.append({
            "hour": f"{hour:02d}:00",
            "calls": hour_calls,
            "completed": hour_completed,
            "completion_rate": (hour_completed / hour_calls * 100) if hour_calls > 0 else 0
        })
    
    # Find peak hours
    peak_hour = max(hourly_data, key=lambda x: x["calls"])
    best_completion_hour = max(hourly_data, key=lambda x: x["completion_rate"]) if any(h["calls"] > 0 for h in hourly_data) else None
    
    return {
        "date": target_date.isoformat(),
        "hourly_breakdown": hourly_data,
        "peak_hour": peak_hour["hour"],
        "peak_calls": peak_hour["calls"],
        "best_completion_hour": best_completion_hour["hour"] if best_completion_hour else None,
        "best_completion_rate": best_completion_hour["completion_rate"] if best_completion_hour else 0
    }

@router.get("/export/report")
async def export_analytics_report(
    format: str = "json",
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Export comprehensive analytics report"""
    
    # Gather all analytics data
    summary = await get_dashboard_summary(db, current_user)
    call_metrics = await get_call_metrics(days, db, current_user)
    student_metrics = await get_student_metrics(db, current_user)
    trends = await get_trend_analysis(days, db, current_user)
    
    report_data = {
        "report_generated": datetime.utcnow().isoformat(),
        "report_period_days": days,
        "summary": summary.dict(),
        "call_metrics": call_metrics.dict(),
        "student_metrics": student_metrics.dict(),
        "trend_analysis": trends.dict()
    }
    
    if format.lower() == "json":
        return report_data
    
    elif format.lower() == "csv":
        from fastapi.responses import StreamingResponse
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary data
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Students", summary.total_students])
        writer.writerow(["Total Calls", summary.total_calls])
        writer.writerow(["Completion Rate %", summary.completion_rate])
        writer.writerow(["Active Context Items", summary.active_context_items])
        writer.writerow(["Configured Fields", summary.configured_fields])
        writer.writerow([])
        
        # Write daily trend data
        writer.writerow(["Daily Trends"])
        writer.writerow(["Date", "Calls", "Completed", "Failed", "Students Added"])
        for day_data in trends.daily_data:
            writer.writerow([day_data.date, day_data.calls, day_data.completed, day_data.failed, day_data.students_added])
        
        output.seek(0)
        
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'csv'")

@router.get("/health/system")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get system health and performance indicators"""
    
    # Database health
    try:
        db.execute("SELECT 1")
        db_health = "healthy"
    except Exception:
        db_health = "unhealthy"
    
    # Check for data quality issues
    warnings = []
    
    # Students without phone numbers
    students_no_phone = db.query(Student).filter(Student.phone_number.is_(None)).count()
    if students_no_phone > 0:
        warnings.append(f"{students_no_phone} students without phone numbers")
    
    # Calls without duration (might indicate incomplete calls)
    calls_no_duration = db.query(CallLog).filter(
        CallLog.call_status == CallStatus.COMPLETED,
        CallLog.call_duration == 0
    ).count()
    if calls_no_duration > 0:
        warnings.append(f"{calls_no_duration} completed calls without duration recorded")
    
    # Check for old pending calls
    old_pending = db.query(CallLog).filter(
        CallLog.call_status == CallStatus.PENDING,
        CallLog.created_at < datetime.utcnow() - timedelta(hours=24)
    ).count()
    if old_pending > 0:
        warnings.append(f"{old_pending} calls pending for over 24 hours")
    
    return {
        "overall_health": "healthy" if db_health == "healthy" and len(warnings) == 0 else "warning",
        "database_health": db_health,
        "data_warnings": warnings,
        "last_checked": datetime.utcnow().isoformat(),
        "recommendations": [
            "Regular data backup recommended",
            "Monitor call completion rates",
            "Review pending calls regularly"
        ] if len(warnings) == 0 else ["Address data quality warnings"]
    }
