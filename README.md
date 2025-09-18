# WFM Unified Application

[![Build Status](https://dev.azure.com/tsaro/WFM/_apis/build/status%2FwfmUnified?branchName=main)](https://dev.azure.com/tsaro/WFM/_build/latest?definitionId=4&branchName=main)

This repository contains the integrated Workforce Management (WFM) system with Order-Process-Task workflow architecture and BPMN modeling capabilities.

## Architecture Overview

The system implements an **Order-Process-Task** hierarchical workflow architecture:

### Core Components
1. **wfmApp** - Next.js frontend with Order-Process-Task UI and integrated BPMN modeler
2. **wfmServices** - API Gateway and core backend services
3. **wfmProcess** - SpiffWorkflow BPMN engine for process execution
4. **intServices** - Integration layer for external systems
5. **vendor-service** - Vendor and technician management
6. **process-service** - BPMN process management and execution

### Workflow Hierarchy
- **Orders**: Top-level work requests from external systems (OSM, CRM)
- **Processes**: BPMN workflows that define how to fulfill orders
- **Tasks**: Individual work items assigned to technicians with leads

### Key Principles
- Orders contain multiple Processes
- Processes contain multiple Tasks
- Only Tasks can be assigned/scheduled to technicians
- Each task assignment requires both a Technician and Team Lead
- BPMN diagrams represent Processes and are executed by SpiffWorkflow

## Key Features

### Frontend Features
- **Order Management**: Complete order lifecycle with process and task visibility
- **Task Management**: Advanced task assignment with technician + lead pairing
- **Vendor Management**: Comprehensive vendor, technician, and team lead management
- **BPMN Modeling**: Integrated workflow designer for process creation
- **Dashboard**: Real-time metrics for orders, processes, tasks, and technician utilization
- **Unified Interface**: Single application with consistent navigation

### Backend Features
- **Microservices Architecture**: Scalable, independent services
- **BPMN Process Engine**: SpiffWorkflow integration for workflow execution
- **Rules Engine**: Automatic process identification from order metadata
- **Scheduling System**: Advanced task assignment with skill matching
- **Analytics**: Performance tracking and utilization metrics
- **API Gateway**: Centralized routing and authentication

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.9+ (for backend development)

### Development Setup

1. **Clone and setup the repository:**
   ```bash
   git clone <repository-url>
   cd wfm-unified
   ```

2. **Install frontend dependencies:**
   ```bash
   cd wfm/wfmApp
   npm install --legacy-peer-deps
   ```

3. **Start the unified application:**
   ```bash
   # From the root directory
   docker-compose up -d
   ```

### Service Ports

- **Frontend (wfmApp)**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001
- **Config Service**: http://localhost:8002
- **Rules Service**: http://localhost:8003
- **Scheduler Service**: http://localhost:8004
- **Issue Service**: http://localhost:8005
- **Analytics Service**: http://localhost:8006
- **Dashboard Service**: http://localhost:8007
- **Order Service**: http://localhost:8008
- **Vendor Service**: http://localhost:8009
- **Process Service**: http://localhost:8010
- **BPMN Backend**: http://localhost:8100
- **Traefik Dashboard**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Order-Process-Task Workflow

### Workflow Lifecycle

1. **Order Creation**: External systems (OSM, CRM) create orders with metadata
2. **Process Identification**: Rules service analyzes order metadata to identify required processes
3. **Process Instantiation**: BPMN processes are created and executed via SpiffWorkflow
4. **Task Generation**: Processes generate specific tasks that need completion
5. **Task Assignment**: Tasks are assigned to technician + lead pairs based on skills and availability
6. **Task Execution**: Technicians complete tasks with lead oversight
7. **Process Completion**: All tasks complete, marking the process as finished
8. **Order Fulfillment**: All processes complete, fulfilling the original order

### Data Flow

### OSM XML Integration
```
OSM XML → XMLToJSONParser → OSMXMLMapper → OSMMapper → Rules Engine Format


   ### Key Features
   - Dual Format Support: Handles both XML and JSON inputs seamlessly
   - Structure Validation: Validates OSM XML structure before processing
   - Error Handling: Comprehensive error handling with meaningful messages
   - Type Conversion: Intelligent conversion of XML strings to appropriate Python types
   - Backward Compatibility: Existing JSON workflows remain unchanged
   - Comprehensive Testing: Full test coverage for XML functionality
```
End to End flow

```
External System → Order → Rules Engine → Process Selection → BPMN Execution → Task Creation → Assignment → Completion
```

XML to JSON Flow Summary
```
OSM XML Input → Integration Service → JSON Processing → Rules Engine → Process Selection → JSON Response → XML Conversion → XML Output File
```


The Order refers to below OSM XML integration i.e.,
```
Order (OSM XML → XMLToJSONParser → OSMXMLMapper → OSMMapper → Rules Engine Format) → Rules Engine → Process Selection → BPMN Execution → Task Creation → Assignment → Completion (JSON Response → XML Conversion → XML Output File)
```


### Integration Points

- **Frontend Integration**: Unified wfmApp with Order, Task, Vendor, and BPMN modeling pages
- **Backend Integration**: Microservices communicate via API Gateway
- **Process Integration**: SpiffWorkflow engine executes BPMN processes
- **Database Integration**: MongoDB for WFM data, PostgreSQL for BPMN engine
- **External Integration**: APIs for OSM, CRM, and other external systems

### Key Files

#### Configuration
- `/docker-compose.yml` - Unified deployment configuration
- `/AZURE_DEPLOYMENT_GUIDE.md` - Azure deployment instructions
- `/.env.example` - Environment variable template

#### Frontend (wfmApp)
- `/wfmApp/app/orders/page.tsx` - Order management interface
- `/wfmApp/app/tasks/page.tsx` - Task management interface  
- `/wfmApp/app/vendors/page.tsx` - Vendor management interface
- `/wfmApp/app/modelling/page.tsx` - BPMN modeling interface
- `/wfmApp/components/task-management.tsx` - Task assignment and tracking
- `/wfmApp/components/dashboard-content.tsx` - Order-Process-Task metrics
- `/wfmApp/components/app-shell.tsx` - Navigation with new menu items

#### Backend Services
- `/wfmServices/` - Core WFM microservices
- `/wfmServices/vendor_service/` - Vendor and technician management
- `/wfmServices/process_service/` - Process management and BPMN integration
- `/wfmProcess/backend/` - SpiffWorkflow BPMN engine
- `/intServices/` - External system integrations

## Development Workflow

### Branch Strategy

- **feature/load-save-intg** - Current integration branch (both repos)
- Create feature branches from this branch for additional work

### Making Changes

1. **Frontend Changes**: Work in `/wfm/wfmApp/`
2. **Backend Services**: Work in `/wfm/wfmServices/`
3. **BPMN Engine**: Work in `/wfmProcess/backend/`
4. **Integration Services**: Work in `/wfm/intServices/`

### Testing

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down
```

## Environment Configuration

### Production Environment Variables

Update the following in `docker-compose.yml` for production:


### Development Environment

For local development, you can override environment variables:

```bash
# Create .env file in root directory
cp .env.example .env
# Edit .env with your local configuration
```

## Environment Variables

### Offline Queue & Synchronization (BPMN Modeler)

These flags control the client-side offline queue for BPMN diagrams when the backend is unreachable.

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_QUEUE_MAX_SIZE` | `20` | Maximum number of queued diagrams retained locally. Oldest is evicted when limit exceeded. |
| `NEXT_PUBLIC_QUEUE_COMPRESSION` | `false` | If `true`, queued XML is gzip-compressed via `CompressionStream` when supported. Falls back to plain text if not available. |
| `NEXT_PUBLIC_QUEUE_ENCRYPTION` | `false` | If `true`, queued payload (after optional compression) is encrypted with an AES-GCM key. The client now first attempts to fetch a server-distributed key from `/api/security/encryption-key` (ephemeral, in-memory) falling back to a locally generated key. |

### BPMN Offline Sync & Conflict Handling (Enhanced)

Recent enhancements to the BPMN modeler offline queue & conflict resolution:

1. Semantic Structural Diff:
   - Diffs are computed by parsing BPMN XML and comparing elements by `id` & `tagName`.
   - Counts surfaced: Added elements, Remote-only elements, Modified elements.
   - Additional semantic enrichment: adopted `camunda:assignee`, imported `extensionElements`, and documentation adoption when missing locally.

2. Semantic Merge Strategy:
   - Remote-only elements appended to the local diagram.
   - Local changes always preserved (local wins for name/content already present).
   - Missing local properties (name, documentation, `camunda:assignee`, `extensionElements`) are filled from remote.
   - Future extension target: candidate groups, due dates, timers.

3. Visual Diff Overlays:
   - Added (green), Changed (amber), Remote-only (red) badges rendered via bpmn-js overlays during conflict modal.
   - Overlays cleared automatically after resolution.

4. Conflict Resolution Actions:
   - Skip: Leaves item in queue.
   - Overwrite: Local diagram overwrites remote.
   - Merge: Performs semantic merge before overwrite.
   - Rename: Stores local as a new filename (preserving remote original).

5. Audit Logging & Persistence:
   - Client posts conflict resolution events to `/api/audit/conflicts` with diff metadata.
   - Server persists audit log (best-effort) to `tmp/conflict-audit.json` (override path with `AUDIT_LOG_DIR`).
   - Download raw log: `GET /api/audit/conflicts/download` (returns JSON file).
   - In-memory cache keeps last 200 (file rotation trims to 500 total for persistence).

6. Security Note:
   - Encryption key delivered from server endpoint (ephemeral, non-rotating demo). For production: implement key rotation & per-user scoping or wrap with KMS.

### Audit Log Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_LOG_DIR` | `./tmp` | Directory for persisted conflict audit JSON file. |

### New API Endpoints (BPMN Modeller Support)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/security/encryption-key` | GET | Returns AES-GCM JWK for encrypting offline queue entries (if enabled). |
| `/api/audit/conflicts` | GET/POST | Retrieve or append conflict resolution audit records. |
| `/api/audit/conflicts/download` | GET | Download raw persisted audit log JSON. |

### Local Storage Keys (Updated)

| Key | Purpose |
|-----|---------|
| `bpmn_pending_syncs_v2` | Metadata list of queued BPMN diagrams awaiting sync. |
| `bpmn_queue_enc_key_v2_server` | Cached AES-GCM JWK (server-fetched or locally generated fallback). |
| `bpmn_conflict_audit_v1` | Client-side rolling conflict event history (for quick inspection). |

### Future Roadmap (Suggested)

| Item | Description |
|------|-------------|
| Candidate Group Merge | Reconcile `camunda:candidateGroups` & `camunda:candidateUsers`. |
| Timer/Event Detail Diff | Classify timer/event definition changes distinctly. |
| BPMN Validation Gate | Run schema & lint pass pre-sync to avoid corrupt remote state. |
| Key Rotation | Time or usage-based server key rotation with client re-fetch & re-encryption. |
| Persistent Store | Replace in-memory + file with Redis / DB for multi-instance scaling. |

Behavior Notes:
* Compression happens before encryption for better ratios.
* Each queued item stores metadata (hash, compression/encryption flags) in `localStorage` under `bpmn_pending_syncs_v2`.
* Evictions emit an info toast identifying the removed diagram.
* Encryption key (if enabled) persists under `bpmn_queue_enc_key_v1`.
* Conflict detection on sync: if a remote temp item with the same filename exists, a modal prompts to Skip, Overwrite, or Merge (current merge = overwrite with local; future enhancement could implement a structural BPMN merge).

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3000, 8000-8008, 5432, 6379 are available
2. **Docker Network**: If services can't communicate, check network configuration
3. **Dependencies**: Run `npm install --legacy-peer-deps` in wfmApp for BPMN packages
4. **Database Connection**: Ensure PostgreSQL is healthy before starting BPMN backend

### Logs and Debugging

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs wfmapp
docker-compose logs wfmprocess-backend

# Follow logs in real-time
docker-compose logs -f
```

## Contributing

1. Create feature branch from `feature/load-save-intg`
2. Make changes and test locally
3. Update documentation if needed
4. Submit pull request

## License

[Your License Here]


## for running E2E
### Create virtual environment
python3 -m venv venv

### Activate it
source venv/bin/activate

### Install requirements
pip install -r requirements-test.txt

### Running the Test
cd /Users/pavan.pvj/code/wfmUnified
python -m e2e.test_osm_flow