-- Runs once, the first time the Postgres container starts.
-- All people, emails, phone numbers, PAN and Aadhaar values below are FAKE.

CREATE TABLE employees (
    employee_id   TEXT PRIMARY KEY,          -- e.g. E101
    full_name     TEXT NOT NULL,
    department    TEXT NOT NULL,
    designation   TEXT NOT NULL,
    manager_id    TEXT REFERENCES employees(employee_id),
    location      TEXT NOT NULL,
    date_joined   DATE NOT NULL,
    work_email    TEXT NOT NULL,
    phone         TEXT NOT NULL,
    pan           TEXT NOT NULL,
    aadhaar       TEXT NOT NULL
);

CREATE TABLE leave_balances (
    employee_id   TEXT REFERENCES employees(employee_id),
    year          INT  NOT NULL,
    leave_type    TEXT NOT NULL,             -- earned / casual / sick
    entitled      NUMERIC(4,1) NOT NULL,
    used          NUMERIC(4,1) NOT NULL,
    PRIMARY KEY (employee_id, year, leave_type)
);

CREATE TABLE it_tickets (
    ticket_id     TEXT PRIMARY KEY,
    employee_id   TEXT REFERENCES employees(employee_id),
    category      TEXT NOT NULL,             -- laptop / access / password / software
    summary       TEXT NOT NULL,
    status        TEXT NOT NULL,             -- open / in_progress / resolved
    priority      TEXT NOT NULL,             -- P1..P4
    opened_on     DATE NOT NULL,
    resolved_on   DATE
);

INSERT INTO employees VALUES
 ('E101','Ananya Rao','Engineering','Senior Software Engineer',NULL,'Bengaluru','2021-03-15','ananya.rao@brightpath.example','+91 98450 11223','ABCPR1234K','2345 6789 0123'),
 ('E102','Rohit Verma','Engineering','Software Engineer','E101','Delhi','2023-07-03','rohit.verma@brightpath.example','+91 99100 44556','BXYPV5678L','3456 7890 1234'),
 ('E103','Meera Iyer','Human Resources','HR Business Partner',NULL,'Bengaluru','2020-01-20','meera.iyer@brightpath.example','+91 98860 77889','CQWPI9012M','4567 8901 2345'),
 ('E104','Kabir Khan','Sales','Account Executive','E103','Mumbai','2024-02-12','kabir.khan@brightpath.example','+91 98200 33445','DKLPK3456N','5678 9012 3456'),
 ('E105','Sneha Das','Finance','Financial Analyst','E103','Delhi','2022-09-05','sneha.das@brightpath.example','+91 98110 66778','ERTPD7890P','6789 0123 4567');

INSERT INTO leave_balances VALUES
 ('E101',2026,'earned',18,9),  ('E101',2026,'casual',8,5),  ('E101',2026,'sick',10,2),
 ('E102',2026,'earned',18,11.5),('E102',2026,'casual',8,6), ('E102',2026,'sick',10,1),
 ('E103',2026,'earned',18,4),  ('E103',2026,'casual',8,2),  ('E103',2026,'sick',10,0),
 ('E104',2026,'earned',18,15), ('E104',2026,'casual',8,8),  ('E104',2026,'sick',10,6),
 ('E105',2026,'earned',18,7),  ('E105',2026,'casual',8,3),  ('E105',2026,'sick',10,3);

INSERT INTO it_tickets VALUES
 ('INC-2041','E102','password','Locked out of SSO after password expiry','resolved','P2','2026-10-28','2026-10-28'),
 ('INC-2077','E104','laptop','Laptop battery drains in under 2 hours','in_progress','P3','2026-11-10',NULL),
 ('INC-2080','E104','access','Need Salesforce access for the West region','open','P2','2026-11-14',NULL),
 ('INC-2085','E101','software','Request IntelliJ IDEA Ultimate licence','open','P4','2026-11-17',NULL),
 ('INC-2090','E105','access','VPN disconnects every 10 minutes','in_progress','P2','2026-11-18',NULL);

-- Least privilege: the MCP server logs in as this role, which can only SELECT.
CREATE ROLE helpdesk_ro LOGIN PASSWORD 'readonly_dev_only';
GRANT CONNECT ON DATABASE helpdesk TO helpdesk_ro;
GRANT USAGE ON SCHEMA public TO helpdesk_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO helpdesk_ro;
