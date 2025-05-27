import pytest
from unittest.mock import Mock, AsyncMock
from damien_cli.features.ai_intelligence.natural_language.rule_parser import NaturalLanguageRuleParser
from damien_cli.features.ai_intelligence.models import ParsedRuleIntent

@pytest.fixture
def mock_llm_provider():
    provider = Mock()
    provider.complete = AsyncMock()
    provider.embed = AsyncMock()
    provider.count_tokens = Mock(return_value=100)
    return provider

@pytest.mark.asyncio
async def test_parse_simple_archive_rule(mock_llm_provider):
    """Test parsing a simple archive rule"""
    
    # Mock LLM response
    mock_llm_provider.complete.return_value = '''
    {
        "action": "archive",
        "conditions": [
            {"field": "from", "operator": "contains", "value": "newsletter"}
        ],
        "parameters": {},
        "confidence": 0.9,
        "reasoning": "User wants to archive emails from newsletters"
    }
    '''
    
    parser = NaturalLanguageRuleParser(mock_llm_provider)
    rule, intent = await parser.parse_instruction("Archive emails from newsletters")
    
    assert rule.name
    assert len(rule.conditions) == 1
    assert rule.conditions[0].field == "from"
    assert rule.conditions[0].operator == "contains"
    assert rule.conditions[0].value == "newsletter"
    assert rule.actions[0].type == "archive"
    assert intent.confidence == 0.9

@pytest.mark.asyncio
async def test_parse_complex_rule_with_age(mock_llm_provider):
    """Test parsing rule with multiple conditions"""
    
    mock_llm_provider.complete.return_value = '''
    {
        "action": "trash",
        "conditions": [
            {"field": "label", "operator": "equals", "value": "SPAM"},
            {"field": "age_days", "operator": "greater_than", "value": "30"}
        ],
        "parameters": {},
        "confidence": 0.85
    }
    '''
    
    parser = NaturalLanguageRuleParser(mock_llm_provider)
    rule, intent = await parser.parse_instruction("Delete spam emails older than 30 days")
    
    assert len(rule.conditions) == 2
    assert rule.actions[0].type == "trash"
    assert any(c.field == "age_days" for c in rule.conditions)

def test_fallback_parser():
    """Test fallback parser when LLM fails"""
    
    parser = NaturalLanguageRuleParser(Mock())
    intent = parser._fallback_parse("Archive emails from john@example.com older than 7 days")
    
    assert intent.action == "archive"
    assert len(intent.conditions) >= 1
    assert any(c["field"] == "from" for c in intent.conditions)
    assert intent.confidence < 1.0  # Lower confidence for fallback