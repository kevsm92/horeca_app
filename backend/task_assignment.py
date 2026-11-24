"""Offline task reassignment with venue-scoped, append-only provenance.

Caller must authenticate actor and authorize assignment in the venue before use.
Staff membership validation requires a trusted staff directory in a later increment.
"""
from backend.operations_tasks import _time


def assign_task(db, *, venue_id, task_id, actor_id, assignee_id, occurred_at):
    if not all(isinstance(v, str) and v.strip() for v in
               (venue_id, task_id, actor_id, assignee_id)):
        raise ValueError('venue, task, actor and assignee required')
    at = _time(occurred_at)
    db.execute('PRAGMA foreign_keys=ON')
    with db:
        current = db.execute(
            'SELECT assignee_id, status FROM tasks WHERE venue_id=? AND task_id=?',
            (venue_id, task_id)).fetchone()
        if current is None:
            raise ValueError('task not found in venue')
        if current[1] != 'open':
            raise ValueError('completed task cannot be reassigned')
        if current[0] == assignee_id:
            return False
        db.execute('UPDATE tasks SET assignee_id=? WHERE venue_id=? AND task_id=? AND status=?',
                   (assignee_id, venue_id, task_id, 'open'))
        db.execute('INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES(?,?,?,?,?)',
                   (venue_id, task_id, actor_id, 'assigned', at))
    return True
