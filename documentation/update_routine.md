# Enrollment & Routine Separation Guidelines

## Core Principles
The WeBuddhist Backend maintains two distinct but related concepts:

**ENROLLMENT** = User's commitment to learning/tracking a plan or series  
**ROUTINE** = User's daily practice schedule (a filtered view of enrolled content)

### Key Rules:

✅ **Adding to routine → Auto-enrolls** (if not already enrolled)  
⛔ **Removing from routine → Does NOT unenroll** (preserves enrollment & progress)  
📊 **Progress tracking depends on enrollment, NOT routine**  
🔒 **Only enrolled plans can be added to routines** (auto-enroll if needed)  
🧹 **Auto-cleanup enrollments** when plans are deleted/unavailable  
🔄 **Plans can exist in multiple time blocks** (no re-enrollment needed)  

## Critical Behavior Changes Needed

### POST /routines/{routineId}/time-blocks
**NEW REQUIREMENT:** Auto-enroll users in all plans send in the body when creating new time blocks

```python
# When creating new time block with plans:
_enroll_plans_if_needed(user_id, plan_ids_in_new_timeblock)
```

### PUT /routines/{routineId}/time-blocks/{timeBlockId}
**CHANGE:** Stop calling `_unenroll_plans()` for removed plans

```python
# BEFORE (problematic):
_unenroll_plans(db=db, user_id=user_id, plan_ids=removed_plans)

# AFTER (correct):
# Only enroll new plans, don't unenroll removed ones
_enroll_plans_if_needed(user_id, added_plans)
```

### DELETE /routines/{routineId}/time-blocks/{timeBlockId}
**CHANGE:** Stop auto-unenrolling when deleting time blocks

```python
# REMOVE this line:
# _unenroll_plans(db=db, user_id=current_user.id, plan_ids=plan_ids)
```

### DELETE /users/me/plans/{planId}
**ENHANCE:** Remove from routine first, then unenroll

```python
def unenroll_from_plan(user_id, plan_id):
    # 1. Remove from all routine time blocks
    remove_plan_from_all_user_routines(user_id, plan_id)
    # 2. Then delete enrollment and progress  
    delete_user_plan_progress(user_id, plan_id)
```

### Plan Deletion/Unavailability
**NEW REQUIREMENT:** Automatic cleanup of orphaned data

```python
def cleanup_deleted_plan(plan_id):
    # 1. Remove from all user routines
    remove_plan_from_all_routines(plan_id)
    # 2. Clean up all user enrollments and progress
    cleanup_all_enrollments_for_plan(plan_id)
```

### Bulk Operations
**NEW REQUIREMENT:** Handle multiple plans consistently

```python
# For any bulk routine updates:
# - Auto-enroll all newly added plans
# - Do NOT unenroll removed plans
# - Validate all plans exist before processing
```

### Validation & Error Handling
**NEW REQUIREMENT:** Auto-enrollment when adding unenrolled plans

```python
# When adding plans to routine:
def add_plans_to_routine(user_id, routine_id, plan_ids):
    # 1. Auto-enroll user in any unenrolled plans (skip if already enrolled)
    _enroll_plans_if_needed(user_id, plan_ids)
    # 2. Then add to routine
    _add_plans_to_routine_timeblock(routine_id, plan_ids)
```

### Multiple Time Blocks Support
**NEW REQUIREMENT:** Handle plans across multiple time blocks

```python
# Plans can exist in multiple time blocks:
# - Same plan in different time blocks within one routine ✅
# - Same plan across different routines ✅  
# - No duplicate enrollment needed ✅
# - Removing from one time block keeps it in others ✅

def _enroll_plans_if_needed(user_id, plan_ids):
    """Only enroll if not already enrolled - prevents duplicates"""
    unenrolled_plans = get_unenrolled_plans(user_id, plan_ids)
    if unenrolled_plans:
        enroll_user_in_plans(user_id, unenrolled_plans)

def remove_plan_from_timeblock(user_id, timeblock_id, plan_id):
    """Remove from specific timeblock only - keep enrollment and other timeblocks"""
    remove_plan_from_specific_timeblock(timeblock_id, plan_id)
    # Do NOT unenroll - plan may exist in other timeblocks
```

## Key Benefits
- **Data Safety:** Users never accidentally lose progress when reorganizing routines
- **User Control:** Explicit unenrollment requires intentional action
- **Mental Clarity:** "Remove from routine" ≠ "Stop learning this"
- **Flexibility:** Can experiment with routine structure without fear
- **Consistency:** All routine operations follow same enrollment principles

## Implementation Priority
1. **High Priority:** Remove auto-unenrollment from routine operations
2. **High Priority:** Add auto-enrollment to POST/PUT routine operations
3. **Medium Priority:** Add routine cleanup to explicit unenrollment
4. **Medium Priority:** Implement plan deletion cleanup
5. **Low Priority:** UI enhancements and warnings