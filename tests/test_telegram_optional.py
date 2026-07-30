from app.models.job import Job
from app.notifications.telegram import TelegramNotifier


def test_unconfigured_telegram_is_a_noop():
    notifier = TelegramNotifier("", "")
    notifier.send(Job("linkedin", "1", "Engineer", "Acme", "Remote", "https://example.com"))
    assert not notifier.enabled

