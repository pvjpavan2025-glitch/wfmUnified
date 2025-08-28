// MongoDB initialization script for WFM
// This script sets up the initial database structure and indexes

// Switch to the WFM database
db = db.getSiblingDB('wfm');

print("Initializing WFM database...");

// Create collections
db.createCollection("users");
db.createCollection("roles");
db.createCollection("permissions");
db.createCollection("tenants");
db.createCollection("configs");
db.createCollection("config_versions");
db.createCollection("rules");
db.createCollection("processes");
db.createCollection("tasks");
db.createCollection("jobs");
db.createCollection("analysts");
db.createCollection("schedules");
db.createCollection("issues");
db.createCollection("reports");
db.createCollection("metrics");
db.createCollection("audit_logs");

print("Collections created successfully");

// Create indexes for better performance
print("Creating indexes...");

// Users collection indexes
db.users.createIndex({ "tenant_id": 1 });
db.users.createIndex({ "username": 1, "tenant_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1, "tenant_id": 1 }, { unique: true });

// Roles collection indexes
db.roles.createIndex({ "tenant_id": 1 });
db.roles.createIndex({ "name": 1, "tenant_id": 1 }, { unique: true });

// Permissions collection indexes
db.permissions.createIndex({ "tenant_id": 1 });
db.permissions.createIndex({ "resource": 1, "action": 1, "tenant_id": 1 }, { unique: true });

// Tenants collection indexes
db.tenants.createIndex({ "domain": 1 }, { unique: true });

// Configs collection indexes
db.configs.createIndex({ "tenant_id": 1 });
db.configs.createIndex({ "key": 1, "tenant_id": 1, "environment": 1 }, { unique: true });

// Rules collection indexes
db.rules.createIndex({ "tenant_id": 1 });
db.rules.createIndex({ "name": 1, "tenant_id": 1 }, { unique: true });
db.rules.createIndex({ "category": 1, "tenant_id": 1 });

// Jobs collection indexes
db.jobs.createIndex({ "tenant_id": 1 });
db.jobs.createIndex({ "status": 1, "tenant_id": 1 });
db.jobs.createIndex({ "created_at": -1, "tenant_id": 1 });

// Issues collection indexes
db.issues.createIndex({ "tenant_id": 1 });
db.issues.createIndex({ "status": 1, "tenant_id": 1 });
db.issues.createIndex({ "priority": 1, "tenant_id": 1 });
db.issues.createIndex({ "created_at": -1, "tenant_id": 1 });

// Reports collection indexes
db.reports.createIndex({ "tenant_id": 1 });
db.reports.createIndex({ "type": 1, "tenant_id": 1 });

// Audit logs collection indexes
db.audit_logs.createIndex({ "tenant_id": 1 });
db.audit_logs.createIndex({ "user_id": 1, "tenant_id": 1 });
db.audit_logs.createIndex({ "timestamp": -1, "tenant_id": 1 });
db.audit_logs.createIndex({ "action": 1, "tenant_id": 1 });

print("Indexes created successfully");

// Create default tenant
print("Creating default tenant...");
db.tenants.insertOne({
    _id: ObjectId(),
    name: "Default Tenant",
    domain: "default",
    status: "active",
    settings: {
        "timezone": "UTC",
        "date_format": "YYYY-MM-DD",
        "time_format": "HH:mm:ss"
    },
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
    updated_by: "system"
});

// Create default roles
print("Creating default roles...");
const defaultTenantId = db.tenants.findOne({ domain: "default" })._id;

db.roles.insertMany([
    {
        _id: ObjectId(),
        name: "admin",
        description: "System Administrator",
        tenant_id: defaultTenantId,
        permission_ids: [],
        status: "active",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    },
    {
        _id: ObjectId(),
        name: "manager",
        description: "Team Manager",
        tenant_id: defaultTenantId,
        permission_ids: [],
        status: "active",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    },
    {
        _id: ObjectId(),
        name: "analyst",
        description: "Data Analyst",
        tenant_id: defaultTenantId,
        permission_ids: [],
        status: "active",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    }
]);

// Create default permissions
print("Creating default permissions...");
const permissions = [
    // User management
    { name: "user:create", description: "Create users", resource: "users", action: "create", tenant_id: defaultTenantId },
    { name: "user:read", description: "Read users", resource: "users", action: "read", tenant_id: defaultTenantId },
    { name: "user:update", description: "Update users", resource: "users", action: "update", tenant_id: defaultTenantId },
    { name: "user:delete", description: "Delete users", resource: "users", action: "delete", tenant_id: defaultTenantId },
    
    // Configuration management
    { name: "config:create", description: "Create configurations", resource: "configs", action: "create", tenant_id: defaultTenantId },
    { name: "config:read", description: "Read configurations", resource: "configs", action: "read", tenant_id: defaultTenantId },
    { name: "config:update", description: "Update configurations", resource: "configs", action: "update", tenant_id: defaultTenantId },
    { name: "config:delete", description: "Delete configurations", resource: "configs", action: "delete", tenant_id: defaultTenantId },
    
    // Rules management
    { name: "rule:create", description: "Create rules", resource: "rules", action: "create", tenant_id: defaultTenantId },
    { name: "rule:read", description: "Read rules", resource: "rules", action: "read", tenant_id: defaultTenantId },
    { name: "rule:update", description: "Update rules", resource: "rules", action: "update", tenant_id: defaultTenantId },
    { name: "rule:delete", description: "Delete rules", resource: "rules", action: "delete", tenant_id: defaultTenantId },
    { name: "rule:evaluate", description: "Evaluate rules", resource: "rules", action: "evaluate", tenant_id: defaultTenantId },
    
    // Job management
    { name: "job:create", description: "Create jobs", resource: "jobs", action: "create", tenant_id: defaultTenantId },
    { name: "job:read", description: "Read jobs", resource: "jobs", action: "read", tenant_id: defaultTenantId },
    { name: "job:update", description: "Update jobs", resource: "jobs", action: "update", tenant_id: defaultTenantId },
    { name: "job:delete", description: "Delete jobs", resource: "jobs", action: "delete", tenant_id: defaultTenantId },
    { name: "job:schedule", description: "Schedule jobs", resource: "jobs", action: "schedule", tenant_id: defaultTenantId },
    
    // Issue management
    { name: "issue:create", description: "Create issues", resource: "issues", action: "create", tenant_id: defaultTenantId },
    { name: "issue:read", description: "Read issues", resource: "issues", action: "read", tenant_id: defaultTenantId },
    { name: "issue:update", description: "Update issues", resource: "issues", action: "update", tenant_id: defaultTenantId },
    { name: "issue:delete", description: "Delete issues", resource: "issues", action: "delete", tenant_id: defaultTenantId },
    { name: "issue:escalate", description: "Escalate issues", resource: "issues", action: "escalate", tenant_id: defaultTenantId },
    
    // Reports and analytics
    { name: "report:create", description: "Create reports", resource: "reports", action: "create", tenant_id: defaultTenantId },
    { name: "report:read", description: "Read reports", resource: "reports", action: "read", tenant_id: defaultTenantId },
    { name: "report:update", description: "Update reports", resource: "reports", action: "update", tenant_id: defaultTenantId },
    { name: "report:delete", description: "Delete reports", resource: "reports", action: "delete", tenant_id: defaultTenantId },
    { name: "metrics:read", description: "Read metrics", resource: "metrics", action: "read", tenant_id: defaultTenantId }
];

permissions.forEach(permission => {
    permission._id = ObjectId();
    permission.created_at = new Date();
    permission.updated_at = new Date();
    permission.created_by = "system";
    permission.updated_by = "system";
});

db.permissions.insertMany(permissions);

// Update roles with permissions
print("Updating roles with permissions...");
const adminRole = db.roles.findOne({ name: "admin", tenant_id: defaultTenantId });
const managerRole = db.roles.findOne({ name: "manager", tenant_id: defaultTenantId });
const analystRole = db.roles.findOne({ name: "analyst", tenant_id: defaultTenantId });

// Get all permission IDs
const allPermissionIds = db.permissions.find({ tenant_id: defaultTenantId }).map(p => p._id);

// Admin gets all permissions
db.roles.updateOne(
    { _id: adminRole._id },
    { $set: { permission_ids: allPermissionIds } }
);

// Manager gets most permissions except user management
const managerPermissionIds = db.permissions.find({
    tenant_id: defaultTenantId,
    name: { $nin: ["user:create", "user:delete"] }
}).map(p => p._id);

db.roles.updateOne(
    { _id: managerRole._id },
    { $set: { permission_ids: managerPermissionIds } }
);

// Analyst gets read permissions and job management
const analystPermissionIds = db.permissions.find({
    tenant_id: defaultTenantId,
    name: { $in: [
        "user:read", "config:read", "rule:read", "rule:evaluate",
        "job:create", "job:read", "job:update", "job:schedule",
        "issue:create", "issue:read", "issue:update",
        "report:read", "metrics:read"
    ]}
}).map(p => p._id);

db.roles.updateOne(
    { _id: analystRole._id },
    { $set: { permission_ids: analystPermissionIds } }
);

// Create default admin user
print("Creating default admin user...");
const adminRoleId = adminRole._id;
const adminUser = {
    _id: ObjectId(),
    username: "admin",
    email: "admin@wfm.local",
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KqK9K", // "admin123"
    first_name: "Admin",
    last_name: "User",
    tenant_id: defaultTenantId,
    role_ids: [adminRoleId],
    status: "active",
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
    updated_by: "system"
};

db.users.insertOne(adminUser);

print("Default admin user created:");
print("Username: admin");
print("Password: admin123");
print("Email: admin@wfm.local");

// Create some default configurations
print("Creating default configurations...");
const defaultConfigs = [
    {
        key: "system.name",
        value: "WFM System",
        type: "string",
        description: "System name",
        tenant_id: defaultTenantId,
        environment: "default",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    },
    {
        key: "system.timezone",
        value: "UTC",
        type: "string",
        description: "Default timezone",
        tenant_id: defaultTenantId,
        environment: "default",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    },
    {
        key: "scheduler.max_concurrent_jobs",
        value: "10",
        type: "number",
        description: "Maximum concurrent jobs",
        tenant_id: defaultTenantId,
        environment: "default",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    },
    {
        key: "rules.evaluation_timeout",
        value: "30",
        type: "number",
        description: "Rule evaluation timeout in seconds",
        tenant_id: defaultTenantId,
        environment: "default",
        created_at: new Date(),
        updated_at: new Date(),
        created_by: "system",
        updated_by: "system"
    }
];

db.configs.insertMany(defaultConfigs);

print("Database initialization completed successfully!");
print("Default tenant ID:", defaultTenantId);
print("Default admin user created with username 'admin' and password 'admin123'"); 