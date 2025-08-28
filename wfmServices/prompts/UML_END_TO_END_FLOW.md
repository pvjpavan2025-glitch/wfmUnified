# 🏗️ WFM System UML - End-to-End Flow

## 📋 System Overview

This UML diagram represents the complete end-to-end flow of the Workforce Management (WFM) system, showing all microservices, their interactions, data flow, and the complete user journey from authentication to analytics.

---

## 🔄 Sequence Diagram - Complete End-to-End Flow

```mermaid
sequenceDiagram
    participant Client
    participant AuthService as 🔐 Auth Service
    participant ConfigService as ⚙️ Config Service
    participant RulesService as 🎯 Rules Service
    participant SchedulerService as 📅 Scheduler Service
    participant IssueService as 🐛 Issue Service
    participant AnalyticsService as 📊 Analytics Service
    participant MongoDB as 🗄️ MongoDB
    participant Redis as 🔄 Redis

    Note over Client,Redis: Phase 1: System Setup & Authentication
    
    Client->>AuthService: POST /auth/login
    Note right of Client: {username, password, tenant_id}
    AuthService->>MongoDB: Query user credentials
    MongoDB-->>AuthService: User data
    AuthService->>AuthService: Generate JWT token
    AuthService-->>Client: {access_token, user_info}
    
    Client->>ConfigService: POST /configs
    Note right of Client: {key, value, tenant_id}
    ConfigService->>MongoDB: Store configuration
    MongoDB-->>ConfigService: Config saved
    ConfigService-->>Client: Configuration created
    
    Client->>RulesService: POST /rules
    Note right of Client: {name, conditions, actions, tenant_id}
    RulesService->>MongoDB: Store business rule
    MongoDB-->>RulesService: Rule saved
    RulesService-->>Client: Rule created
    
    Note over Client,Redis: Phase 2: Core Operations - Job Scheduling
    
    Client->>SchedulerService: POST /jobs
    Note right of Client: {title, description, priority, skills}
    SchedulerService->>MongoDB: Store job details
    MongoDB-->>SchedulerService: Job saved
    SchedulerService-->>Client: Job created
    
    Client->>SchedulerService: POST /jobs/{id}/schedule
    Note right of Client: {scheduling_strategy}
    SchedulerService->>RulesService: Evaluate scheduling rules
    RulesService->>Redis: Get cached rules
    Redis-->>RulesService: Rules data
    RulesService-->>SchedulerService: Rule evaluation result
    SchedulerService->>MongoDB: Find available analysts
    MongoDB-->>SchedulerService: Analyst list
    SchedulerService->>SchedulerService: Calculate optimal assignment
    SchedulerService->>MongoDB: Update job with schedule
    MongoDB-->>SchedulerService: Schedule saved
    SchedulerService-->>Client: Job scheduled
    
    Note over Client,Redis: Phase 3: Issue Management
    
    Client->>IssueService: POST /issues
    Note right of Client: {title, description, priority, job_id}
    IssueService->>MongoDB: Create issue record
    MongoDB-->>IssueService: Issue saved
    IssueService->>Redis: Cache issue data
    IssueService-->>Client: Issue created
    
    Client->>IssueService: POST /issues/{id}/comments
    Note right of Client: {content, tenant_id}
    IssueService->>MongoDB: Add comment
    MongoDB-->>IssueService: Comment saved
    IssueService-->>Client: Comment added
    
    Note over Client,Redis: Phase 4: Analytics & Reporting
    
    Client->>AnalyticsService: GET /metrics/performance
    Note right of Client: {time_range, group_by}
    AnalyticsService->>MongoDB: Query performance data
    MongoDB-->>AnalyticsService: Raw metrics
    AnalyticsService->>AnalyticsService: Process analytics
    AnalyticsService->>Redis: Cache results
    AnalyticsService-->>Client: Performance metrics
    
    Client->>AnalyticsService: POST /reports/generate
    Note right of Client: {report_type, parameters}
    AnalyticsService->>MongoDB: Aggregate data
    MongoDB-->>AnalyticsService: Aggregated data
    AnalyticsService->>AnalyticsService: Generate report
    AnalyticsService-->>Client: Report generated
```

---

## 🏗️ Component Diagram - System Architecture

```mermaid
graph TB
    subgraph "🌐 Client Layer"
        WebClient[Web Client]
        MobileClient[Mobile Client]
        APIClient[API Client]
    end
    
    subgraph "🔐 Authentication Layer"
        AuthService[Auth Service<br/>Port: 8000]
        JWT[JWT Token Manager]
        RBAC[Role-Based Access Control]
    end
    
    subgraph "⚙️ Configuration Layer"
        ConfigService[Config Service<br/>Port: 8002]
        ConfigCache[Configuration Cache]
        ConfigValidator[Config Validator]
    end
    
    subgraph "🎯 Rules Engine Layer"
        RulesService[Rules Service<br/>Port: 8001]
        RulesEngine[Rules Engine]
        ConditionEvaluator[Condition Evaluator]
        ActionExecutor[Action Executor]
    end
    
    subgraph "📅 Scheduling Layer"
        SchedulerService[Scheduler Service<br/>Port: 8005]
        JobScheduler[Job Scheduler]
        AnalystManager[Analyst Manager]
        AvailabilityChecker[Availability Checker]
    end
    
    subgraph "🐛 Issue Management Layer"
        IssueService[Issue Service<br/>Port: 8003]
        IssueTracker[Issue Tracker]
        CommentManager[Comment Manager]
        EscalationHandler[Escalation Handler]
    end
    
    subgraph "📊 Analytics Layer"
        AnalyticsService[Analytics Service<br/>Port: 8004]
        MetricsCollector[Metrics Collector]
        ReportGenerator[Report Generator]
        DashboardManager[Dashboard Manager]
    end
    
    subgraph "🗄️ Data Layer"
        MongoDB[(MongoDB<br/>Port: 27018)]
        Redis[(Redis<br/>Port: 6380)]
    end
    
    subgraph "🔄 Communication Layer"
        MessageQueue[Message Queue]
        EventBus[Event Bus]
        ServiceDiscovery[Service Discovery]
    end
    
    %% Client connections
    WebClient --> AuthService
    MobileClient --> AuthService
    APIClient --> AuthService
    
    %% Authentication flow
    AuthService --> JWT
    AuthService --> RBAC
    AuthService --> MongoDB
    
    %% Configuration flow
    ConfigService --> ConfigCache
    ConfigService --> ConfigValidator
    ConfigService --> MongoDB
    ConfigService --> Redis
    
    %% Rules flow
    RulesService --> RulesEngine
    RulesEngine --> ConditionEvaluator
    RulesEngine --> ActionExecutor
    RulesService --> MongoDB
    RulesService --> Redis
    
    %% Scheduling flow
    SchedulerService --> JobScheduler
    SchedulerService --> AnalystManager
    SchedulerService --> AvailabilityChecker
    SchedulerService --> MongoDB
    SchedulerService --> Redis
    
    %% Issue management flow
    IssueService --> IssueTracker
    IssueService --> CommentManager
    IssueService --> EscalationHandler
    IssueService --> MongoDB
    IssueService --> Redis
    
    %% Analytics flow
    AnalyticsService --> MetricsCollector
    AnalyticsService --> ReportGenerator
    AnalyticsService --> DashboardManager
    AnalyticsService --> MongoDB
    AnalyticsService --> Redis
    
    %% Inter-service communication
    SchedulerService --> RulesService
    IssueService --> SchedulerService
    AnalyticsService --> IssueService
    AnalyticsService --> SchedulerService
    
    %% Data layer
    MongoDB --> Redis
    Redis --> MongoDB
    
    %% Communication layer
    MessageQueue --> EventBus
    EventBus --> ServiceDiscovery
```

---

## 📊 Class Diagram - Core Entities

```mermaid
classDiagram
    class User {
        +String id
        +String username
        +String email
        +String tenant_id
        +String status
        +List~String~ role_ids
        +DateTime created_at
        +DateTime updated_at
        +authenticate()
        +has_permission()
    }
    
    class Role {
        +String id
        +String name
        +String description
        +String tenant_id
        +List~String~ permission_ids
        +String status
        +DateTime created_at
        +DateTime updated_at
    }
    
    class Job {
        +String id
        +String title
        +String description
        +String tenant_id
        +String priority
        +String status
        +String assigned_analyst_id
        +DateTime deadline
        +List~String~ required_skills
        +DateTime created_at
        +DateTime updated_at
        +schedule()
        +assign_analyst()
    }
    
    class Analyst {
        +String id
        +String name
        +String email
        +String tenant_id
        +List~String~ skills
        +Integer experience_years
        +Integer max_jobs
        +Dict availability
        +String status
        +DateTime created_at
        +DateTime updated_at
        +is_available()
        +get_workload()
    }
    
    class Issue {
        +String id
        +String title
        +String description
        +String tenant_id
        +String priority
        +String category
        +String assigned_to
        +String reported_by
        +String job_id
        +String status
        +DateTime created_at
        +DateTime updated_at
        +escalate()
        +add_comment()
    }
    
    class Rule {
        +String id
        +String name
        +String description
        +String tenant_id
        +String tag_name
        +Integer sequence
        +Dict conditions
        +List~Dict~ actions
        +String status
        +DateTime created_at
        +DateTime updated_at
        +evaluate()
        +execute_actions()
    }
    
    class Configuration {
        +String id
        +String key
        +Dict value
        +String tenant_id
        +String description
        +String category
        +DateTime created_at
        +DateTime updated_at
        +validate()
        +get_value()
    }
    
    class Report {
        +String id
        +String name
        +String report_type
        +Dict parameters
        +String tenant_id
        +String status
        +DateTime created_at
        +DateTime updated_at
        +generate()
        +export()
    }
    
    %% Relationships
    User ||--o{ Role : has
    User ||--o{ Job : creates
    User ||--o{ Issue : reports
    Analyst ||--o{ Job : assigned_to
    Job ||--o{ Issue : related_to
    Rule ||--o{ Job : affects
    Configuration ||--o{ Job : configures
    Report ||--o{ Job : analyzes
    Report ||--o{ Issue : analyzes
```

---

## 🔄 State Machine Diagram - Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created : Job created
    Created --> Validated : Validation passed
    Validated --> Queued : Added to queue
    Queued --> Scheduled : Rules evaluated
    Scheduled --> Assigned : Analyst assigned
    Assigned --> InProgress : Work started
    InProgress --> OnHold : Paused
    OnHold --> InProgress : Resumed
    InProgress --> Review : Work completed
    Review --> Completed : Approved
    Review --> InProgress : Rejected
    Completed --> [*] : Job finished
    
    InProgress --> Escalated : SLA breach
    Escalated --> InProgress : Resolved
    Escalated --> Cancelled : Cannot resolve
    Cancelled --> [*] : Job cancelled
```

---

## 🎯 Activity Diagram - Complete Workflow

```mermaid
flowchart TD
    Start([Start]) --> Auth{Authenticate User}
    Auth -->|Success| Config[Setup Configuration]
    Auth -->|Failed| Error1[Authentication Error]
    Error1 --> End([End])
    
    Config --> Rules[Create Business Rules]
    Rules --> CreateJob[Create Job]
    CreateJob --> ValidateJob{Validate Job}
    ValidateJob -->|Valid| ScheduleJob[Schedule Job]
    ValidateJob -->|Invalid| Error2[Validation Error]
    Error2 --> End
    
    ScheduleJob --> EvaluateRules[Evaluate Rules]
    EvaluateRules --> FindAnalyst[Find Available Analyst]
    FindAnalyst --> AssignJob[Assign Job to Analyst]
    AssignJob --> StartWork[Analyst Starts Work]
    
    StartWork --> MonitorProgress[Monitor Progress]
    MonitorProgress --> CheckIssues{Issues Found?}
    CheckIssues -->|Yes| CreateIssue[Create Issue]
    CheckIssues -->|No| ContinueWork[Continue Work]
    
    CreateIssue --> TrackIssue[Track Issue Resolution]
    TrackIssue --> IssueResolved{Issue Resolved?}
    IssueResolved -->|Yes| ContinueWork
    IssueResolved -->|No| EscalateIssue[Escalate Issue]
    EscalateIssue --> ContinueWork
    
    ContinueWork --> WorkComplete{Work Complete?}
    WorkComplete -->|No| MonitorProgress
    WorkComplete -->|Yes| GenerateReport[Generate Analytics Report]
    
    GenerateReport --> End
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
```

---

## 📊 Data Flow Diagram

```mermaid
graph LR
    subgraph "Input Sources"
        A[User Input]
        B[System Events]
        C[External APIs]
    end
    
    subgraph "Processing Layer"
        D[Auth Service]
        E[Config Service]
        F[Rules Engine]
        G[Scheduler]
        H[Issue Handler]
        I[Analytics Engine]
    end
    
    subgraph "Data Storage"
        J[(MongoDB)]
        K[(Redis Cache)]
    end
    
    subgraph "Output Destinations"
        L[User Interface]
        M[Reports]
        N[Notifications]
        O[External Systems]
    end
    
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    
    B --> F
    B --> G
    B --> H
    
    C --> I
    
    D --> J
    D --> K
    E --> J
    E --> K
    F --> J
    F --> K
    G --> J
    G --> K
    H --> J
    H --> K
    I --> J
    I --> K
    
    J --> L
    J --> M
    J --> N
    J --> O
    
    K --> L
    K --> M
    K --> N
    K --> O
```

---

## 🔐 Security Architecture Diagram

```mermaid
graph TB
    subgraph "🔒 Security Layer"
        JWT[JWT Authentication]
        RBAC[Role-Based Access Control]
        RateLimit[Rate Limiting]
        InputValidation[Input Validation]
        AuditLog[Audit Logging]
    end
    
    subgraph "🌐 API Gateway"
        Gateway[API Gateway]
        LoadBalancer[Load Balancer]
        SSL[SSL/TLS]
    end
    
    subgraph "🔧 Microservices"
        Auth[Auth Service]
        Config[Config Service]
        Rules[Rules Service]
        Scheduler[Scheduler Service]
        Issue[Issue Service]
        Analytics[Analytics Service]
    end
    
    subgraph "🗄️ Data Layer"
        MongoDB[(MongoDB)]
        Redis[(Redis)]
    end
    
    Gateway --> JWT
    Gateway --> RBAC
    Gateway --> RateLimit
    Gateway --> InputValidation
    Gateway --> AuditLog
    
    JWT --> Auth
    RBAC --> Auth
    RateLimit --> Auth
    InputValidation --> Auth
    AuditLog --> Auth
    
    Auth --> Config
    Auth --> Rules
    Auth --> Scheduler
    Auth --> Issue
    Auth --> Analytics
    
    Config --> MongoDB
    Rules --> MongoDB
    Scheduler --> MongoDB
    Issue --> MongoDB
    Analytics --> MongoDB
    
    Config --> Redis
    Rules --> Redis
    Scheduler --> Redis
    Issue --> Redis
    Analytics --> Redis
```

---

## 📋 Key Features Demonstrated

### ✅ **Authentication & Authorization**
- JWT-based authentication
- Role-based access control
- Multi-tenant isolation
- Secure token management

### ✅ **Configuration Management**
- Dynamic configuration updates
- Tenant-specific settings
- Caching for performance
- Validation and versioning

### ✅ **Rules Engine**
- Business rule evaluation
- Condition-based actions
- Real-time rule processing
- Caching for efficiency

### ✅ **Job Scheduling**
- Intelligent job assignment
- Skill-based matching
- Availability checking
- Workload balancing

### ✅ **Issue Management**
- Issue tracking and resolution
- Comment and attachment support
- SLA monitoring
- Escalation handling

### ✅ **Analytics & Reporting**
- Real-time metrics collection
- Performance analytics
- Custom report generation
- Dashboard visualization

---

## 🚀 System Benefits

1. **Scalability**: Microservices architecture allows independent scaling
2. **Reliability**: Fault isolation and redundancy
3. **Maintainability**: Clear separation of concerns
4. **Security**: Multi-layered security approach
5. **Performance**: Caching and optimization strategies
6. **Flexibility**: Easy to extend and modify

---

**Status: ✅ Complete UML Documentation Created**

The UML diagrams provide a comprehensive view of the WFM system's end-to-end flow, architecture, and interactions between all components. 