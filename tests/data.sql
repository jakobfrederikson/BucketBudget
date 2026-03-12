INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO budget (owner_id, created, title, frequency)
VALUES
  ('1', '2026-01-01 00:00:00', 'test budget', 'Weekly');

INSERT INTO budget_member (budget_id, user_id)
VALUES
  ('1', '1');

INSERT INTO income_item (budget_id, title, amount, frequency, split_income)
VALUES
  ('1', 'test income', '1000.00', 'Weekly', '1');

INSERT INTO expense_item (budget_id, title, amount, frequency, expense_bucket)
VALUES
  ('1', 'test expense', '100.00', 'Weekly', '1');

INSERT INTO bucket (budget_id, title, percent)
VALUES
  ('1', 'test bucket', '100.00');