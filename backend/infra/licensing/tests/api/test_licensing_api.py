from infra.licensing.api.router import router


def test_licensing_router_is_mounted_at_expected_prefix():
    # The licensing module is a placeholder. This smoke test verifies the
    # router exists with the expected prefix; replace with real endpoint
    # tests once routes are added.
    assert router.prefix == "/api/v1/licensing"
    assert "licensing" in router.tags
    assert router.routes == []
