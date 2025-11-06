-- Users table
CREATE TABLE IF NOT EXISTS User (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100),
    Password VARCHAR(100),
    UserType VARCHAR(50),
    JoinDate DATE
);

-- Client table
CREATE TABLE IF NOT EXISTS Client (
    ClientID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    ClientName VARCHAR(100) NOT NULL,
    Email VARCHAR(100),
    Phone VARCHAR(20),
    Company VARCHAR(100),
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Project table
CREATE TABLE IF NOT EXISTS Project (
    ProjectID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    ProjectName VARCHAR(100) NOT NULL,
    ClientID INT,
    StartDate DATE,
    EndDate DATE,
    Status VARCHAR(50),
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ClientID) REFERENCES Client(ClientID) ON DELETE CASCADE
);

-- Invoice table
CREATE TABLE IF NOT EXISTS Invoice (
    InvoiceID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    ProjectID INT,
    Amount DECIMAL(10,2),
    IssueDate DATE,
    DueDate DATE,
    PaidStatus VARCHAR(20),
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ProjectID) REFERENCES Project(ProjectID) ON DELETE CASCADE
);

-- Task table
CREATE TABLE IF NOT EXISTS Task (
    TaskID INT AUTO_INCREMENT PRIMARY KEY,
    ProjectID INT,
    Title VARCHAR(100) NOT NULL,
    Description TEXT,
    AssignedDate DATE,
    DueDate DATE,
    Priority VARCHAR(20),
    Status VARCHAR(20),
    FOREIGN KEY (ProjectID) REFERENCES Project(ProjectID) ON DELETE CASCADE
);

-- WorkLog table
CREATE TABLE IF NOT EXISTS WorkLog (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    Title VARCHAR(100),
    Description TEXT,
    Date DATE,
    StartTime TIME,
    EndTime TIME,
    Duration TIME GENERATED ALWAYS AS (TIMEDIFF(EndTime, StartTime)) STORED,
    Status VARCHAR(20),
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
);
