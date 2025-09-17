# Integration Services (intServices)

FastAPI-based integration layer that ingests payloads from external applications (e.g., OSM, BRM, Activation), transforms them into the canonical Rules API payload, and forwards them to the WFM Rules Service.

## Features
- Application registry with CRUD
- Application Endpoint registry with CRUD
- Pluggable transformation engine (per-app adapters + JSON mapping support)
- **XML-to-JSON conversion layer for OSM systems**
- **Enhanced OSM mapper supporting both XML and JSON inputs**
- Example OSM ingestion endpoint
- Security via API keys / bearer tokens (configurable)
- Async HTTP forwarding to Rules API

## Quickstart

1. Create a virtualenv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Configure environment

Copy `.env.example` to `.env` and fill values (defaults to Postgres).

3. Run the server

```bash
uvicorn app.main:app --reload --port 8082
```

Open: http://localhost:8082/docs
### API key header

All endpoints require an API key header unless you clear `API_KEY` in env.

- Header name: `X-API-Key` (configurable via `API_KEY_NAME`)
- Default value: `change-me-please` (set `API_KEY`)

Example:

```bash
curl -H "X-API-Key: change-me-please" http://localhost:8082/healthz
```


## OSM XML Integration

### Overview
The integration services now support XML payloads from OSM systems through a two-layer mapping architecture:

1. **XML-to-JSON Layer**: Converts OSM XML payloads to structured JSON
2. **JSON-to-Rules Layer**: Transforms JSON to canonical rules engine format

### Supported XML Formats
- `ServiceOrderInstallationRequest` - For fiber installation orders
- `ServiceOrderFeasibilityRequest` - For fiber feasibility checks

### XML Processing Endpoints

#### Process OSM XML
```bash
POST /osm/xml/process
Content-Type: application/xml

# Send raw XML in request body
curl -X POST 'http://localhost:8082/osm/xml/process' \
  -H 'X-API-Key: change-me-please' \
  -H 'Content-Type: application/xml' \
  --data-raw '<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderInstallationRequest>
  <id>ORD-001</id>
  <category>FiberInstallation</category>
  <orderDate>2024-11-09T10:00:00Z</orderDate>
  <!-- ... rest of XML -->
</ServiceOrderInstallationRequest>'
```

#### Validate OSM XML Structure
```bash
POST /osm/xml/validate
Content-Type: application/xml

# Returns validation results without processing
curl -X POST 'http://localhost:8082/osm/xml/validate' \
  -H 'X-API-Key: change-me-please' \
  -H 'Content-Type: application/xml' \
  --data-raw '<XML_CONTENT>'
```

#### Convert XML to JSON (Debug)
```bash
POST /osm/xml/convert
Content-Type: application/xml

# Returns intermediate JSON conversion
curl -X POST 'http://localhost:8082/osm/xml/convert' \
  -H 'X-API-Key: change-me-please' \
  -H 'Content-Type: application/xml' \
  --data-raw '<XML_CONTENT>'
```

### Sample XML Payloads

#### ServiceOrderInstallationRequest
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderInstallationRequest>
  <id>ORD-001</id>
  <externalId>EXT-001</externalId>
  <priority>5</priority>
  <category>FiberInstallation</category>
  <orderDate>2024-11-09T10:00:00Z</orderDate>
  <requestedCompletionDate>2024-11-15T18:00:00Z</requestedCompletionDate>
  <description>Fiber installation for customer</description>
  
  <relatedParty>
    <item>
      <id>CUST-001</id>
      <role>Customer</role>
      <name>John Doe</name>
      <attr_referredType>Individual</attr_referredType>
    </item>
  </relatedParty>
  
  <serviceOrderItem>
    <item>
      <id>ITEM-001</id>
      <action>add</action>
      <service>
        <id>SVC-001</id>
        <category>Broadband</category>
        <serviceType>Fiber</serviceType>
        <serviceSpecification>
          <id>123</id>
          <name>FiberBroadband</name>
          <version>1.0</version>
        </serviceSpecification>
        <serviceCharacteristic>
          <item>
            <name>CPE MAC</name>
            <value>00:11:22:33:44:55</value>
            <valueType>string</valueType>
          </item>
          <item>
            <name>CPE Model</name>
            <value>Router-X1</value>
            <valueType>string</valueType>
          </item>
        </serviceCharacteristic>
        <place>
          <item>
            <id>LOC-001</id>
            <role>InstallationSite</role>
            <attr_type>GeographicAddress</attr_type>
            <street>123 Main Street</street>
            <city>Anytown</city>
            <postalCode>12345</postalCode>
            <country>US</country>
            <geographicLocation>
              <latitude>40.7128</latitude>
              <longitude>-74.0060</longitude>
            </geographicLocation>
          </item>
        </place>
      </service>
    </item>
  </serviceOrderItem>
  
  <note>
    <item>
      <text>Customer prefers morning installation</text>
      <date>2024-11-09T08:00:00Z</date>
      <author>Customer Service</author>
    </item>
  </note>
</ServiceOrderInstallationRequest>
```

#### ServiceOrderFeasibilityRequest
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderFeasibilityRequest>
  <id>ORD-002</id>
  <externalId>EXT-002</externalId>
  <priority>3</priority>
  <category>FiberFeasibility</category>
  <orderDate>2024-11-09T09:00:00Z</orderDate>
  <description>Check fiber availability for address</description>
  
  <relatedParty>
    <item>
      <id>CUST-002</id>
      <role>Customer</role>
      <name>Jane Smith</name>
    </item>
  </relatedParty>
  
  <serviceOrderItem>
    <item>
      <id>ITEM-002</id>
      <action>add</action>
      <service>
        <id>SVC-002</id>
        <category>Broadband</category>
        <serviceType>Fiber</serviceType>
        <serviceCharacteristic>
          <item>
            <name>ConnectionType</name>
            <value>FTTH</value>
            <valueType>string</valueType>
          </item>
          <item>
            <name>SplicingRequired</name>
            <value>true</value>
            <valueType>boolean</valueType>
          </item>
        </serviceCharacteristic>
        <place>
          <item>
            <role>InstallationSite</role>
            <street>456 Oak Avenue</street>
            <city>Somewhere</city>
            <postalCode>67890</postalCode>
            <country>US</country>
          </item>
        </place>
      </service>
    </item>
  </serviceOrderItem>
</ServiceOrderFeasibilityRequest>
```

### Architecture

```
OSM XML → XMLToJSONParser → OSMXMLMapper → OSMMapper → Rules Engine Format
```

1. **XMLToJSONParser**: Generic XML-to-JSON converter with OSM structure handling
2. **OSMXMLMapper**: OSM-specific XML-to-JSON transformation
3. **OSMXMLToRulesMapper**: Combined mapper supporting both XML and JSON inputs
4. **OSMMapper**: Existing JSON-to-rules transformation (unchanged)

### Mapper Registration
- `osm_xml`: Enhanced mapper supporting XML and JSON inputs
- `osm`: Original JSON-only mapper (preserved for backward compatibility)

## Canonical Rules Payload
The canonical target payload is defined in `app/models/rules.py` and used by mappers. See `references/input-order.json` for a sample source payload from OSM.

### 🔧 Supported XML Formats
- ServiceOrderInstallationRequest - Fiber installation orders
- ServiceOrderFeasibilityRequest - Fiber feasibility checks
### 📋 API Endpoints Available
- POST /osm/xml/process - Main XML processing endpoint
- POST /osm/xml/validate - XML validation without processing
- POST /osm/xml/convert - XML-to-JSON conversion for debugging
- GET /osm/xml/health - Service health check


## Docker

Run app + Postgres with data persisted in a named volume:

```bash
docker compose up --build
```

Then visit http://localhost:8082/docs

By default, the service runs with `RULES_API_STUB=true` so you can test end-to-end without a live Rules API. To call a real Rules API, set `RULES_API_STUB=false` and configure `RULES_API_BASE_URL` (default http://localhost:8003 for wfmServices rules-service). If `RULES_API_TOKEN` is not set but `rules_jWT_SECRET` is provided, the service will mint a compatible JWT on-the-fly for wfmServices.

### Optional: Create and schedule jobs

You can have the ingestion endpoint create jobs and schedule them via the wfmServices scheduler-service. Use the query flags:

- `create_job=true` to create a job per order (or per item if `split_jobs=true`).
- `schedule_job=true` to immediately schedule the created job(s).
- `split_jobs=true` to create one job per serviceOrderItem.

Examples:

```bash
curl -X POST 'http://localhost:8082/ingest/osm?dry_run=false&create_job=true&schedule_job=true&split_jobs=true' \
	-H 'X-API-Key: change-me-please' -H 'Content-Type: application/json' \
	-d '{"externalId":"ORD-1","description":"Fiber install","serviceOrderItem":[{"id":"ITEM-1"},{"id":"ITEM-2"}]}'
```

When running against real services, set:

- `RULES_API_STUB=false`
- `SCHEDULER_API_STUB=false`
- Provide either `RULES_API_TOKEN` / `SCHEDULER_API_TOKEN` OR set `RULES_JWT_SECRET` to the same as `wfmServices`' `JWT_SECRET_KEY` (intServices will mint JWTs).

## Testing

### Run All Tests
```bash
pytest
```

### Test OSM XML Functionality
```bash
# Test XML mapper components
pytest tests/test_osm_xml_mapper.py -v

# Test XML endpoints
curl -X GET 'http://localhost:8082/osm/xml/health' \
  -H 'X-API-Key: change-me-please'
```

### XML Test Files
Sample XML files for testing are available in:
- `documentation/xmls/OSM_CreateFiberService_Request_Payload.xml`
- `documentation/xmls/OSM_FiberServiceFeasibility_Request_Payload.xml`

### Integration Test Example
```bash
# Test complete XML-to-rules pipeline
curl -X POST 'http://localhost:8082/osm/xml/process' \
  -H 'X-API-Key: change-me-please' \
  -H 'Content-Type: application/xml' \
  --data-binary '@documentation/xmls/OSM_CreateFiberService_Request_Payload.xml'
```
