from backend.business.cldflow.service import CLDFlowService
from backend.business.cldflow.models import CLDFlowFailureReport, CLDFlowReport


def test_cldflow_service_returns_report():
    service = CLDFlowService()
    result = service.run("为什么先做测试先行的 CLDFlow MVP？")
    assert isinstance(result, CLDFlowReport)
    assert result.shared_cld.nodes
    assert result.synthesized_insights


def test_cldflow_service_rejects_empty_question():
    service = CLDFlowService()
    result = service.run("   ")
    assert isinstance(result, CLDFlowFailureReport)
    assert "empty" in result.reason.lower()
