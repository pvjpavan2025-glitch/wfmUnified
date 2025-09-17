"""
End-to-End Test using REST APIs for WFM Order Flow:
Order Data → Rules Engine → Process Selection → BPMN Execution
"""

import os
import sys
import json
import logging
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service URLs (matching docker-compose configuration)
RULES_SERVICE_URL = "http://localhost:8003"  # Rules Service
PROCESS_SERVICE_URL = "http://localhost:8010"  # Process Service

# Test data
test_order_data = {
    "id": f"order-{str(uuid.uuid4())[:8]}",
    "externalId": f"ext-{str(uuid.uuid4())[:8]}",
    "priority": 5,
    "state": "acknowledged",
    "customerID": f"cust-{str(uuid.uuid4())[:8]}",
    "description": "Fiber service installation test",
    "requestedCompletionDate": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    "orderType": "FiberInstallation",
    "serviceType": "fiber",
    "category": "FiberInstallation",  # Ensure this matches the rule's category
    "tenant_id": "test-tenant",  # Explicitly set tenant_id
    "serviceOrderItems": [
        {
            "id": f"item-{str(uuid.uuid4())[:8]}",
            "action": "add",
            "service": {
                "id": f"svc-{str(uuid.uuid4())[:8]}",
                "name": "Fiber Internet 1Gbps",
                "category": "internet"
            },
            "serviceSpecification": {
                "id": "fiber-internet-1gbps",
                "name": "Fiber Internet 1Gbps",
                "serviceType": "fiber"
            },
            "relatedPlace": [
                {
                    "id": "location-123",
                    "role": "serviceLocation",
                    "name": "Customer Location"
                }
            ]
        }
    ],
    "relatedParty": [
        {
            "id": "customer-123",
            "role": "customer",
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
    ],
    "note": [
        {
            "text": "Test order for end-to-end testing",
            "date": datetime.now(timezone.utc).isoformat()
        }
    ]
}

class OrderFlowTest:
    """End-to-end test for WFM order flow using REST APIs."""
    
    def __init__(self):
        self.client = None
        self.order_id = None
        self.process_instance_id = None
        self.test_run_id = f"test-{uuid.uuid4().hex[:8]}"
    
    def _create_mock_token(self, tenant_id: str = "test-tenant") -> str:
        """Create a mock JWT token for testing.
        
        In development mode, the Rules Service expects a token that starts with 
        "mock-jwt-token-for-development". We can append the tenant_id to the token
        to make it available in the get_current_user function.
        """
        return f"mock-jwt-token-for-development-{tenant_id}"
    
    async def log_rules_from_database(self) -> None:
        """Log rules from the database for debugging."""
        try:
            from pymongo import MongoClient
            
            # MongoDB connection details
            mongo_uri = "mongodb://wfmadmin:tsarolabs%4012345%23@localhost:27017/wfm?authSource=admin"
            db_name = "wfm"
            collection_name = "rules"
            
            # Connect to MongoDB
            client = MongoClient(mongo_uri)
            db = client[db_name]
            collection = db[collection_name]
            
            # Get all active rules for the test tenant
            query = {
                "tenant_id": "test-tenant",
                "status": "active"
            }
            
            rules = list(collection.find(query))
            
            logger.info("\n" + "=" * 80)
            logger.info("===== ACTIVE RULES IN DATABASE =====")
            logger.info(f"Found {len(rules)} active rules for tenant 'test-tenant'")
            
            for i, rule in enumerate(rules, 1):
                logger.info(f"\nRule {i}:")
                logger.info(f"  ID: {rule.get('_id')}")
                logger.info(f"  Name: {rule.get('name')}")
                logger.info(f"  Status: {rule.get('status')}")
                logger.info(f"  Category: {rule.get('category')}")
                logger.info(f"  Condition: {json.dumps(rule.get('condition', {}), indent=4)}")
                logger.info(f"  Actions: {json.dumps(rule.get('actions', []), indent=4)}")
                
            logger.info("=" * 80 + "\n")
            
            client.close()
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to log rules from database: {str(e)}")
    
    async def check_mongodb_connection(self) -> bool:
        """Check MongoDB connection and list available rules."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            from pymongo import MongoClient
            
            # MongoDB connection details
            mongo_uri = "mongodb://wfmadmin:tsarolabs%4012345%23@localhost:27017/wfm?authSource=admin"
            db_name = "wfm"
            collection_name = "rules"
            
            logger.info("\n" + "=" * 80)
            logger.info("===== CHECKING MONGODB CONNECTION =====")
            logger.info(f"[MONGODB] URI: {mongo_uri}")
            logger.info(f"[MONGODB] Database: {db_name}")
            logger.info(f"[MONGODB] Collection: {collection_name}")
            
            # First try with synchronous connection to get better error messages
            try:
                sync_client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=10000,        # 10 second connection timeout
                    socketTimeoutMS=30000,          # 30 second socket timeout
                    connect=False                   # Don't connect yet
                )
                
                # Force connection attempt
                sync_client.admin.command('ping')
                logger.info("[MONGODB] Synchronous connection successful")
                
                # Get database and collection info
                db = sync_client[db_name]
                collection = db[collection_name]
                
                # Get database stats
                db_stats = db.command('dbstats')
                logger.info(f"\n[MONGODB] Database stats: {db_stats}")
                
                # List all collections
                collections = db.list_collection_names()
                logger.info(f"\n[MONGODB] Available collections: {collections}")
                
                # Get the count of rules in the collection
                rule_count = collection.count_documents({})
                logger.info(f"\n[MONGODB] Found {rule_count} rules in collection '{collection_name}'")
                
                # Get a sample of rules for debugging
                if rule_count > 0:
                    sample_rules = list(collection.find().limit(3))
                    logger.info("\nSample rules:")
                    for i, rule in enumerate(sample_rules, 1):
                        logger.info(f"{i}. ID: {rule.get('_id')}, "
                                  f"Name: {rule.get('name')}, "
                                  f"Status: {rule.get('status')}, "
                                  f"Tenant: {rule.get('tenant_id', 'default')}")
                
                # Ensure we have at least one rule with a proper condition that will match our test order
                test_rule = {
                    "id": "fiber-installation-rule-001",
                    "name": "Fiber Installation Rule",
                    "description": "Rule for fiber installation orders",
                    "status": "active",
                    "tenant_id": "test-tenant",
                    "category": "FiberInstallation",
                    "condition": {
                        "all": [
                            {
                                "fact": "orderType",
                                "operator": "equals",
                                "value": "FiberInstallation"
                            },
                            {
                                "fact": "serviceType",
                                "operator": "equals",
                                "value": "fiber"
                            }
                        ]
                    },
                    "actions": [
                        {
                            "type": "select_process",
                            "params": {
                                "process_id": "fiber_installation_process"
                            }
                        }
                    ],
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z"
                }
                
                # Delete any existing test rule to avoid duplicates
                collection.delete_many({"id": "fiber-installation-rule-001", "tenant_id": "test-tenant"})
                
                # Insert the test rule
                try:
                    collection.insert_one(test_rule)
                    logger.info("\nInserted test fiber installation rule with proper condition")
                    logger.info(f"Rule ID: {test_rule['id']}")
                    logger.info(f"Condition: {json.dumps(test_rule['condition'], indent=2)}")
                    logger.info(f"Actions: {json.dumps(test_rule['actions'], indent=2)}")
                except Exception as e:
                    logger.warning(f"Could not insert test rule: {str(e)}")
                
                # Now try with async client
                try:
                    async_client = AsyncIOMotorClient(mongo_uri)
                    await async_client.admin.command('ping')
                    logger.info("\n[MONGODB] Asynchronous connection successful")
                    return True
                except Exception as e:
                    logger.error(f"[ERROR] Asynchronous MongoDB connection failed: {str(e)}")
                    return False
                
            except Exception as e:
                logger.error(f"[ERROR] Synchronous MongoDB connection failed: {str(e)}")
                
                # Try to get more detailed error information
                if hasattr(e, 'details') and 'errmsg' in e.details:
                    logger.error(f"[MONGODB] Error details: {e.details['errmsg']}")
                
                # Check if MongoDB is running
                try:
                    import subprocess
                    mongo_process = subprocess.run(['pgrep', 'mongod'], capture_output=True, text=True)
                    if mongo_process.returncode != 0:
                        logger.error("[MONGODB] MongoDB does not appear to be running. Please start MongoDB and try again.")
                    else:
                        logger.info("[MONGODB] MongoDB process is running but connection failed")
                except Exception:
                    logger.error("[MONGODB] Could not check if MongoDB is running")
                
                return False
            
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error during MongoDB connection check: {str(e)}", exc_info=True)
            return False
    
    async def evaluate_with_rules_engine(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate order data with rules engine with enhanced debugging."""
        url = f"{RULES_SERVICE_URL}/rules/evaluate"
        tenant_id = "test-tenant"
        mock_token = self._create_mock_token(tenant_id)
        
        # Ensure tenant_id is set in the order data
        order_data.setdefault("tenant_id", tenant_id)
        
        # Add debug information to the order data
        order_data["_debug"] = {
            "test_run_id": self.test_run_id,
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "e2e_test"
        }
        
        # Create headers with debug information
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mock_token}",
            "X-Tenant-ID": tenant_id,
            "X-Request-ID": f"test-{uuid.uuid4()}",
            "X-Test-Run-ID": self.test_run_id,
            "X-Debug-Mode": "true",
            "X-Request-Source": "e2e-test"
        }
        
        # Prepare the evaluation request with all parameters and debug info
        evaluation_request = {
            "data": order_data,
            "category": "FiberInstallation",
            "tenant_id": tenant_id,
            "orchestrate": True,
            "auto_schedule": True,
            "debug": True,  # Enable debug mode in rules service
            "metadata": {
                "test_run_id": self.test_run_id,
                "test_timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "e2e_test",
                "test_name": "test_osm_rest_flow_v2"
            },
            "evaluation_options": {
                "include_rule_details": True,
                "include_evaluation_steps": True,
                "include_matched_rules": True,
                "include_failed_conditions": True
            }
        }
        
        # Log the request with additional context
        logger.info("\n" + "=" * 80)
        logger.info("===== SENDING RULE EVALUATION REQUEST =====")
        logger.info(f"[REQUEST] URL: {url}")
        logger.info(f"[REQUEST] Method: POST")
        logger.info(f"[REQUEST] Tenant ID: {tenant_id}")
        logger.info(f"[REQUEST] Order ID: {order_data.get('id')}")
        logger.info(f"[REQUEST] Order Type: {order_data.get('orderType')}")
        logger.info(f"[REQUEST] Category: {evaluation_request.get('category')}")
        
        # Log headers with sensitive information redacted
        safe_headers = {
            k: '*****' if k.lower() in ['authorization', 'x-api-key'] else v 
            for k, v in headers.items()
        }
        logger.info("[REQUEST] Headers: " + json.dumps(safe_headers, indent=2))
        
        # Log the payload with sensitive information redacted
        def redact_sensitive(data, path=()):
            if isinstance(data, dict):
                return {
                    k: '*****' if any(s in k.lower() for s in ['pass', 'token', 'secret', 'key', 'auth']) 
                    else redact_sensitive(v, path + (k,))
                    for k, v in data.items()
                }
            elif isinstance(data, list):
                return [redact_sensitive(item, path) for item in data]
            else:
                return data
        
        logger.info("\n[REQUEST BODY]")
        logger.info(json.dumps(redact_sensitive(evaluation_request), indent=2, default=str))
        
        # Log the expected rule matching criteria
        logger.info("\n[EXPECTED RULE MATCHING CRITERIA]")
        logger.info("Rule should match when ALL of these conditions are true:")
        logger.info("1. orderType equals 'FiberInstallation'")
        logger.info("2. serviceType equals 'fiber'")
        logger.info("3. tenant_id equals 'test-tenant'")
        logger.info("4. status equals 'active'")
        logger.info("5. category equals 'FiberInstallation'")
        logger.info("=" * 80 + "\n")
        
        # Include tenant_id in query params as well for compatibility
        params = {
            "tenant_id": tenant_id,
            "debug": "true"
        }
        
        client = None
        try:
            logger.info(f"Sending to Rules Service: {url}?tenant_id={tenant_id}&debug=true")
            
            # First, get the rules that should match this request
            logger.info("\n[DEBUG] Fetching rules that should match this request...")
            rules_url = f"{RULES_SERVICE_URL}/rules"
            rules_params = {
                "tenant_id": tenant_id,
                "category": "FiberInstallation",
                "status": "active",
                "limit": 10
            }
            
            try:
                rules_client = httpx.AsyncClient()
                rules_response = await rules_client.get(
                    rules_url,
                    params=rules_params,
                    headers={
                        "Authorization": f"Bearer {mock_token}",
                        "X-Tenant-ID": tenant_id
                    },
                    timeout=10.0
                )
                
                if rules_response.status_code == 200:
                    rules_data = rules_response.json()
                    
                    # Handle both list and object responses
                    if isinstance(rules_data, list):
                        rules_list = rules_data
                        logger.info(f"[DEBUG] Found {len(rules_list)} active rules (list response format)")
                    elif isinstance(rules_data, dict) and 'items' in rules_data:
                        rules_list = rules_data.get('items', [])
                        logger.info(f"[DEBUG] Found {len(rules_list)} active rules (pagination response format)")
                    else:
                        rules_list = []
                        logger.warning(f"[DEBUG] Unexpected rules response format: {type(rules_data)}")
                    
                    # Filter rules for the current tenant and category
                    filtered_rules = [
                        rule for rule in rules_list 
                        if rule.get('tenant_id') == tenant_id 
                        and rule.get('category') == 'FiberInstallation'
                        and rule.get('status') == 'active'
                    ]
                    
                    logger.info(f"[DEBUG] Found {len(filtered_rules)} active rules for tenant '{tenant_id}' and category 'FiberInstallation':")
                    
                    if not filtered_rules:
                        logger.warning("[DEBUG] No active rules found for the specified criteria")
                        
                        # Log all rules for debugging
                        logger.info("\n[DEBUG] All available rules:")
                        for i, rule in enumerate(rules_list, 1):
                            logger.info(f"  {i}. ID: {rule.get('id')}, Name: {rule.get('name')}")
                            logger.info(f"     Tenant: {rule.get('tenant_id')}")
                            logger.info(f"     Category: {rule.get('category')}")
                            logger.info(f"     Status: {rule.get('status')}")
                            logger.info(f"     Condition: {json.dumps(rule.get('condition', {}), indent=6)}")
                    
                    for i, rule in enumerate(filtered_rules, 1):
                        logger.info(f"\n  {i}. ID: {rule.get('id')}")
                        logger.info(f"     Name: {rule.get('name')}")
                        logger.info(f"     Status: {rule.get('status')}")
                        logger.info(f"     Priority: {rule.get('priority')}")
                        logger.info(f"     Tenant: {rule.get('tenant_id')}")
                        logger.info(f"     Category: {rule.get('category')}")
                        logger.info(f"     Condition: {json.dumps(rule.get('condition', {}), indent=8)}")
                        logger.info(f"     Actions: {json.dumps(rule.get('actions', []), indent=8)}")
                else:
                    logger.warning(f"[DEBUG] Failed to fetch rules: {rules_response.status_code} - {rules_response.text}")
            except Exception as e:
                logger.warning(f"[DEBUG] Error fetching rules: {str(e)}")
            finally:
                if 'rules_client' in locals() and rules_client is not None:
                    await rules_client.aclose()
            
            # Now make the evaluation request
            logger.info("\n[DEBUG] Sending evaluation request...")
            client = httpx.AsyncClient(timeout=60.0)
            response = await client.post(
                url,
                params=params,
                json=evaluation_request,
                headers=headers,
                timeout=60.0
            )
            
            # Log the raw response for debugging
            logger.info("\n[DEBUG] Raw response:")
            logger.info(f"Status: {response.status_code}")
            logger.info("Headers:")
            for k, v in response.headers.items():
                logger.info(f"  {k}: {v}")
            
            try:
                result = response.json()
                logger.info("\n[DEBUG] Response JSON:")
                logger.info(json.dumps(result, indent=2))
            except Exception as e:
                logger.error(f"[DEBUG] Failed to parse JSON response: {str(e)}")
                logger.error(f"[DEBUG] Response text: {response.text[:1000]}")
                raise
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Log the evaluation result
            logger.info("\n" + "=" * 80)
            logger.info("===== RULES EVALUATION RESULT =====")
            logger.info(f"Status: {'SUCCESS' if result.get('success', False) else 'FAILED'}")
            logger.info(f"Message: {result.get('message', 'No message')}")
            logger.info(f"Matched Rules: {len(result.get('matched_rules', []))}")
            logger.info(f"Process ID: {result.get('process_id')}")
            
            # Log matched rules details
            if 'matched_rules' in result and result['matched_rules']:
                logger.info("\nMatched Rules Details:")
                for i, rule in enumerate(result['matched_rules'], 1):
                    logger.info(f"  {i}. ID: {rule.get('id')}, Name: {rule.get('name')}")
                    logger.info(f"     Condition: {json.dumps(rule.get('condition', {}), indent=4)}")
                    logger.info(f"     Actions: {json.dumps(rule.get('actions', []), indent=4)}")
            
            # Log executed actions
            if 'executed_actions' in result and result['executed_actions']:
                logger.info("\nExecuted Actions:")
                for i, action in enumerate(result['executed_actions'], 1):
                    logger.info(f"  {i}. {json.dumps(action, indent=2)}")
            
            # Log evaluation metrics if available
            if 'evaluation_metrics' in result:
                logger.info("\nEvaluation Metrics:")
                for k, v in result['evaluation_metrics'].items():
                    logger.info(f"  {k}: {v}")
            
            # Log the full result for debugging
            logger.info("\nFull Result:")
            logger.info(json.dumps(result, indent=2, default=str))
            logger.info("=" * 80 + "\n")
            
            # Check if we got a process_id
            if not result.get('process_id'):
                logger.error(f"No process_id returned from rules evaluation. Response keys: {list(result.keys())}")
                logger.error(f"Executed actions: {result.get('executed_actions', [])}")
                
                # Add detailed troubleshooting information
                logger.info("\n" + "!" * 80)
                logger.info("TROUBLESHOOTING INFORMATION:")
                logger.info(f"1. Order ID: {order_data.get('id')}")
                logger.info(f"2. Order Type: {order_data.get('orderType')}")
                logger.info(f"3. Category: {evaluation_request.get('category')}")
                logger.info(f"4. Tenant ID: {tenant_id}")
                logger.info(f"5. Test Run ID: {self.test_run_id}")
                logger.info("\nCHECK THE FOLLOWING:")
                logger.info("1. Verify that the Rules Service is running and accessible")
                logger.info("2. Check the Rules Service logs for any errors")
                logger.info("3. Ensure there are active rules for the category 'FiberInstallation'")
                logger.info("4. Verify that the rule conditions match the order data structure")
                logger.info("5. Check if the tenant_id is correctly set in the rules")
                logger.info("6. Verify that the rule status is 'active'")
                logger.info("7. Check if the rule actions include a 'select_process' action")
                logger.info("!" * 80 + "\n")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            if e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {dict(e.response.headers)}")
                try:
                    error_body = e.response.json()
                    logger.error(f"Response body (JSON): {json.dumps(error_body, indent=2)}")
                except:
                    logger.error(f"Response text: {e.response.text[:1000]}")
            raise
            
        except Exception as e:
            logger.error(f"Error evaluating rules: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
        finally:
            if client is not None and not client.is_closed:
                await client.aclose()
            
    async def start_process(self, process_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Start a BPMN process with the given ID and variables."""
        url = f"{PROCESS_SERVICE_URL}/process/start"
        payload = {
            "processId": process_id,
            "variables": variables
        }
        
        logger.info(f"Starting process {process_id}")
        
        client = None
        try:
            client = httpx.AsyncClient()
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Process Service error: {e.response.text}")
            raise Exception(f"Process Service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Error calling Process Service: {str(e)}")
            raise
        finally:
            if client:
                await client.aclose()
    
    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'client') and self.client is not None and not self.client.is_closed:
            await self.client.aclose()
            self.client = None
    
    async def get_or_create_test_rule(self) -> str:
        """Get an existing test rule or create a new one if it doesn't exist."""
        # First, try to find an existing test rule
        list_url = f"{RULES_SERVICE_URL}/rules"
        tenant_id = "test-tenant"
        
        # Use our mock token creation method
        mock_token = self._create_mock_token(tenant_id)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mock_token}"
        }
        
        client = None
        try:
            # Create a new client for this request
            client = httpx.AsyncClient()
            
            # Try to list all rules for our test tenant to find our test rule
            params = {
                "tenant_id": "test-tenant"
            }
            response = await client.get(
                list_url,
                params=params,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                rules = response.json()
                # Look for a test rule with a matching category
                for rule in rules:
                    if rule.get("category") == "FiberInstallation" and rule.get("name", "").startswith("Test Fiber Installation"):
                        logger.info(f"Found existing test rule: {rule['id']}")
                        return rule["id"]
            
            # If we get here, no existing test rule was found, so create a new one
            logger.info("No existing test rule found, creating a new one...")
            
            # Create a unique name for the test rule
            import time
            rule_name = f"Test Fiber Installation Rule - {int(time.time())}"
            
            # Create a simple rule that matches our test order data
            rule_data = {
                "name": rule_name,
                "description": "Test rule for fiber installation orders",
                "category": "FiberInstallation",
                "conditions": {
                    "orderType": {"eq": "FiberInstallation"}
                },
                "actions": [
                    {
                        "type": "select_process",
                        "params": {
                            "process_id": "fiber_installation_process"
                        }
                    }
                ],
                "priority": 5,
                "status": "active",
                "tenant_id": "test-tenant"
            }
            
            # Create the new rule
            create_url = f"{RULES_SERVICE_URL}/rules"
            
            # Ensure tenant_id is in the request body
            rule_data["tenant_id"] = "test-tenant"
                
            response = await client.post(
                create_url,
                json=rule_data,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Created new test rule: {result.get('id')}")
            
            # Return the rule ID for cleanup
            return result.get("id")
                
        except httpx.HTTPStatusError as e:
            error_detail = f"{e.response.status_code} - {e.response.text}"
            logger.error(f"Error managing test rule: {error_detail}")
            raise Exception(f"Error managing test rule: {error_detail}")
        except Exception as e:
            logger.error(f"Error managing test rule: {str(e)}")
            raise
    
    async def delete_test_rule(self, rule_id: str) -> None:
        """Delete a test rule."""
        if not rule_id:
            return
            
        url = f"{RULES_SERVICE_URL}/rules/{rule_id}"
        logger.info(f"Deleting test rule at: {url}")
        
        # For testing, we'll use a mock token that will be accepted
        mock_token = "mock-jwt-token-for-development"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mock_token}"
        }
        
        client = None
        try:
            client = httpx.AsyncClient()
            response = await client.delete(
                url,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"Test rule {rule_id} deleted")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:  # Not found is okay
                error_detail = f"{e.response.status_code} - {e.response.text}"
                logger.error(f"Error deleting test rule: {error_detail}")
        except Exception as e:
            logger.error(f"Error deleting test rule: {str(e)}")
        finally:
            if client:
                await client.aclose()
    
    async def run_test(self):
        """Run the complete order flow test."""
        try:
            logger.info("\n" + "=" * 80)
            logger.info("===== STARTING WFM ORDER FLOW TEST =====")
            logger.info(f"Test Run ID: {self.test_run_id}")
            logger.info(f"Start Time: {datetime.now(timezone.utc).isoformat()}")
            logger.info("=" * 80 + "\n")
            
            # Check MongoDB connection and list rules
            logger.info("Checking MongoDB connection and rules...")
            db_ok = await self.check_mongodb_connection()
            if not db_ok:
                logger.error("MongoDB connection check failed. Please check the MongoDB service and try again.")
                return {
                    "success": False,
                    "error": "MongoDB connection check failed"
                }
            
            # Step 1: Log rules from database for debugging
            await self.log_rules_from_database()
            
            # Step 2: Evaluate order with rules engine
            logger.info("\n" + "=" * 80)
            logger.info("===== STEP 1: EVALUATING ORDER WITH RULES ENGINE =====")
            logger.info("=" * 80 + "\n")
            
            rules_response = await self.evaluate_with_rules_engine(test_order_data)
            
            # Log the full result for debugging
            logger.info("\n" + "=" * 80)
            logger.info("===== RULES EVALUATION RESULT =====")
            logger.info(f"Status: {'SUCCESS' if rules_response.get('success', False) else 'FAILED'}")
            logger.info(f"Message: {rules_response.get('message', 'No message')}")
            logger.info(f"Matched Rules: {len(rules_response.get('matches', []))}")
            logger.info(f"Process ID: {rules_response.get('process_id', 'None')}")
            logger.info("\nFull Result:")
            logger.info(json.dumps(rules_response, indent=2))
            logger.info("=" * 80 + "\n")
            
            # Check if we got a process_id from the rules engine
            process_id = rules_response.get('process_id')
            if not process_id:
                # Try to find process_id in executed_actions if not in the root
                if 'executed_actions' in rules_response:
                    for action in rules_response['executed_actions']:
                        if isinstance(action, dict) and 'params' in action and 'process_id' in action['params']:
                            process_id = action['params']['process_id']
                            logger.info(f"Found process_id in executed_actions: {process_id}")
                            break
            
            if not process_id:
                error_msg = "No process_id returned from rules evaluation"
                logger.error(f"{error_msg}. Response keys: {list(rules_response.keys())}")
                if 'executed_actions' in rules_response:
                    logger.error(f"Executed actions: {json.dumps(rules_response['executed_actions'], indent=2)}")
                
                # Additional debugging information
                logger.info("\n" + "!" * 80)
                logger.info("TROUBLESHOOTING TIPS:")
                logger.info("1. Check if the MongoDB has the expected rules for the test tenant")
                logger.info("2. Verify that the rule conditions match the test order data")
                logger.info("3. Check the Rules Service logs for any errors")
                logger.info("4. Ensure the tenant_id is correctly set in both the request and the rules")
                logger.info("5. Verify that the rule status is 'active'")
                logger.info("!" * 80 + "\n")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "rules_response": rules_response
                }
            
            # Step 2: Start BPMN process
            logger.info("\n" + "=" * 80)
            logger.info("===== STEP 2: STARTING BPMN PROCESS =====")
            logger.info(f"Process ID: {process_id}")
            logger.info("=" * 80 + "\n")
            
            process_instance = await self.start_process(process_id, test_order_data)
            
            logger.info("\n" + "=" * 80)
            logger.info("===== PROCESS INSTANCE CREATED =====")
            logger.info(f"Process Instance ID: {process_instance.get('id')}")
            logger.info("=" * 80 + "\n")
            
            return {
                "success": True,
                "process_instance_id": process_instance.get('id'),
                "process_data": process_instance,
                "rules_evaluation": rules_response
            }
            
        except Exception as e:
            logger.error("\n" + "!" * 80)
            logger.error(f"TEST FAILED: {str(e)}")
            logger.error("!" * 80 + "\n", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Log test completion
            logger.info("\n" + "=" * 80)
            logger.info(f"TEST COMPLETED: {datetime.now(timezone.utc).isoformat()}")
            logger.info("=" * 80 + "\n")
            
            # Clean up resources


async def main():
    """Run the end-to-end test."""
    test = None
    try:
        logger.info("\n" + "=" * 80)
        logger.info("===== WFM ORDER FLOW TEST - STARTING =====")
        logger.info("=" * 80 + "\n")
        
        test = OrderFlowTest()
        result = await test.run_test()
        
        logger.info("\n" + "=" * 80)
        if result and result.get('success'):
            logger.info("✅ TEST PASSED")
            logger.info(f"Process Instance ID: {result.get('process_instance_id')}")
            
            # Log the full result for reference
            logger.info("\nTest Result:")
            logger.info(json.dumps({
                "success": True,
                "process_instance_id": result.get('process_instance_id'),
                "test_run_id": test.test_run_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, indent=2))
            
            return 0  # Success exit code
        else:
            logger.error("❌ TEST FAILED")
            if 'error' in result:
                logger.error(f"Error: {result['error']}")
            
            # Log the full error details for debugging
            logger.error("\nFailure Details:")
            logger.error(json.dumps({
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "test_run_id": test.test_run_id if test else 'unknown',
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": result if isinstance(result, dict) else str(result)
            }, indent=2))
            
            return 1  # Error exit code
            
    except Exception as e:
        logger.error("\n" + "!" * 80)
        logger.error("❌ UNEXPECTED ERROR IN TEST")
        logger.error(f"Error: {str(e)}")
        logger.error("!" * 80 + "\n", exc_info=True)
        return 2  # Critical error exit code
        
    finally:
        if test:
            await test.cleanup()
            
        logger.info("\n" + "=" * 80)
        logger.info("===== WFM ORDER FLOW TEST COMPLETED =====")
        logger.info("=" * 80 + "\n")

if __name__ == "__main__":
    import sys
    from datetime import timedelta  # Moved here to avoid circular import
    
    try:
        # Run the main test and get the exit code
        exit_code = asyncio.run(main())
        
        # Exit with the appropriate status code
        sys.exit(exit_code if isinstance(exit_code, int) else 0)
        
    except KeyboardInterrupt:
        logger.error("\nTest interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(f"\nUnhandled exception in test runner: {str(e)}", exc_info=True)
        sys.exit(2)  # General error exit code
