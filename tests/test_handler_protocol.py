from app.agents.handlers import SegmentHandler, HANDLER_REGISTRY, register_handler


def test_registry_is_dict():
    assert isinstance(HANDLER_REGISTRY, dict)


def test_register_adds_handler():
    class Fake:
        name = "fake"
        async def step(self, state, db, redis, user_input): return {}
        async def initial_message(self, state): return None
    register_handler(Fake())
    assert "fake" in HANDLER_REGISTRY
    del HANDLER_REGISTRY["fake"]
