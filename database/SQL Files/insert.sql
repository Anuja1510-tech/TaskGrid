-- Users 
INSERT INTO User (Name, Email, Password, UserType, JoinDate) VALUES
('Ishwari', 'ishwari@example.com', 'pass123', 'Admin', '2025-01-01'),
('Prajakta', 'prajakta@example.com', 'pass456', 'Manager', '2025-02-15'),
('Anuja', 'anuja@example.com', 'pass789', 'Manager', '2025-03-01'),
('Dhanshree', 'dhanshree@example.com', 'pass321', 'User', '2025-04-01');

-- Clients
INSERT INTO Client (UserID, ClientName, Email, Phone, Company) VALUES
(2, 'Charlie Corp', 'charlie@example.com', '1234567890', 'Charlie Co.'),
(2, 'Delta Ltd', 'delta@example.com', '0987654321', 'Delta Ltd'),
(3, 'Echo Inc', 'echo@example.com', '1122334455', 'Echo Inc.'),
(4, 'Foxtrot LLC', 'foxtrot@example.com', '5566778899', 'Foxtrot LLC');

-- Projects
INSERT INTO Project (UserID, ProjectName, ClientID, StartDate, EndDate, Status) VALUES
(2, 'Website Redesign', 1, '2025-03-01', '2025-06-01', 'In Progress'),
(2, 'Mobile App Launch', 2, '2025-04-01', '2025-08-01', 'Pending'),
(3, 'Marketing Campaign', 3, '2025-05-01', '2025-07-15', 'Pending'),
(4, 'Data Analysis', 4, '2025-06-01', '2025-09-01', 'In Progress');

-- Tasks
INSERT INTO Task (ProjectID, Title, Description, AssignedDate, DueDate, Priority, Status) VALUES
(1, 'Create Wireframes', 'Design initial wireframes', '2025-03-02', '2025-03-15', 'High', 'Pending'),
(1, 'Design Homepage', 'Create homepage design', '2025-03-05', '2025-03-20', 'Medium', 'Pending'),
(2, 'Develop API', 'API development for app', '2025-04-05', '2025-05-05', 'High', 'Pending'),
(3, 'Social Media Strategy', 'Plan campaign strategy', '2025-05-02', '2025-05-20', 'Medium', 'Pending'),
(4, 'Analyze Sales Data', 'Prepare insights report', '2025-06-05', '2025-06-25', 'High', 'Pending');

-- Invoices
INSERT INTO Invoice (UserID, ProjectID, Amount, IssueDate, DueDate, PaidStatus) VALUES
(2, 1, 5000.00, '2025-03-10', '2025-03-25', 'Unpaid'),
(2, 2, 10000.00, '2025-04-10', '2025-04-25', 'Unpaid'),
(3, 3, 7000.00, '2025-05-10', '2025-05-25', 'Unpaid'),
(4, 4, 8500.00, '2025-06-10', '2025-06-25', 'Unpaid');

-- WorkLogs
INSERT INTO WorkLog (UserID, Title, Description, Date, StartTime, EndTime, Status) VALUES
(2, 'Meeting with client', 'Discuss project requirements', '2025-03-03', '10:00:00', '11:30:00', 'Completed'),
(2, 'Design review', 'Review homepage design', '2025-03-06', '14:00:00', '15:00:00', 'Pending'),
(3, 'Strategy Meeting', 'Discuss social media campaign', '2025-05-03', '11:00:00', '12:00:00', 'Pending'),
(4, 'Data Cleaning', 'Prepare dataset for analysis', '2025-06-06', '09:00:00', '11:00:00', 'Completed');
