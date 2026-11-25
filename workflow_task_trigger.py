"""Pure offline task trigger policy; no notifications or compliance certification."""

def task_created_trigger(event_type: str, payload: dict) -> dict | None:
    """Map a task-created event to an internal manager review intent.

    Venue must come from authenticated context, not untrusted event payload.
    Does not write tasks, perform network I/O or mark SOP checks passed.
    """
    if event_type != 'task.created':
        return None
    if not isinstance(payload, dict):
        raise ValueError('payload must be an object')
    task_id = payload.get('task_id')
    priority = payload.get('priority')
    if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 128:
        raise ValueError('invalid task_id')
    if priority not in ('low', 'normal', 'high', 'critical'):
        raise ValueError('invalid priority')
    if priority not in ('high', 'critical'):
        return None
    return {'kind': 'manager_review_required', 'task_id': task_id,
            'reason': 'priority_escalation', 'requires_human_review': True}
