from src.api import CloseApi


class DummySender:
    def __init__(self):
        self.last_message = None

    def send_danmaku(self, message):
        self.last_message = message
        return {"ok": True, "message": message}


class DummyRoomCtx:
    def __init__(self, sender):
        self.sender = sender


class DummyRoomManager:
    def __init__(self):
        self._rooms = {"123": DummyRoomCtx(DummySender())}


class DummyAppCtx:
    fixed_room_id = None
    sender = None

    def reload_config(self):
        return False


def test_senddanmu_uses_selected_room_sender_when_room_id_is_given():
    room_manager = DummyRoomManager()
    ctx = DummyAppCtx()
    api = CloseApi(ctx, room_manager)

    result = api.sendDanmu("hello", room_id="123")

    assert result["ok"] is True
    assert (
        getattr(room_manager._rooms["123"].sender.last_message, "text", None) == "hello"
    )
