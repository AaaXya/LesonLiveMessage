from src.danmu_parser import parse_gift


def test_multi_gift_uses_total_price_when_total_coin_missing():
    payload = {
        "data": {
            "data": {
                "giftName": "辣条",
                "price": 1000,
                "num": 10,
                "total_coin": 0,
                "combo_total_coin": 0,
                "original_gift_price": 1000,
                "uname": "测试用户",
                "uid": 123,
            }
        }
    }

    result = parse_gift(payload)

    assert result is not None
    assert result["gift_num"] == 10
    assert result["total_coin"] == 10000
    assert result["paid_coin"] == 10000
