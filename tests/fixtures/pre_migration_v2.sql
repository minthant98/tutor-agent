-- Snapshot of representative pre-migration data shape.
-- Loaded BEFORE the ux_overhaul_v1 migration runs in regression tests.
-- Mirrors the state of production at deploy time.

-- A student who completed legacy onboarding with one subject
INSERT INTO students (id, email, name, hashed_password, exam_board, exam_level, subjects, exam_date, onboarding_complete, subscription_tier, created_at)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'alice@example.com', 'Alice',
    'bcrypt$dummy',
    'edexcel', 'a_level', '["pure_mathematics"]'::json,
    '2026-11-15', true, 'free', NOW() - INTERVAL '30 days'
);

-- A student mid-onboarding (no subjects yet)
INSERT INTO students (id, email, name, hashed_password, exam_board, exam_level, subjects, onboarding_complete, subscription_tier, created_at)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'bob@example.com', 'Bob',
    'bcrypt$dummy',
    'cambridge', 'a_level', '[]'::json,
    false, 'free', NOW() - INTERVAL '1 day'
);

-- Alice has an in-flight session
INSERT INTO sessions (id, student_id, subject, topic, mode, messages, started_at)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'pure_mathematics', 'integration_basics', 'explain',
    '[{"role":"tutor","content":"Hi"}]'::json,
    NOW() - INTERVAL '1 hour'
);

-- Alice has mastery rows
INSERT INTO mastery_state (id, student_id, subject, topic, mastery_score, total_attempts, correct_streak, is_weak)
VALUES
    ('44444444-4444-4444-4444-444444444441', '11111111-1111-1111-1111-111111111111',
     'pure_mathematics', 'integration_basics', 0.65, 5, 2, false),
    ('44444444-4444-4444-4444-444444444442', '11111111-1111-1111-1111-111111111111',
     'pure_mathematics', 'differentiation_basics', 0.82, 8, 4, false)
