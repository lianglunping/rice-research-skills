import copy
import json
import unittest

from next_check import initialize, decide, record_repair, recover, renew_repair_budget
from monitor_repair_budget import validate_budget


class RenewableRepairTests(unittest.TestCase):
    def start(self, **kwargs):
        return initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user execution',
                          repair_budget_mode='RENEWABLE', scope_fingerprint='scope-A',
                          renewal_authority='user renewable repair instruction', **kwargs)

    def observe_failure(self, s, issue='incident'):
        return decide(s, dict(run_id='run', attempt=s['attempt'],
                             observation_id=(s.get('last_observation_id') or '') + '-failure-' + str(s['total_repair_attempts']),
                             status='FAILED', issue_key=issue), s['last_observed_at'] + 60)

    def reserve(self, s, issue='incident'):
        s = self.observe_failure(s, issue)
        n = s['total_repair_attempts'] + 1
        return record_repair(s, 'repair-' + str(n), s['last_observed_at'], issue,
                             'evidence-' + str(n), 'method-' + str(n))

    def exhausted(self, **kwargs):
        s = self.start(**kwargs)
        for _ in range(3):
            s = self.reserve(s)
        return self.observe_failure(s)

    def renewal_args(self, s):
        cycle = len(s['repair_renewal_log']) + 1
        return dict(run_id='run', scope_fingerprint='scope-A', issue_key=s['issue_key'],
                    now=s['last_observed_at'], diagnosis='cause-' + str(cycle),
                    next_approach='next-' + str(cycle), evidence='review-' + str(cycle),
                    recovery_gate=dict(payload_ended=True, lock_safe=True, within_scope=True,
                                       resources_available=True, journals_reconciled=True,
                                       evidence='verified job/resource/journal receipt'),
                    reservation_outcomes={r['repair_id']: 'failed-action-journal-' + r['repair_id']
                                          for r in s.get('repair_history', []) if r['status'] == 'RESERVED'})

    def test_five_renewals_preserve_fifteen_failures(self):
        s = self.start()
        for cycle in range(5):
            for _ in range(3):
                s = self.reserve(s)
            s = self.observe_failure(s)
            self.assertEqual(s['decision'], 'REVIEW_REPAIR_CYCLE')
            s = renew_repair_budget(s, **self.renewal_args(s))
            s = json.loads(json.dumps(s))  # persisted/reloaded state
        self.assertEqual(s['total_repair_attempts'], 15)
        self.assertEqual(s['repair_attempts_by_issue'], {'incident': 15})
        self.assertEqual(len(s['repair_history']), 15)
        self.assertTrue(all(r['status'] == 'FAILED' for r in s['repair_history']))
        self.assertEqual(len(s['repair_renewal_log']), 5)
        self.assertEqual(s['repair_cycle_attempts'], 0)
        self.assertEqual(s['run_id'], 'run')

    def test_six_distinct_issues_trigger_batch_review(self):
        s = self.start()
        for n in range(6):
            s = self.reserve(s, 'issue-' + str(n))
        s = self.observe_failure(s, 'issue-5')
        self.assertEqual(s['decision'], 'REVIEW_REPAIR_CYCLE')
        s = renew_repair_budget(s, **self.renewal_args(s))
        self.assertEqual(s['total_repair_attempts'], 6)
        self.assertEqual(s['repair_cycle_attempts_by_issue'], {})

    def test_renewal_is_pure_and_preserves_monitor_deadline(self):
        s = self.exhausted()
        before = copy.deepcopy(s)
        result = renew_repair_budget(s, **self.renewal_args(s))
        self.assertEqual(s, before)
        self.assertEqual(result['next_check_at'], before['next_check_at'])
        self.assertEqual(result['anomaly_checks'], before['anomaly_checks'])
        self.assertEqual(result['attempt'], before['attempt'])

    def test_cannot_reserve_past_threshold_before_review(self):
        s = self.exhausted()
        with self.assertRaises(ValueError):
            record_repair(s, 'fourth', s['last_observed_at'], 'incident', 'ev', 'fix4')

    def test_same_fix_still_rejected_after_renewal(self):
        s = self.exhausted()
        s = renew_repair_budget(s, **self.renewal_args(s))
        with self.assertRaises(ValueError):
            record_repair(s, 'new-id', s['last_observed_at'], 'incident', 'new-ev', 'method-1')

    def test_repeated_review_receipt_rejected(self):
        s = self.exhausted()
        first = self.renewal_args(s)
        s = renew_repair_budget(s, **first)
        for _ in range(3):
            s = self.reserve(s)
        s = self.observe_failure(s)
        repeated = self.renewal_args(s)
        for key in ['diagnosis', 'next_approach', 'evidence']:
            repeated[key] = first[key]
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **repeated)

    def test_reserved_submission_does_not_double_count(self):
        s = self.reserve(self.start())
        s = recover(s, 'attempt-2', s['last_observed_at'], 'incident', 'actual submission', repair_id='repair-1')
        self.assertEqual(s['total_repair_attempts'], 1)
        self.assertEqual(s['repair_cycle_attempts'], 1)
        self.assertEqual(s['repair_budget_mode'], 'RENEWABLE')
        self.assertEqual(s['next_check_at'], s['last_observed_at'] + 60)

    def test_recovery_preserves_renewal_ledger(self):
        s = self.exhausted()
        s = renew_repair_budget(s, **self.renewal_args(s))
        s = self.reserve(s)
        s = recover(s, 'attempt-2', s['last_observed_at'], 'incident', 'submitted', repair_id='repair-4')
        self.assertEqual(s['total_repair_attempts'], 4)
        self.assertEqual(s['repair_cycle_attempts'], 1)
        self.assertEqual(len(s['repair_renewal_log']), 1)
        validate_budget(s)

    def test_renewable_recovery_requires_reservation(self):
        s = self.observe_failure(self.start())
        with self.assertRaises(ValueError):
            recover(s, 'attempt-2', s['last_observed_at'], 'incident', 'submitted')

    def test_hard_cap_cannot_be_renewed(self):
        s = self.exhausted(repair_hard_limit=3)
        self.assertEqual(s['decision'], 'DECISION_REQUIRED')
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **self.renewal_args(s))

    def test_reserved_last_allowed_repair_can_submit(self):
        s = self.reserve(self.start(repair_hard_limit=1))
        s = recover(s, 'attempt-2', s['last_observed_at'], 'incident', 'submitted', repair_id='repair-1')
        s = self.observe_failure(s)
        self.assertEqual(s['decision'], 'DECISION_REQUIRED')

    def test_resource_stop_blocks_renewal_and_recovery(self):
        s = self.exhausted()
        s['repair_stop_reason'] = 'RESOURCE_EXHAUSTED'
        s = self.observe_failure(s, 'new-incident')
        self.assertEqual(s['decision'], 'DECISION_REQUIRED')
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **self.renewal_args(s))
        with self.assertRaises(ValueError):
            recover(s, 'attempt-2', s['last_observed_at'], 'new-incident', 'ev', repair_id='repair-3')

    def test_scope_and_run_mismatch_block_renewal(self):
        s = self.exhausted()
        for key in ['run_id', 'scope_fingerprint', 'issue_key']:
            with self.subTest(key=key):
                args = self.renewal_args(s)
                args[key] = 'different'
                with self.assertRaises(ValueError):
                    renew_repair_budget(s, **args)

    def test_observe_only_and_decision_modes_cannot_renew(self):
        s = self.exhausted()
        for mode in ['OBSERVE_ONLY', 'DECISION_REQUIRED']:
            with self.subTest(mode=mode):
                s['authority'] = mode
                with self.assertRaises(ValueError):
                    renew_repair_budget(s, **self.renewal_args(s))

    def test_all_recovery_gates_require_verified_evidence(self):
        s = self.exhausted()
        for key in ['payload_ended', 'lock_safe', 'within_scope', 'resources_available', 'journals_reconciled', 'evidence']:
            with self.subTest(key=key):
                args = self.renewal_args(s)
                args['recovery_gate'][key] = False
                with self.assertRaises(ValueError):
                    renew_repair_budget(s, **args)

    def test_outstanding_reservations_must_be_reconciled(self):
        s = self.exhausted()
        args = self.renewal_args(s)
        args['reservation_outcomes'] = {}
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **args)

    def test_legacy_absent_mode_still_fixed(self):
        s = initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user')
        self.assertNotIn('repair_budget_mode', s)
        for _ in range(3):
            s = self.reserve(s)
        s = self.observe_failure(s)
        self.assertEqual(s['decision'], 'DECISION_REQUIRED')

    def test_initialization_requires_renewal_authority_and_scope(self):
        for field in ['scope_fingerprint', 'renewal_authority']:
            args = dict(repair_budget_mode='RENEWABLE', scope_fingerprint='scope-A', renewal_authority='user')
            args[field] = ''
            with self.subTest(field=field), self.assertRaises(ValueError):
                initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user', **args)

    def test_invalid_mode_and_fixed_cap_rejected(self):
        for args in [dict(repair_budget_mode='UNKNOWN'), dict(repair_hard_limit=0), dict(repair_hard_limit=True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                initialize('run', 'attempt-1', 0, **args)

    def test_ledger_corruption_rejected(self):
        s = self.exhausted()
        for field in ['total_repair_attempts', 'repair_cycle_attempts']:
            broken = copy.deepcopy(s)
            broken[field] = 0
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_budget(broken)
        renewed = renew_repair_budget(s, **self.renewal_args(s))
        renewed['repair_renewal_log'][0]['scope_fingerprint'] = 'wrong'
        with self.assertRaises(ValueError):
            validate_budget(renewed)

    def test_accepted_success_at_threshold_needs_no_renewal(self):
        s = self.exhausted()
        s = decide(s, dict(run_id='run', attempt=s['attempt'], observation_id='accepted',
                           status='SUCCESS', signal_verified=True, acceptance_passed=True,
                           acceptance_evidence='artifact/semantic QA'), s['last_observed_at'] + 60)
        self.assertEqual(s['decision'], 'ACCEPTED')
        self.assertTrue(s['closed'])
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **self.renewal_args(s))

    def test_early_renewal_and_invalid_time_rejected(self):
        s = self.observe_failure(self.start())
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **self.renewal_args(s))
        s = self.exhausted()
        for now in [-1, float('nan'), True]:
            args = self.renewal_args(s)
            args['now'] = now
            with self.subTest(now=now), self.assertRaises(ValueError):
                renew_repair_budget(s, **args)

    def test_missing_diagnosis_method_or_evidence_blocks_renewal(self):
        s = self.exhausted()
        for key in ['diagnosis', 'next_approach', 'evidence']:
            args = self.renewal_args(s)
            args[key] = ' '
            with self.subTest(key=key), self.assertRaises(ValueError):
                renew_repair_budget(s, **args)

    def test_pending_acceptance_is_not_a_recovery_review(self):
        s = self.exhausted()
        s = decide(s, dict(run_id='run', attempt=s['attempt'], observation_id='success-pending',
                           status='SUCCESS', signal_verified=True), s['last_observed_at'] + 60)
        self.assertEqual(s['decision'], 'ACCEPTANCE_REQUIRED')
        with self.assertRaises(ValueError):
            renew_repair_budget(s, **self.renewal_args(s))

    def test_fixed_hard_cap_blocks_legacy_unreserved_recovery(self):
        s = initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user', repair_hard_limit=1)
        s = self.observe_failure(s)
        s = recover(s, 'attempt-2', s['last_observed_at'], 'incident', 'submission')
        s = self.observe_failure(s)
        with self.assertRaises(ValueError):
            recover(s, 'attempt-3', s['last_observed_at'], 'incident', 'submission')

    def test_reservation_replay_does_not_spend_more_cycle_budget(self):
        s = self.reserve(self.start())
        replay = record_repair(s, 'repair-1', s['last_observed_at'], 'incident', 'evidence-1', 'method-1')
        self.assertEqual(s, replay)
        s['total_repair_attempts'] = 0
        with self.assertRaises(ValueError):
            record_repair(s, 'repair-1', s['last_observed_at'], 'incident', 'evidence-1', 'method-1')


if __name__ == '__main__':
    unittest.main()
