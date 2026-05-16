from backend.core.cldflow import CLDFlowAppService


def test_cldflow_mvp_happy_path() -> None:
    service = CLDFlowAppService()
    parsed = service.parse_query("How does policy shape system outcomes?")
    run_context = service.create_run_context()
    shared_cld = service.build_shared_cld(parsed)
    weighted_fcm = service.build_weighted_fcm(shared_cld)
    leverage = service.build_leverage_analysis(shared_cld)
    report = service.synthesize_report(run_context, shared_cld, weighted_fcm, leverage)

    assert parsed.query_text
    assert shared_cld.nodes
    assert weighted_fcm.weight_matrix
    assert leverage.leverage_points
    assert report.evidence_tracing["run_id"] == run_context.run_id


def test_cldflow_empty_question_rejected() -> None:
    service = CLDFlowAppService()

    try:
        service.parse_query("   ")
    except ValueError as exc:
        assert "不能为空" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
