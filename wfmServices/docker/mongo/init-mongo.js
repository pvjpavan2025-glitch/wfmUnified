// MongoDB initialization script for WFM system
// This script runs when the MongoDB container starts for the first time

print('🔧 Initializing WFM MongoDB database...');

// Switch to admin database to create user
db = db.getSiblingDB('admin');

// Check if user already exists
var existingUser = db.getUser('wfmadmin');
if (!existingUser) {
    // Create WFM database user
    db.createUser({
        user: 'wfmadmin',
        pwd: 'tsarolabs@12345#',
        roles: [
            {
                role: 'readWrite',
                db: 'wfm'
            },
            {
                role: 'dbAdmin',
                db: 'wfm'
            }
        ]
    });
    print('✅ WFM admin user created successfully');
} else {
    print('ℹ️ WFM admin user already exists, skipping creation');
}

// Switch to WFM database
db = db.getSiblingDB('wfm');

// Create collections (ignore if they already exist)
var collections = ['users', 'orders', 'tasks', 'technicians', 'vendors', 'workflows', 'configurations', 'rules', 'schedules', 'issues', 'analytics', 'dashboard'];

collections.forEach(function(collectionName) {
    try {
        db.createCollection(collectionName);
        print('✅ Collection ' + collectionName + ' created or already exists');
    } catch (e) {
        if (e.code === 48) { // Collection already exists
            print('ℹ️ Collection ' + collectionName + ' already exists');
        } else {
            print('⚠️ Error creating collection ' + collectionName + ': ' + e.message);
        }
    }
});

print('✅ WFM collections setup completed');

// Create indexes for better performance (ignore if they already exist)
try {
    db.users.createIndex({ "email": 1 }, { unique: true });
    print('✅ Users email index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Users email index already exists');
    } else {
        print('⚠️ Error creating users email index: ' + e.message);
    }
}

try {
    db.users.createIndex({ "username": 1 }, { unique: true });
    print('✅ Users username index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Users username index already exists');
    } else {
        print('⚠️ Error creating users username index: ' + e.message);
    }
}

try {
    db.orders.createIndex({ "order_id": 1 }, { unique: true });
    print('✅ Orders order_id index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Orders order_id index already exists');
    } else {
        print('⚠️ Error creating orders order_id index: ' + e.message);
    }
}

try {
    db.orders.createIndex({ "status": 1 });
    print('✅ Orders status index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Orders status index already exists');
    } else {
        print('⚠️ Error creating orders status index: ' + e.message);
    }
}

try {
    db.tasks.createIndex({ "task_id": 1 }, { unique: true });
    print('✅ Tasks task_id index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Tasks task_id index already exists');
    } else {
        print('⚠️ Error creating tasks task_id index: ' + e.message);
    }
}

try {
    db.tasks.createIndex({ "assigned_to": 1 });
    print('✅ Tasks assigned_to index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Tasks assigned_to index already exists');
    } else {
        print('⚠️ Error creating tasks assigned_to index: ' + e.message);
    }
}

try {
    db.workflows.createIndex({ "workflow_id": 1 }, { unique: true });
    print('✅ Workflows workflow_id index created');
} catch (e) {
    if (e.code === 85) { // Index already exists
        print('ℹ️ Workflows workflow_id index already exists');
    } else {
        print('⚠️ Error creating workflows workflow_id index: ' + e.message);
    }
}

print('✅ Database indexes setup completed');

print('🎉 WFM MongoDB initialization completed successfully!');
print('📊 Database: wfm');
print('👤 Admin User: wfmadmin');
print('🔑 Collections: users, orders, tasks, technicians, vendors, workflows, configurations, rules, schedules, issues, analytics, dashboard');
