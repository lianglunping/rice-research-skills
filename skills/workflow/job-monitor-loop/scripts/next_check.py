#!/usr/bin/env python3
"""Calculate persistent monitoring decisions; never submit, repair, sleep or notify.

The caller supplies verified observations, applies the decision via its actual
monitoring backend and persists the returned state. See adaptive-monitor.md.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import time

from monitor_repair_budget import budget_status, count_repair, validate_budget
from monitor_repair_budget import renew_repair_budget as renew_reviewed_cycle

POLICY_PATH = Path(__file__).resolve().parents[1] / 'references/backoff-policy.json'
POLICY = json.loads(POLICY_PATH.read_text())
STATUSES = {'QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'UNKNOWN'}
MODES = {'OBSERVE_ONLY', 'REPAIR_PREAUTHORIZED', 'DECISION_REQUIRED'}


def renew_repair_budget(previous, **review):
    """Record a reviewed renewal using the current policy thresholds; no side effects."""
    return renew_reviewed_cycle(previous, per_issue=POLICY['maximum_repairs_per_issue'],
                               per_cycle=POLICY['maximum_repairs_per_run'], **review)


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def initialize(run_id, attempt, now, authority='OBSERVE_ONLY', approval_evidence=None,
               *, repair_budget_mode='FIXED', scope_fingerprint=None,
               renewal_authority=None, repair_hard_limit=None):
    if not run_id or not attempt or authority not in MODES or not finite_number(now):
        raise ValueError('Nonempty run/attempt, valid authority and finite time required')
    if authority == 'REPAIR_PREAUTHORIZED' and not approval_evidence:
        raise ValueError('Preauthorized recovery requires recorded user evidence')
    s = dict(policy_version=POLICY['version'], run_id=run_id, attempt=attempt,
                authority=authority, approval_evidence=approval_evidence,
                tier=0, normal_checks=0, anomaly_checks=0, unknown_checks=0,
                issue_key=None, last_status=None, last_observation_id=None,
                last_observed_at=now, last_progress_pct=None,
                next_check_at=now + 60, interval_seconds=60, countable_due=True,
                repair_attempts_by_issue={}, total_repair_attempts=0,
                closed=False, decision='MONITOR', reason='Initial stability window')
    if repair_budget_mode != 'FIXED':
        s.update(repair_budget_mode=repair_budget_mode, scope_fingerprint=scope_fingerprint,
                 repair_renewal_authority=renewal_authority, repair_cycle_attempts=0,
                 repair_cycle_attempts_by_issue={}, repair_renewal_log=[])
    if repair_hard_limit is not None:
        s['repair_hard_limit'] = repair_hard_limit
    validate_budget(s)
    return s


def decide(previous, observation, now):
    s = copy.deepcopy(previous)
    if s.get('policy_version') != POLICY['version']:
        raise ValueError('Policy version mismatch; migrate deliberately')
    validate_budget(s)
    if observation.get('run_id') != s['run_id']:
        raise ValueError('Observation belongs to a different logical run')
    if not finite_number(now) or now < s['last_observed_at']:
        raise ValueError('Observation time moved backwards or is not finite')
    oid = observation.get('observation_id')
    if not isinstance(oid, str) or not oid:
        raise ValueError('A unique nonempty observation_id is required')
    if oid == s['last_observation_id'] or s['closed']:
        return s
    status = observation.get('status')
    if status not in STATUSES:
        raise ValueError('Unsupported task status')
    if observation.get('attempt') != s['attempt']:
        raise ValueError('Use explicit recovery initialization for a new attempt')
    previous_due = s['next_check_at']
    due = previous_due is None or now >= previous_due
    s['last_observation_id'], s['last_observed_at'] = oid, now
    verified = observation.get('signal_verified') is True
    anomaly = status == 'FAILED' or observation.get('explicit_anomaly') is True
    if anomaly or (verified and status != 'UNKNOWN'):
        s['observability_issue_key'], s['diagnosed_unknown_checks'] = None, 0
    if anomaly:
        key = observation.get('issue_key')
        if not isinstance(key, str) or not key:
            key = 'UNCLASSIFIED'
        # Different wording/fingerprint does not rearm a repeated short window.
        if due or s['anomaly_checks'] == 0:
            s['anomaly_checks'] += 1
        s['normal_checks'], s['unknown_checks'] = 0, 0
        s['issue_key'] = key
        budget = budget_status(s, key, POLICY['maximum_repairs_per_issue'],
                               POLICY['maximum_repairs_per_run'])
        if s['authority'] == 'DECISION_REQUIRED' or budget == 'DECISION_REQUIRED':
            action = 'DECISION_REQUIRED'
        elif s['authority'] == 'REPAIR_PREAUTHORIZED':
            action = budget if budget == 'REVIEW_REPAIR_CYCLE' else 'LOCALIZE_AND_RECOVER_WITHIN_AUTHORITY'
        else:
            action = 'LOCALIZE_AND_REPORT'
        ladder = POLICY['anomaly_intervals_seconds']
        delay = ladder[min(s['anomaly_checks'] - 1, len(ladder) - 1)]
        reason = 'Failure evidence takes precedence; do not blindly repeat a repair'
    elif status == 'SUCCESS' and verified:
        accepted = (observation.get('acceptance_passed') is True and
                    bool(observation.get('acceptance_evidence')))
        s.update(closed=accepted, normal_checks=0, interval_seconds=None,
                 next_check_at=None, last_status=status,
                 decision='ACCEPTED' if accepted else 'ACCEPTANCE_REQUIRED',
                 reason='Stop payload polling; complete artifact and semantic acceptance')
        return s
    elif not verified or status == 'UNKNOWN':
        s['normal_checks'] = 0
        if due or s['unknown_checks'] == 0:
            s['unknown_checks'] += 1
        ladder = POLICY['unknown_intervals_seconds']
        delay = ladder[min(s['unknown_checks'] - 1, len(ladder) - 1)]
        gap = observation.get('observability_gap')
        diagnosed = (isinstance(gap, dict) and
                     isinstance(gap.get('issue_key'), str) and
                     bool(gap['issue_key'].strip()) and
                     isinstance(gap.get('diagnosis_evidence'), str) and
                     bool(gap['diagnosis_evidence'].strip()) and
                     gap.get('recovery_blocked') is True)
        if diagnosed:
            if s.get('observability_issue_key') != gap['issue_key']:
                s['diagnosed_unknown_checks'] = 0
            s['observability_issue_key'] = gap['issue_key']
            if due or not s.get('diagnosed_unknown_checks', 0):
                s['diagnosed_unknown_checks'] = s.get('diagnosed_unknown_checks', 0) + 1
            ladder = POLICY['diagnosed_unknown_intervals_seconds']
            delay = ladder[min(s['diagnosed_unknown_checks'] - 1, len(ladder) - 1)]
            # A prolonged telemetry outage must not erase a known completion cap.
            if s['last_progress_pct'] is not None:
                delay = min([delay] + [cap for threshold, cap in POLICY['progress_caps']
                                      if s['last_progress_pct'] >= threshold])
        else:
            s['observability_issue_key'], s['diagnosed_unknown_checks'] = None, 0
        phase_cap = observation.get('phase_interval_cap_seconds')
        if finite_number(phase_cap) and phase_cap >= 60:
            delay = min(delay, int(phase_cap))
        action, reason = 'RESTORE_OBSERVABILITY', 'Missing evidence is not a normal check'
        if diagnosed:
            reason = 'Diagnosed unchanged observability gap; bounded checks while recovery is blocked'
    else:
        restarted = s['last_status'] == 'QUEUED' and status == 'RUNNING'
        recovered = s['anomaly_checks'] > 0 or s['unknown_checks'] > 0
        if restarted or recovered:
            s['tier'], s['normal_checks'] = 0, 0
            if restarted:
                s['last_progress_pct'] = None
            due = False  # transition is a new baseline, not the first minute check
            s['next_check_at'] = now + 60
        s['anomaly_checks'], s['unknown_checks'], s['issue_key'] = 0, 0, None
        progress = observation.get('progress_pct')
        reliable_progress = (observation.get('progress_reliable') is True and
                             observation.get('progress_scope') == 'whole_run' and
                             finite_number(progress) and 0 <= progress <= 100)
        regressed = (reliable_progress and s['last_progress_pct'] is not None and
                     progress < s['last_progress_pct'])
        if reliable_progress and not regressed:
            s['last_progress_pct'] = progress
        eta = observation.get('eta_seconds')
        reliable_eta = (observation.get('eta_reliable') is True and
                        observation.get('eta_scope') == 'whole_run' and
                        finite_number(eta) and eta > 0)
        caps = []
        # A missing telemetry field cannot erase a verified completion lower bound.
        # Retain only the timing cap; never present an old percentage as fresh evidence.
        if s['last_progress_pct'] is not None:
            caps.extend(delay for threshold, delay in POLICY['progress_caps']
                        if s['last_progress_pct'] >= threshold)
        if reliable_eta and not regressed:
            caps.append(max(60, int(eta * POLICY['eta_fraction'])))
        else:
            caps.append(POLICY['without_reliable_eta_cap_seconds'])
        if regressed:
            caps.append(600)
            s['normal_checks'] = 0
        phase_cap = observation.get('phase_interval_cap_seconds')
        if finite_number(phase_cap) and phase_cap >= 60:
            caps.append(int(phase_cap))
        # Early events and progress-capped quick checks must not accelerate tiers.
        if due and not regressed and s['countable_due']:
            s['normal_checks'] += 1
            if s['normal_checks'] >= POLICY['normal_checks_to_promote'][s['tier']]:
                s['tier'] = min(s['tier'] + 1, len(POLICY['tiers_seconds']) - 1)
                s['normal_checks'] = 0
        delay = min(POLICY['tiers_seconds'][s['tier']], *caps)
        # Unscheduled progress events may bring a due time closer, never postpone it.
        if not due:
            delay = min(delay, max(0, s['next_check_at'] - now))
        action = 'VERIFY_PROGRESS' if regressed else 'MONITOR'
        reason = ('Progress regressed; verify denominator and stage mapping' if regressed else
                  'Stable tier capped by verified overall progress and remaining time')
    # Applies to anomalies and unknowns too: early callbacks cannot keep moving
    # an already scheduled observation away from the present.
    if previous_due is not None and now < previous_due:
        delay = min(delay, previous_due - now)
    if action in {'MONITOR', 'VERIFY_PROGRESS'}:
        if not due and now + delay == s['next_check_at'] and not (restarted or recovered):
            countable = s['countable_due']
        else:
            countable = delay >= POLICY['tiers_seconds'][s['tier']] and not regressed
    else:
        countable = False
    s.update(interval_seconds=delay, next_check_at=now + delay, countable_due=countable,
             last_status=status, decision=action, reason=reason)
    return s


def record_repair(previous, repair_id, now, issue_key, repair_evidence, repair_fingerprint):
    """Reserve a repair budget BEFORE its side effects; the caller must persist it.

    Failed fixes and failed submissions consume budget too. A reserved record is
    not proof that the action ran: reconcile its journal before retrying after a
    crash. The helper itself never performs any repair.
    """
    if (previous.get('policy_version') != POLICY['version'] or previous['closed'] or
            previous['authority'] != 'REPAIR_PREAUTHORIZED' or
            not previous.get('approval_evidence') or not finite_number(now) or
            now < previous['last_observed_at']):
        raise ValueError('Repair authority, state or time invalid')
    if (not previous['anomaly_checks'] or issue_key != previous['issue_key'] or
            not all(isinstance(v, str) and v for v in
                    [repair_id, issue_key, repair_evidence, repair_fingerprint])):
        raise ValueError('Repair requires current failure, identity and evidence')
    validate_budget(previous)
    history = previous.get('repair_history', [])
    for item in history:
        if item['repair_id'] == repair_id:
            if (item['source_attempt'] == previous['attempt'] and
                    item['status'] == 'RESERVED' and item['issue_key'] == issue_key and
                    item['repair_fingerprint'] == repair_fingerprint and
                    item['repair_evidence'] == repair_evidence):
                return copy.deepcopy(previous)
            raise ValueError('Repair ID already belongs to a different action')
        if (item['issue_key'] == issue_key and
                item['repair_fingerprint'] == repair_fingerprint):
            raise ValueError('Same incident and fix already attempted; submission is not resolution')
    if budget_status(previous, issue_key, POLICY['maximum_repairs_per_issue'],
                     POLICY['maximum_repairs_per_run']) != 'AVAILABLE':
        raise ValueError('Repair requires budget review or a hard stop decision')
    s = copy.deepcopy(previous)
    count_repair(s, issue_key)
    s.setdefault('repair_history', []).append(dict(
        repair_id=repair_id, issue_key=issue_key, repair_evidence=repair_evidence,
        repair_fingerprint=repair_fingerprint, source_attempt=s['attempt'],
        recorded_at=now, status='RESERVED'))
    s['last_observed_at'] = now
    return s


def recover(previous, new_attempt, now, issue_key, recovery_evidence, repair_id=None):
    """Record verified submission; pair with record_repair before actual repair.

    The legacy unreserved call remains readable for existing v2 integrations;
    it accounts for one repair but cannot track fixes that failed before it.
    New integrations must supply the previously reserved repair_id.
    """
    if (previous.get('policy_version') != POLICY['version'] or previous['closed'] or
            previous['authority'] != 'REPAIR_PREAUTHORIZED' or
            not recovery_evidence or not new_attempt or new_attempt == previous['attempt'] or
            not finite_number(now) or now < previous['last_observed_at']):
        raise ValueError('Recovery identity, authority, time or evidence invalid')
    if not previous['anomaly_checks'] or not issue_key or issue_key != previous['issue_key']:
        raise ValueError('Recovery must refer to the observed current failure')
    validate_budget(previous)
    if (previous.get('repair_stop_reason') or
            (previous.get('repair_hard_limit') is not None and
             previous['total_repair_attempts'] > previous['repair_hard_limit'])):
        raise ValueError('Recovery blocked by task resource or authority stop')
    if previous.get('repair_budget_mode') == 'RENEWABLE' and repair_id is None:
        raise ValueError('Renewable recovery requires a previously reserved repair')
    counts = dict(previous['repair_attempts_by_issue'])
    total = previous['total_repair_attempts']
    history = copy.deepcopy(previous.get('repair_history', []))
    if repair_id is not None:
        matches = [item for item in history if item['repair_id'] == repair_id]
        if (len(matches) != 1 or matches[0]['issue_key'] != issue_key or
                matches[0]['source_attempt'] != previous['attempt'] or
                matches[0]['status'] != 'RESERVED'):
            raise ValueError('Recovery requires the matching reserved repair')
        matches[0].update(status='SUBMITTED', new_attempt=new_attempt,
                          recovery_evidence=recovery_evidence)
    else:
        if any(item['source_attempt'] == previous['attempt'] and
               item['status'] == 'RESERVED' for item in history):
            raise ValueError('Supply repair_id for an already reserved repair')
        if budget_status(previous, issue_key, POLICY['maximum_repairs_per_issue'],
                         POLICY['maximum_repairs_per_run']) != 'AVAILABLE':
            raise ValueError('Repair budget exhausted')
        counts[issue_key] = counts.get(issue_key, 0) + 1
        total += 1
    s = initialize(previous['run_id'], new_attempt, now, previous['authority'],
                   previous['approval_evidence'])
    s.update(repair_attempts_by_issue=counts, total_repair_attempts=total,
             repair_history=history, previous_attempt=previous['attempt'],
             recovery_evidence=recovery_evidence)
    for key in ['repair_budget_mode', 'scope_fingerprint', 'repair_renewal_authority',
                'repair_cycle_attempts', 'repair_cycle_attempts_by_issue',
                'repair_renewal_log', 'repair_hard_limit', 'repair_stop_reason']:
        if key in previous:
            s[key] = copy.deepcopy(previous[key])
    validate_budget(s)
    return s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--observation', type=Path, required=True)
    parser.add_argument('--now', type=float, default=None)
    args = parser.parse_args()
    state = json.loads(args.state.read_text())
    observation = json.loads(args.observation.read_text())
    print(json.dumps(decide(state, observation, time.time() if args.now is None else args.now),
                     ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
