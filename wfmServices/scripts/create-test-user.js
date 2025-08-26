// Script to create a test user for frontend authentication testing
// Run this script to create a test user that can be used to login to the frontend

// Switch to the WFM database
db = db.getSiblingDB('wfm');

print("Creating test user for frontend authentication...");

// Create a default tenant
const tenant = {
    _id: ObjectId(),
    name: "Test Tenant",
    domain: "test",
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
};

db.tenants.insertOne(tenant);
const tenantId = tenant._id;

print("Created tenant:", tenant.name, "with ID:", tenantId);

// Create a test role
const role = {
    _id: ObjectId(),
    name: "SuperAdmin",
    description: "Super Administrator with full access",
    tenant_id: tenantId,
    permission_ids: [],
    status: "active",
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
    updated_by: "system"
};

db.roles.insertOne(role);
const roleId = role._id;

print("Created role:", role.name, "with ID:", roleId);

// Create a test user
// Password: test123 (proper bcrypt hash for passlib)
// This hash was generated using the Docker container
const user = {
    _id: ObjectId(),
    username: "testuser",
    email: "test@wfm.local",
    password_hash: "$2b$12$aVURW/59hs0L8s/Q5yOzy.5YL2B/T0jzFfbjJohSMmJcj2uxR96CG", // "test123"
    first_name: "Test",
    last_name: "User",
    tenant_id: tenantId,
    role_ids: [roleId],
    status: "active",
    last_login: null,
    failed_login_attempts: 0,
    locked_until: null,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
    updated_by: "system"
};

db.users.insertOne(user);

print("=== TEST USER CREATED SUCCESSFULLY ===");
print("Username: testuser");
print("Password: test123");
print("Tenant ID:", tenantId);
print("Role: SuperAdmin");
print("Email: test@wfm.local");
print("");
print("You can now use these credentials to login to the frontend!");
print("Frontend URL: http://localhost:5173/login");
