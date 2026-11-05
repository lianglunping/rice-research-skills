"""Pure optional repair-cycle bookkeeping; no job, journal or scheduling IO."""
import copy
import math


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def count(value):
    return type(value) is int and value >= 0


def validate_budget(state):
    mode = state.get('repair_budget_mode', 'FIXED')
    if mode not in {'FIXED', 'RENEWABLE'}:
        raise ValueError('Unsupported repair budget mode')
    hard = state.get('repair_hard_limit')
    if hard is not None and (not count(hard) or hard == 0):
        raise ValueError('Fixed task cap must be a positive integer')
    if mode == 'FIXED':
        return
    if (not nonempty(state.get('scope_fingerprint')) or
            not nonempty(state.get('repair_renewal_authority'))):
        raise ValueError('Renewable budget requires scope and renewal authority')
    total = state.get('total_repair_attempts')
    lifetime = state.get('repair_attempts_by_issue')
    current = state.get('repair_cycle_attempts')
    by_issue = state.get('repair_cycle_attempts_by_issue')
    log = state.get('repair_renewal_log')
    if not isinstance(log, list):
        raise ValueError('Missing renewal history')
    expected = {}
    archived = 0
    for receipt in log:
        if (not isinstance(receipt, dict) or receipt.get('run_id') != state['run_id'] or
                receipt.get('scope_fingerprint') != state['scope_fingerprint']):
            raise ValueError('Renewal receipt belongs to a different run or scope')
        values = receipt.get('cycle_attempts_by_issue')
        n = receipt.get('cycle_attempts')
        if not isinstance(values, dict) or not count(n) or n == 0:
            raise ValueError('Invalid archived cycle')
        if any(not nonempty(k) or not count(v) for k, v in values.items()):
            raise ValueError('Invalid archived issue counts')
        if sum(values.values()) != n:
            raise ValueError('Archived counts do not reconcile')
        archived += n
        for key, value in values.items():
            expected[key] = expected.get(key, 0) + value
    if (not count(total) or not count(current) or not isinstance(lifetime, dict) or
            not isinstance(by_issue, dict) or
            any(not nonempty(k) or not count(v) for k, v in by_issue.items()) or
            any(not nonempty(k) or not count(v) for k, v in lifetime.items())):
        raise ValueError('Invalid repair counts')
    for key, value in by_issue.items():
        expected[key] = expected.get(key, 0) + value
    if (sum(by_issue.values()) != current or archived + current != total or
            expected != lifetime):
        raise ValueError('Current, archived and lifetime repair counts do not reconcile')


def budget_status(state, issue_key, per_issue, per_cycle):
    validate_budget(state)
    if (state.get('repair_stop_reason') or
            (state.get('repair_hard_limit') is not None and
             state['total_repair_attempts'] >= state['repair_hard_limit'])):
        return 'DECISION_REQUIRED'
    renewable = state.get('repair_budget_mode', 'FIXED') == 'RENEWABLE'
    values = state['repair_cycle_attempts_by_issue'] if renewable else state['repair_attempts_by_issue']
    total = state['repair_cycle_attempts'] if renewable else state['total_repair_attempts']
    if values.get(issue_key, 0) >= per_issue or total >= per_cycle:
        return 'REVIEW_REPAIR_CYCLE' if renewable else 'DECISION_REQUIRED'
    return 'AVAILABLE'


def count_repair(state, issue_key):
    """Update an already validated copy; reservations count before side effects."""
    state['repair_attempts_by_issue'][issue_key] = state['repair_attempts_by_issue'].get(issue_key, 0) + 1
    state['total_repair_attempts'] += 1
    if state.get('repair_budget_mode', 'FIXED') == 'RENEWABLE':
        values = state['repair_cycle_attempts_by_issue']
        values[issue_key] = values.get(issue_key, 0) + 1
        state['repair_cycle_attempts'] += 1


def renew_repair_budget(previous, *, run_id, scope_fingerprint, issue_key, now,
                       diagnosis, next_approach, evidence, recovery_gate,
                       per_issue, per_cycle, reservation_outcomes=None):
    """Return a reviewed cycle; caller verifies evidence and persists atomically.

    recovery_gate is a caller attestation, never remote proof from this helper.
    reservation_outcomes maps outstanding reserved IDs to verified failure-journal
    evidence; reconciling them here records FAILED, not another executed action.
    """
    validate_budget(previous)
    if (previous.get('repair_budget_mode') != 'RENEWABLE' or previous['closed'] or
            previous['authority'] != 'REPAIR_PREAUTHORIZED' or
            not nonempty(previous.get('approval_evidence')) or
            previous.get('decision') != 'REVIEW_REPAIR_CYCLE' or
            run_id != previous['run_id'] or scope_fingerprint != previous['scope_fingerprint'] or
            not previous['anomaly_checks'] or issue_key != previous['issue_key'] or
            type(now) not in (int, float) or not math.isfinite(now) or
            now < previous['last_observed_at']):
        raise ValueError('Renewal mode, authority, identity, failure or time invalid')
    if budget_status(previous, issue_key, per_issue, per_cycle) != 'REVIEW_REPAIR_CYCLE':
        raise ValueError('Renewal requires a reached review threshold and no hard stop')
    if not all(nonempty(v) for v in [diagnosis, next_approach, evidence]):
        raise ValueError('Diagnosis, distinct next approach and useful evidence required')
    gates = ['payload_ended', 'lock_safe', 'within_scope', 'resources_available', 'journals_reconciled']
    if (not isinstance(recovery_gate, dict) or
            any(recovery_gate.get(k) is not True for k in gates) or
            not nonempty(recovery_gate.get('evidence'))):
        raise ValueError('Verified safe recovery and resource evidence required')
    signature = (issue_key, diagnosis, next_approach, evidence)
    if any((r.get('issue_key'), r.get('diagnosis'), r.get('next_approach'), r.get('evidence')) ==
           signature for r in previous['repair_renewal_log']):
        raise ValueError('Repeated renewal without a new method or evidence')
    outcomes = {} if reservation_outcomes is None else reservation_outcomes
    reserved = [r for r in previous.get('repair_history', []) if r['status'] == 'RESERVED']
    if (not isinstance(outcomes, dict) or set(outcomes) != {r['repair_id'] for r in reserved} or
            any(not nonempty(v) for v in outcomes.values())):
        raise ValueError('Reconcile every outstanding reservation with verified failure evidence')
    s = copy.deepcopy(previous)
    for record in s.get('repair_history', []):
        if record['status'] == 'RESERVED':
            record.update(status='FAILED', failure_evidence=outcomes[record['repair_id']])
    s['repair_renewal_log'].append(dict(
        cycle_id=len(s['repair_renewal_log']) + 1, run_id=run_id,
        scope_fingerprint=scope_fingerprint, issue_key=issue_key,
        cycle_attempts=s['repair_cycle_attempts'],
        cycle_attempts_by_issue=copy.deepcopy(s['repair_cycle_attempts_by_issue']),
        total_repair_attempts=s['total_repair_attempts'], diagnosis=diagnosis,
        next_approach=next_approach, evidence=evidence,
        recovery_gate=copy.deepcopy(recovery_gate),
        authority_evidence=s['repair_renewal_authority'], recorded_at=now))
    s.update(repair_cycle_attempts=0, repair_cycle_attempts_by_issue={},
             last_observed_at=now, decision='LOCALIZE_AND_RECOVER_WITHIN_AUTHORITY',
             reason='Reviewed repair cycle renewed; cumulative evidence preserved')
    validate_budget(s)
    return s
