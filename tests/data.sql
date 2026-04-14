INSERT INTO user (id, username, email, password, active, fs_uniquifier)
VALUES
  (1, 'test', "test@test.com", 'testpassword', 1, 'uniquifier-1'),
  (2, 'other', "test2@test.com", 'testpassword2', 1, 'uniquifier-2');

INSERT INTO budget (owner_id, invite_code, created, title, frequency_enum)
VALUES
  ('1', 'joinme', '2026-01-01 00:00:00', 'test budget', 'Weekly');

INSERT INTO budget_user (budget_id, user_id)
VALUES
  (1, 1);

INSERT INTO income_item (budget_id, title, amount_int, frequency_enum)
VALUES
  ('1', 'test income', 100000, 'Weekly');

INSERT INTO expense_item (budget_id, title, amount_int, frequency_enum, expense_bucket)
VALUES
  ('1', 'test expense', 40000, 'Weekly', '1');

INSERT INTO bucket (budget_id, title, percent_int)
VALUES
  ('1', 'test bucket', 6000);