-- WFM Process Engine Database Initialization
-- This script initializes the PostgreSQL database for the WFM Process Engine

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS workflow;
CREATE SCHEMA IF NOT EXISTS process;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set search path
SET search_path TO workflow, process, audit, public;

-- Workflow Definitions Table
CREATE TABLE IF NOT EXISTS workflow.definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    bpmn_xml TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    UNIQUE(name, version)
);

-- Workflow Instances Table
CREATE TABLE IF NOT EXISTS workflow.instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    definition_id UUID NOT NULL REFERENCES workflow.definitions(id),
    status VARCHAR(50) NOT NULL DEFAULT 'RUNNING',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    context JSONB DEFAULT '{}',
    variables JSONB DEFAULT '{}',
    created_by VARCHAR(255),
    CONSTRAINT fk_definition FOREIGN KEY (definition_id) REFERENCES workflow.definitions(id)
);

-- Process Tasks Table
CREATE TABLE IF NOT EXISTS process.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_id UUID NOT NULL REFERENCES workflow.instances(id),
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    assigned_to VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_instance FOREIGN KEY (instance_id) REFERENCES workflow.instances(id)
);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit.logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_id UUID REFERENCES workflow.instances(id),
    task_id UUID REFERENCES process.tasks(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    user_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_workflow_instances_definition_id ON workflow.instances(definition_id);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_status ON workflow.instances(status);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_created_by ON workflow.instances(created_by);

CREATE INDEX IF NOT EXISTS idx_process_tasks_instance_id ON process.tasks(instance_id);
CREATE INDEX IF NOT EXISTS idx_process_tasks_status ON process.tasks(status);
CREATE INDEX IF NOT EXISTS idx_process_tasks_assigned_to ON process.tasks(assigned_to);

CREATE INDEX IF NOT EXISTS idx_audit_logs_instance_id ON audit.logs(instance_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_task_id ON audit.logs(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit.logs(timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_workflow_definitions_updated_at BEFORE UPDATE ON workflow.definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_instances_updated_at BEFORE UPDATE ON workflow.instances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_process_tasks_updated_at BEFORE UPDATE ON process.tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO workflow.definitions (name, version, bpmn_xml, description, created_by) VALUES
('Sample Workflow', '1.0', '<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"><process id="sample" isExecutable="true"><startEvent id="start"/><endEvent id="end"/><sequenceFlow id="flow1" sourceRef="start" targetRef="end"/></process></definitions>', 'A simple sample workflow for testing', 'system')
ON CONFLICT (name, version) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA workflow TO wfmprocess;
GRANT USAGE ON SCHEMA process TO wfmprocess;
GRANT USAGE ON SCHEMA audit TO wfmprocess;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA workflow TO wfmprocess;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA process TO wfmprocess;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO wfmprocess;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA workflow TO wfmprocess;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA process TO wfmprocess;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO wfmprocess;
