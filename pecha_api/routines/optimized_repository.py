"""
Optimized repository functions for routines to reduce memory usage and improve performance
"""
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import text
from uuid import UUID
from typing import List, Dict, Optional
from .routines_models import Routine, RoutineTimeBlock, RoutineSession
from .routines_enums import SessionType
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.users.plan_users_models import UserPlanProgress


def get_user_routine_optimized(
    db: Session, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 20
) -> Optional[Dict]:
    """
    Optimized routine fetching with eager loading to reduce N+1 queries
    """
    # Single query to get routine with time blocks and sessions
    routine_query = (
        db.query(Routine)
        .filter(Routine.user_id == user_id, Routine.deleted_at.is_(None))
        .options(
            selectinload(Routine.time_blocks.and_(
                RoutineTimeBlock.deleted_at.is_(None)
            )).selectinload(RoutineTimeBlock.sessions)
        )
        .first()
    )
    
    if not routine_query:
        return None
    
    # Apply pagination to time blocks
    time_blocks = sorted(
        [tb for tb in routine_query.time_blocks if tb.deleted_at is None],
        key=lambda x: x.time_int
    )[skip:skip + limit]
    
    total_time_blocks = len([tb for tb in routine_query.time_blocks if tb.deleted_at is None])
    
    return {
        'routine': routine_query,
        'time_blocks': time_blocks,
        'total': total_time_blocks
    }


def get_plans_and_progress_batch(
    db: Session, 
    plan_ids: List[UUID], 
    user_id: UUID
) -> tuple[Dict[UUID, Plan], Dict[UUID, UserPlanProgress]]:
    """
    Batch fetch plans and user progress to minimize database queries
    """
    if not plan_ids:
        return {}, {}
    
    # Fetch all plans in a single query
    plans = db.query(Plan).filter(Plan.id.in_(plan_ids)).all()
    plan_map = {plan.id: plan for plan in plans}
    
    # Fetch all user progress in a single query  
    progress_records = (
        db.query(UserPlanProgress)
        .filter(
            UserPlanProgress.user_id == user_id,
            UserPlanProgress.plan_id.in_(plan_ids)
        )
        .all()
    )
    progress_map = {progress.plan_id: progress for progress in progress_records}
    
    return plan_map, progress_map


def get_routine_statistics(db: Session, user_id: UUID) -> Dict:
    """
    Get routine statistics efficiently using raw SQL for better performance
    """
    stats_query = text("""
        SELECT 
            COUNT(DISTINCT rtb.id) as total_time_blocks,
            COUNT(DISTINCT rs.id) as total_sessions,
            COUNT(DISTINCT CASE WHEN rs.session_type = :plan_type THEN rs.source_id END) as unique_plans,
            COUNT(DISTINCT CASE WHEN rs.session_type = :recitation_type THEN rs.source_id END) as unique_recitations
        FROM routines r
        LEFT JOIN routine_time_blocks rtb ON r.id = rtb.routine_id AND rtb.deleted_at IS NULL
        LEFT JOIN routine_sessions rs ON rtb.id = rs.time_block_id
        WHERE r.user_id = :user_id AND r.deleted_at IS NULL
    """)
    
    result = db.execute(stats_query, {
        'user_id': user_id,
        'plan_type': SessionType.PLAN.value,
        'recitation_type': SessionType.RECITATION.value
    }).fetchone()
    
    if result:
        return {
            'total_time_blocks': result[0] or 0,
            'total_sessions': result[1] or 0,
            'unique_plans': result[2] or 0,
            'unique_recitations': result[3] or 0
        }
    return {
        'total_time_blocks': 0,
        'total_sessions': 0, 
        'unique_plans': 0,
        'unique_recitations': 0
    }


def cleanup_orphaned_sessions(db: Session) -> int:
    """
    Clean up orphaned sessions that might be consuming memory
    """
    # Delete sessions for deleted time blocks
    deleted_count = db.execute(text("""
        DELETE FROM routine_sessions 
        WHERE time_block_id IN (
            SELECT id FROM routine_time_blocks 
            WHERE deleted_at IS NOT NULL
        )
    """)).rowcount
    
    db.commit()
    return deleted_count


def get_memory_heavy_routines(db: Session, limit: int = 10) -> List[Dict]:
    """
    Find routines that might be consuming excessive memory
    """
    query = text("""
        SELECT 
            r.user_id,
            r.id as routine_id,
            COUNT(DISTINCT rtb.id) as time_block_count,
            COUNT(rs.id) as session_count,
            COUNT(DISTINCT rs.source_id) as unique_source_count
        FROM routines r
        LEFT JOIN routine_time_blocks rtb ON r.id = rtb.routine_id AND rtb.deleted_at IS NULL
        LEFT JOIN routine_sessions rs ON rtb.id = rs.time_block_id
        WHERE r.deleted_at IS NULL
        GROUP BY r.user_id, r.id
        HAVING COUNT(rs.id) > 100  -- Routines with more than 100 sessions
        ORDER BY COUNT(rs.id) DESC
        LIMIT :limit
    """)
    
    results = db.execute(query, {'limit': limit}).fetchall()
    
    return [
        {
            'user_id': row[0],
            'routine_id': row[1], 
            'time_block_count': row[2],
            'session_count': row[3],
            'unique_source_count': row[4]
        }
        for row in results
    ]