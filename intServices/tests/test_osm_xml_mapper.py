"""
Test cases for OSM XML mapper functionality.
"""
import pytest
from app.mappers.xml_parser import OSMXMLMapper, XMLParseError
from app.mappers.osm_xml import OSMXMLToRulesMapper


class TestOSMXMLMapper:
    """Test cases for OSM XML to JSON conversion."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = OSMXMLMapper()
        self.rules_mapper = OSMXMLToRulesMapper()
    
    def test_installation_request_conversion(self):
        """Test conversion of ServiceOrderInstallationRequest XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderInstallationRequest>
    <id>ORD-001</id>
    <externalId>EXT-001</externalId>
    <priority>5</priority>
    <category>FiberInstallation</category>
    <orderDate>2024-11-09T10:00:00Z</orderDate>
    <description>Fiber installation request</description>
    <relatedParty>
        <item>
            <id>CUST-001</id>
            <role>Customer</role>
            <name>John Doe</name>
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
            </service>
        </item>
    </serviceOrderItem>
</ServiceOrderInstallationRequest>"""
        
        result = self.mapper.xml_to_json(xml_content)
        
        assert result is not None
        assert result.get('id') == 'ORD-001'
        assert result.get('externalId') == 'EXT-001'
        assert result.get('priority') == 5
        assert result.get('category') == 'FiberInstallation'
        assert 'relatedParty' in result
        assert 'serviceOrderItem' in result
    
    def test_feasibility_request_conversion(self):
        """Test conversion of ServiceOrderFeasibilityRequest XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderFeasibilityRequest>
    <id>ORD-002</id>
    <category>FiberFeasibility</category>
    <orderDate>2024-11-09T11:00:00Z</orderDate>
    <description>Fiber feasibility check</description>
</ServiceOrderFeasibilityRequest>"""
        
        result = self.mapper.xml_to_json(xml_content)
        
        assert result is not None
        assert result.get('id') == 'ORD-002'
        assert result.get('category') == 'FiberFeasibility'
    
    def test_rules_mapper_with_xml(self):
        """Test complete XML to rules engine conversion."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderInstallationRequest>
    <id>ORD-003</id>
    <category>FiberInstallation</category>
    <orderDate>2024-11-09T12:00:00Z</orderDate>
    <serviceOrderItem>
        <item>
            <id>ITEM-001</id>
            <action>add</action>
            <service>
                <id>SVC-001</id>
                <category>Broadband</category>
            </service>
        </item>
    </serviceOrderItem>
</ServiceOrderInstallationRequest>"""
        
        result = self.rules_mapper.to_rules(xml_content)
        
        assert result is not None
        assert 'externalId' in result
        assert 'serviceOrderItems' in result
        assert isinstance(result['serviceOrderItems'], list)
    
    def test_invalid_xml_handling(self):
        """Test handling of invalid XML content."""
        invalid_xml = "<invalid>unclosed tag"
        
        with pytest.raises(XMLParseError):
            self.mapper.xml_to_json(invalid_xml)
    
    def test_empty_xml_handling(self):
        """Test handling of empty XML content."""
        empty_xml = ""
        
        with pytest.raises(XMLParseError):
            self.mapper.xml_to_json(empty_xml)
    
    def test_xml_validation(self):
        """Test XML structure validation."""
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ServiceOrderInstallationRequest>
    <category>FiberInstallation</category>
    <orderDate>2024-11-09T12:00:00Z</orderDate>
</ServiceOrderInstallationRequest>"""
        
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<SomeOtherRequest>
    <randomField>value</randomField>
</SomeOtherRequest>"""
        
        assert self.rules_mapper.validate_xml_structure(valid_xml) == True
        assert self.rules_mapper.validate_xml_structure(invalid_xml) == False


if __name__ == "__main__":
    pytest.main([__file__])
