from backend.business.cldflow.models import CLDFlowRunContext, CLDNode, SharedCLD


def test_cld_node_strips_name():
    node = CLDNode(name="  target  ")
    assert node.name == "target"


def test_run_context_budget_remaining():
    context = CLDFlowRunContext(question="why test first?", budget_turns=3, current_turn=1)
    assert context.budget_remaining == 2


def test_shared_cld_defaults():
    cld = SharedCLD()
    assert cld.nodes == []
    assert cld.edges == []
