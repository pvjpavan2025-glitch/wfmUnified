#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/Users/pavan.pvj/code/wfmUnified/intServices')

from app.mappers.xml_parser import XMLToJSONParser, OSMXMLMapper

# Load the test XML
xml_file = '/Users/pavan.pvj/code/wfmUnified/documentation/xmls-v1/OSM_CreateFiberService_Request_Payload.xml'
with open(xml_file, 'r') as f:
    xml_content = f.read()

print("=== XML Content ===")
print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)

print("\n=== Testing XMLToJSONParser ===")
try:
    parser = XMLToJSONParser()
    json_data = parser.parse_xml_to_json(xml_content)
    print("JSON Data:", json_data)
    print("Type:", type(json_data))
    print("Keys:", list(json_data.keys()) if isinstance(json_data, dict) else "Not a dict")
except Exception as e:
    print("Error in XMLToJSONParser:", str(e))
    import traceback
    traceback.print_exc()

print("\n=== Testing OSMXMLMapper ===")
try:
    mapper = OSMXMLMapper()
    
    # Debug the root key detection
    parsed_data = mapper.parser.parse_xml_to_json(xml_content)
    print("Parsed data keys:", list(parsed_data.keys()))
    root_key = next(iter(parsed_data.keys()))
    print("Root key:", root_key)
    print("Root value type:", type(parsed_data[root_key]))
    print("Root value:", parsed_data[root_key])
    
    result = mapper.xml_to_json(xml_content)
    print("Result:", result)
except Exception as e:
    print("Error in OSMXMLMapper:", str(e))
    import traceback
    traceback.print_exc()
