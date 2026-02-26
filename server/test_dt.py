from datetime import datetime, timedelta, timezone

def test_dashboard():
    from datetime import datetime
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        print("Success:", now)
    except Exception as e:
        import traceback
        traceback.print_exc()

test_dashboard()
