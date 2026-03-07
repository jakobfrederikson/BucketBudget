DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS budget;
DROP TABLE IF EXISTS budget_member;
DROP TABLE IF EXISTS income_item;
DROP TABLE IF EXISTS expense_item;
DROP TABLE IF EXISTS bucket;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    frequency TEXT CHECK( frequency IN ('Weekly', 'Fortnightly', 'Four-Weekly', 'Yearly')) NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE budget_member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budget (id),
    FOREIGN KEY (user_id) REFERENCES user (id),
    UNIQUE(budget_id, user_id)
);

CREATE TABLE income_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    amount DECIMAL NOT NULL,
    frequency TEXT CHECK( frequency IN ('Weekly', 'Fortnightly', 'Four-Weekly', 'Yearly')) NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budget (id)
);

CREATE TABLE expense_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    amount DECIMAL NOT NULL,
    frequency TEXT CHECK( frequency IN ('Weekly', 'Fortnightly', 'Four-Weekly', 'Yearly')) NOT NULL,
    expense_bucket BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (budget_id) REFERENCES budget (id)
);

CREATE TABLE bucket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id INTEGER NOT NULL,
    percent DECIMAL NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budget (id)
);

