import copy
import unittest

from next_check import decide, initialize, record_repair, recover


class BackoffTests(unittest.TestCase):
    def setUp(self):
        self.s = initialize('run', 'attempt-1', 0)
        self.serial = 0

    def observe(self, **fields):
        now = fields.pop('now', self.s['next_check_at'])
        self.serial += 1
        obs = dict(run_id='run', attempt=self.s['attempt'],
                   observation_id=str(self.serial), status='RUNNING',
                   signal_verified=True)
        obs.update(fields)
        self.s = decide(self.s, obs, now)
        return self.s

    def stable_long_run(self):
        return self.observe(eta_seconds=172800, eta_reliable=True, eta_scope='whole_run')

    def at_six_hours(self):
        for _ in range(11):
            self.stable_long_run()
        self.assertEqual(self.s['interval_seconds'], 21600)

    def test_submission_and_exact_stable_sequence(self):
        times, delays = [], []
        for _ in range(11):
            times.append(self.s['next_check_at'])
            delays.append(self.stable_long_run()['interval_seconds'])
        self.assertEqual(times[:5], [60, 120, 180, 780, 1380])
        self.assertEqual(delays, [60, 60, 600, 600, 1800, 1800, 3600,
                                  3600, 10800, 10800, 21600])

    def test_80_percent_shortens_six_hour_tier(self):
        self.at_six_hours()
        self.observe(progress_pct=80, progress_reliable=True, progress_scope='whole_run')
        self.assertEqual(self.s['interval_seconds'], 600)

    def test_95_and_99_percent_shorten_further(self):
        self.at_six_hours()
        for pct, delay in [(95, 120), (99, 60), (100, 60)]:
            self.observe(progress_pct=pct, progress_reliable=True, progress_scope='whole_run')
            self.assertEqual(self.s['interval_seconds'], delay)
            self.assertFalse(self.s['closed'])

    def test_current_stage_percentage_is_not_overall_completion(self):
        self.at_six_hours()
        self.observe(progress_pct=99, progress_reliable=True, progress_scope='current_stage',
                     eta_seconds=172800, eta_reliable=True, eta_scope='whole_run')
        self.assertEqual(self.s['interval_seconds'], 21600)

    def test_missing_eta_caps_long_tiers(self):
        for _ in range(20):
            self.observe()
        self.assertEqual(self.s['interval_seconds'], 3600)

    def test_short_remaining_time_overrides_low_progress(self):
        self.at_six_hours()
        self.observe(progress_pct=20, progress_reliable=True, progress_scope='whole_run',
                     eta_seconds=600, eta_reliable=True, eta_scope='whole_run')
        self.assertEqual(self.s['interval_seconds'], 150)

    def test_final_index_phase_can_shorten_interval(self):
        self.at_six_hours()
        self.observe(phase_interval_cap_seconds=300, eta_seconds=172800,
                     eta_reliable=True, eta_scope='whole_run')
        self.assertEqual(self.s['interval_seconds'], 300)

    def test_progress_capped_checks_do_not_promote_long_tier(self):
        self.at_six_hours()
        self.s['tier'] = 2
        self.s['normal_checks'] = 0
        self.s['countable_due'] = False
        for _ in range(8):
            self.observe(progress_pct=95, progress_reliable=True, progress_scope='whole_run')
        self.assertEqual(self.s['tier'], 2)

    def test_total_repair_limit_is_enforced_across_different_issues(self):
        self.s = initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user request')
        self.s['total_repair_attempts'] = 6
        self.observe(status='FAILED', issue_key='new-issue')
        self.assertEqual(self.s['decision'], 'DECISION_REQUIRED')
        with self.assertRaises(ValueError):
            recover(self.s, 'attempt-2', 120, 'new-issue', 'repair.json')

    def test_missing_or_invalid_progress_does_not_fake_completion(self):
        for pct in [None, float('nan'), float('inf'), -1, 101, '99', True]:
            self.observe(progress_pct=pct, progress_reliable=True, progress_scope='whole_run')
            self.assertEqual(self.s['decision'], 'MONITOR')
            self.assertIsNone(self.s['last_progress_pct'])

    def test_regression_requires_denominator_check(self):
        self.at_six_hours()
        self.observe(progress_pct=85, progress_reliable=True, progress_scope='whole_run')
        self.observe(progress_pct=10, progress_reliable=True, progress_scope='whole_run')
        self.assertEqual(self.s['decision'], 'VERIFY_PROGRESS')
        self.assertLessEqual(self.s['interval_seconds'], 600)

    def test_early_event_does_not_promote_or_postpone_due_time(self):
        self.observe(now=30)
        self.assertEqual(self.s['normal_checks'], 0)
        self.assertEqual(self.s['next_check_at'], 60)
        for _ in range(3):
            self.observe()
        self.assertEqual(self.s['interval_seconds'], 600)

    def test_early_progress_event_brings_check_forward(self):
        self.at_six_hours()
        self.observe(now=self.s['last_observed_at']+60, progress_pct=99,
                     progress_reliable=True, progress_scope='whole_run')
        self.assertEqual(self.s['interval_seconds'], 60)

    def test_duplicate_observation_is_idempotent(self):
        self.observe()
        again = decide(self.s, dict(run_id='run', observation_id='1'), 120)
        self.assertEqual(again, self.s)

    def test_unknown_breaks_normal_streak_and_backs_off(self):
        self.observe()
        delays = [self.observe(status='UNKNOWN')['interval_seconds'] for _ in range(5)]
        self.assertEqual(delays, [60, 600, 600, 600, 600])
        self.assertEqual(self.s['normal_checks'], 0)

    def gap_observation(self, **fields):
        obs = dict(status='UNKNOWN', observability_gap=dict(
            issue_key='route-outage', diagnosis_evidence='diagnosis/route.md',
            recovery_blocked=True))
        obs.update(fields)
        return self.observe(**obs)

    def test_diagnosed_gap_has_bounded_longer_backoff(self):
        delays = [self.gap_observation()['interval_seconds'] for _ in range(6)]
        self.assertEqual(delays, [60, 600, 1800, 3600, 3600, 3600])
        self.assertEqual(self.s['decision'], 'RESTORE_OBSERVABILITY')
        self.assertEqual(self.s['authority'], 'OBSERVE_ONLY')
        self.assertFalse(self.s['closed'])

    def test_gap_opt_in_requires_all_diagnosis_fields(self):
        invalid = [None, {}, {'issue_key': 'outage'},
                   {'issue_key': 'outage', 'diagnosis_evidence': ' ', 'recovery_blocked': True},
                   {'issue_key': 'outage', 'diagnosis_evidence': 'd.md', 'recovery_blocked': 'true'},
                   {'issue_key': ' ', 'diagnosis_evidence': 'd.md', 'recovery_blocked': True},
                   {'issue_key': 'outage', 'diagnosis_evidence': 'd.md', 'recovery_blocked': False}]
        for gap in invalid:
            with self.subTest(gap=gap):
                self.s = initialize('run', 'attempt-1', 0)
                delays = [self.gap_observation(observability_gap=gap)['interval_seconds']
                          for _ in range(4)]
                self.assertEqual(delays, [60, 600, 600, 600])

    def test_missing_gap_evidence_resets_optional_streak(self):
        for _ in range(4):
            self.gap_observation()
        self.observe(status='UNKNOWN')
        self.assertEqual(self.s['interval_seconds'], 600)
        self.gap_observation()
        self.assertEqual(self.s['interval_seconds'], 60)

    def test_changed_gap_does_not_inherit_long_backoff(self):
        for _ in range(4):
            self.gap_observation()
        self.gap_observation(observability_gap=dict(
            issue_key='new-outage', diagnosis_evidence='new.md', recovery_blocked=True))
        self.assertEqual(self.s['interval_seconds'], 60)

    def test_early_gap_does_not_advance_or_postpone(self):
        self.gap_observation()
        self.gap_observation()
        due = self.s['next_check_at']
        self.gap_observation(now=self.s['last_observed_at'] + 1)
        self.assertEqual(self.s['diagnosed_unknown_checks'], 2)
        self.assertEqual(self.s['next_check_at'], due)

    def test_gap_counter_survives_json_round_trip(self):
        import json
        self.gap_observation()
        self.gap_observation()
        self.s = json.loads(json.dumps(self.s))
        self.gap_observation()
        self.assertEqual(self.s['interval_seconds'], 1800)

    def test_gap_recovery_resets_stability_without_changing_repairs(self):
        self.s['total_repair_attempts'] = 2
        for _ in range(4):
            self.gap_observation()
        self.observe()
        self.assertEqual(self.s['interval_seconds'], 60)
        self.assertEqual(self.s['normal_checks'], 0)
        self.assertEqual(self.s['diagnosed_unknown_checks'], 0)
        self.assertEqual(self.s['total_repair_attempts'], 2)

    def test_gap_cannot_override_explicit_failure(self):
        for _ in range(4):
            self.gap_observation()
        self.gap_observation(explicit_anomaly=True, issue_key='OOM')
        self.assertEqual(self.s['decision'], 'LOCALIZE_AND_REPORT')
        self.assertEqual(self.s['interval_seconds'], 60)
        self.assertEqual(self.s['diagnosed_unknown_checks'], 0)

    def test_gap_respects_known_near_completion_caps(self):
        for pct, cap in [(80, 600), (95, 120), (99, 60)]:
            with self.subTest(pct=pct):
                self.s = initialize('run', 'attempt-1', 0)
                self.observe(progress_pct=pct, progress_reliable=True, progress_scope='whole_run')
                for _ in range(5):
                    self.gap_observation()
                    self.assertLessEqual(self.s['interval_seconds'], cap)

    def test_gap_respects_explicit_interval_cap(self):
        for _ in range(5):
            self.gap_observation(phase_interval_cap_seconds=120)
            self.assertLessEqual(self.s['interval_seconds'], 120)

    def test_gap_ends_on_verified_accepted_completion(self):
        self.gap_observation()
        self.gap_observation(status='SUCCESS', acceptance_passed=True,
                             acceptance_evidence='qa.json')
        self.assertTrue(self.s['closed'])
        self.assertIsNone(self.s['next_check_at'])

    def test_legacy_state_without_optional_gap_fields_still_runs(self):
        self.assertEqual(self.s['policy_version'], 2)
        self.assertNotIn('diagnosed_unknown_checks', self.s)
        self.gap_observation()
        self.assertEqual(self.s['interval_seconds'], 60)

    def test_repeated_failure_never_rearms_one_minute_forever(self):
        delays = [self.observe(status='FAILED', issue_key='OOM')['interval_seconds'] for _ in range(7)]
        self.assertEqual(delays, [60, 60, 600, 1800, 3600, 3600, 3600])
        self.assertEqual(self.s['decision'], 'LOCALIZE_AND_REPORT')

    def test_changed_error_wording_does_not_rearm_short_window(self):
        for issue in ['error-1', 'error-2', 'error-3']:
            self.observe(status='FAILED', issue_key=issue)
        self.assertEqual(self.s['interval_seconds'], 600)

    def test_explicit_failure_wins_over_progress_and_success(self):
        self.observe(status='SUCCESS', explicit_anomaly=True, issue_key='checksum',
                     acceptance_passed=True, acceptance_evidence='qa.json', progress_pct=100)
        self.assertFalse(self.s['closed'])
        self.assertEqual(self.s['decision'], 'LOCALIZE_AND_REPORT')

    def test_no_error_without_verified_signal_is_unknown(self):
        self.observe(signal_verified=False)
        self.assertEqual(self.s['decision'], 'RESTORE_OBSERVABILITY')

    def test_success_needs_artifact_acceptance(self):
        self.observe(status='SUCCESS')
        self.assertEqual(self.s['decision'], 'ACCEPTANCE_REQUIRED')
        self.assertIsNone(self.s['next_check_at'])
        self.observe(now=120, status='SUCCESS', acceptance_passed=True,
                     acceptance_evidence='qa/accepted.json')
        self.assertTrue(self.s['closed'])
        self.assertEqual(self.s['decision'], 'ACCEPTED')

    def test_queue_to_running_starts_fresh_stability_window(self):
        for _ in range(5):
            self.observe(status='QUEUED')
        self.observe()
        self.assertEqual(self.s['interval_seconds'], 60)
        self.assertEqual(self.s['normal_checks'], 0)

    def test_transient_recovery_resets_without_erasing_repair_counts(self):
        self.at_six_hours()
        self.s['total_repair_attempts'] = 2
        self.observe(status='FAILED', issue_key='connection')
        self.observe()
        self.assertEqual(self.s['interval_seconds'], 60)
        self.assertEqual(self.s['total_repair_attempts'], 2)

    def test_confirmed_new_attempt_retains_repair_history(self):
        self.s = initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user request')
        self.observe(status='FAILED', issue_key='command')
        self.s = recover(self.s, 'attempt-2', 120, 'command', 'repair/evidence.json')
        self.assertEqual(self.s['run_id'], 'run')
        self.assertEqual(self.s['total_repair_attempts'], 1)
        self.assertEqual(self.s['next_check_at'], 180)

    def test_observe_only_cannot_record_automatic_repair(self):
        self.observe(status='FAILED', issue_key='error')
        with self.assertRaises(ValueError):
            recover(self.s, 'attempt-2', 120, 'error', 'repair.json')

    def test_repair_budget_survives_restarts(self):
        self.s = initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user request')
        for i in range(3):
            self.observe(status='FAILED', issue_key='error')
            self.s = recover(self.s, f'attempt-{i+2}', self.s['last_observed_at']+1,
                             'error', 'repair.json')
        self.observe(status='FAILED', issue_key='error')
        self.assertEqual(self.s['decision'], 'DECISION_REQUIRED')
        with self.assertRaises(ValueError):
            recover(self.s, 'attempt-5', self.s['last_observed_at']+1, 'error', 'repair.json')

    def test_run_identity_and_time_are_checked(self):
        for obs, now in [(dict(run_id='other',observation_id='a'),60),
                         (dict(run_id='run',observation_id='b'),-1)]:
            with self.assertRaises(ValueError):
                decide(self.s, obs, now)

    def test_unaudited_attempt_change_is_rejected(self):
        with self.assertRaises(ValueError):
            self.observe(attempt='new')

    def test_early_failure_cannot_postpone_existing_due_time(self):
        self.observe(now=30, status='FAILED', issue_key='connection')
        self.assertEqual(self.s['next_check_at'], 60)
        self.observe(now=45, status='FAILED', issue_key='connection')
        self.assertEqual(self.s['next_check_at'], 60)
        self.assertEqual(self.s['anomaly_checks'], 1)

    def test_early_unknown_does_not_advance_or_postpone(self):
        self.observe(now=10, status='UNKNOWN')
        self.observe(now=20, status='UNKNOWN')
        self.assertEqual(self.s['unknown_checks'], 1)
        self.assertEqual(self.s['next_check_at'], 60)

    def test_known_near_completion_cap_survives_missing_progress(self):
        self.at_six_hours()
        self.observe(progress_pct=95, progress_reliable=True, progress_scope='whole_run')
        self.stable_long_run()
        self.assertEqual(self.s['interval_seconds'], 120)

    def test_unknown_then_normal_restarts_stability_window(self):
        self.at_six_hours()
        self.observe(status='UNKNOWN')
        self.stable_long_run()
        self.assertEqual(self.s['interval_seconds'], 60)
        self.assertEqual(self.s['normal_checks'], 0)

    def prepare_repair(self):
        self.s = initialize('run', 'attempt-1', 0, 'REPAIR_PREAUTHORIZED', 'user request')
        self.observe(status='FAILED', issue_key='command')

    def reserve(self, number=1):
        self.s = record_repair(self.s, f'repair-{number}', self.s['last_observed_at'],
                               'command', f'diagnosis-{number}.json', f'fix-{number}')
        return self.s

    def test_failed_fixes_consume_budget_before_resubmission(self):
        self.prepare_repair()
        for n in range(1, 4):
            self.reserve(n)
        self.assertEqual(self.s['total_repair_attempts'], 3)
        self.assertEqual(self.s['attempt'], 'attempt-1')
        with self.assertRaises(ValueError):
            self.reserve(4)
        self.observe(status='FAILED', issue_key='command')
        self.assertEqual(self.s['decision'], 'DECISION_REQUIRED')

    def test_successful_reserved_repair_does_not_double_count(self):
        self.prepare_repair()
        self.reserve()
        self.s = recover(self.s, 'attempt-2', 120, 'command', 'submitted.json',
                         repair_id='repair-1')
        self.assertEqual(self.s['total_repair_attempts'], 1)
        self.assertEqual(self.s['repair_attempts_by_issue']['command'], 1)
        self.assertEqual(self.s['repair_history'][0]['status'], 'SUBMITTED')
        self.assertEqual(self.s['next_check_at'], 180)

    def test_third_reserved_repair_can_record_success(self):
        self.prepare_repair()
        for n in range(1, 4):
            self.reserve(n)
        self.s = recover(self.s, 'attempt-2', 120, 'command', 'submitted.json',
                         repair_id='repair-3')
        self.assertEqual(self.s['total_repair_attempts'], 3)

    def test_reserved_repair_replay_is_idempotent(self):
        self.prepare_repair()
        first = self.reserve()
        self.reserve()
        self.assertEqual(self.s, first)

    def test_reused_repair_id_cannot_change_action(self):
        self.prepare_repair()
        self.reserve()
        with self.assertRaises(ValueError):
            record_repair(self.s, 'repair-1', 60, 'command', 'other.json', 'other-fix')

    def test_identical_unresolved_fix_is_rejected(self):
        self.prepare_repair()
        self.reserve()
        with self.assertRaises(ValueError):
            record_repair(self.s, 'repair-2', 60, 'command', 'other.json', 'fix-1')

    def test_reserved_repair_cannot_be_recovered_without_id(self):
        self.prepare_repair()
        self.reserve()
        with self.assertRaises(ValueError):
            recover(self.s, 'attempt-2', 120, 'command', 'submitted.json')

    def test_observe_only_cannot_reserve_repair(self):
        self.observe(status='FAILED', issue_key='command')
        with self.assertRaises(ValueError):
            self.reserve()

    def test_failed_repair_state_round_trip_keeps_budget(self):
        import json
        self.prepare_repair()
        self.reserve()
        self.s = json.loads(json.dumps(self.s))
        self.assertEqual(self.s['total_repair_attempts'], 1)
        self.reserve(2)
        self.assertEqual(self.s['total_repair_attempts'], 2)

    def test_successful_submission_does_not_prove_same_fix_resolved_issue(self):
        self.prepare_repair()
        self.reserve()
        self.s = recover(self.s, 'attempt-2', 120, 'command', 'submitted.json',
                         repair_id='repair-1')
        self.observe(status='FAILED', issue_key='command')
        with self.assertRaises(ValueError):
            record_repair(self.s, 'repair-2', self.s['last_observed_at'],
                          'command', 'fresh-observation.json', 'fix-1')
        self.s = record_repair(self.s, 'repair-2', self.s['last_observed_at'],
                               'command', 'new-diagnosis.json', 'revised-fix')
        self.assertEqual(self.s['total_repair_attempts'], 2)

    def test_input_state_is_not_mutated(self):
        before = copy.deepcopy(self.s)
        decide(self.s, dict(run_id='run',attempt='attempt-1',observation_id='x',
                           status='RUNNING',signal_verified=True),60)
        self.assertEqual(before, self.s)


if __name__ == '__main__':
    unittest.main(verbosity=2)
