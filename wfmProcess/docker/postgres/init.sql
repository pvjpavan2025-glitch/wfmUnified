-- Create the workflow database
CREATE DATABASE workflow;

-- Create the workflow_user with password
CREATE USER workflow_user WITH PASSWORD 'workflow_pass';

-- Grant all privileges on the workflow database to workflow_user
GRANT ALL PRIVILEGES ON DATABASE workflow TO workflow_user;

-- Connect to the workflow database
\c workflow;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO workflow_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO workflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO workflow_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO workflow_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES IN SCHEMA public TO workflow_user;
