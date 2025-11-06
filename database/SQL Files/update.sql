-- Update task status
UPDATE Task SET Status='Completed' WHERE TaskID=1;

-- Update invoice status
UPDATE Invoice SET PaidStatus='Paid' WHERE InvoiceID=1;

-- Update project status
UPDATE Project SET Status='Completed' WHERE ProjectID=1;

-- Update user email
UPDATE User SET Email='alice_new@example.com' WHERE Name='Alice';    BTW EXPLAIN IN DETAIL 