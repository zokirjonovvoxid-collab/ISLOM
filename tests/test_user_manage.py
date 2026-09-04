import unittest

from handlers.admin.panel import format_user_reference, normalize_user_identifier
from keyboards.inline.subscribe import build_subscribe_url
from services.subscription import (
    _is_supported_subscription_target,
    get_default_mandatory_channel_refs,
    normalize_channel_reference,
)


class UserManageHelpersTests(unittest.TestCase):
    def test_normalize_user_identifier_strips_prefix_and_spaces(self) -> None:
        self.assertEqual(normalize_user_identifier(" @demo_user "), "demo_user")
        self.assertEqual(normalize_user_identifier(" 12345 "), "12345")

    def test_format_user_reference_contains_id_username_and_nickname(self) -> None:
        user = {"user_id": 42, "username": "demo", "full_name": "Demo User"}
        text = format_user_reference(user)
        self.assertIn("42", text)
        self.assertIn("demo", text)
        self.assertIn("Demo User", text)

    def test_normalize_channel_reference_handles_t_me_links(self) -> None:
        self.assertEqual(normalize_channel_reference("https://t.me/filmkanal"), "@filmkanal")
        self.assertEqual(normalize_channel_reference("t.me/filmkanal"), "@filmkanal")
        self.assertEqual(normalize_channel_reference("https://telegram.me/filmkanal"), "@filmkanal")
        self.assertEqual(normalize_channel_reference("https://t.me/joinchat/abc123"), "joinchat/abc123")

    def test_supported_targets_accepts_telegram_usernames_and_ids(self) -> None:
        self.assertTrue(_is_supported_subscription_target("@filmkanal"))
        self.assertTrue(_is_supported_subscription_target("-1001234567890"))
        self.assertTrue(_is_supported_subscription_target("12345"))
        self.assertTrue(_is_supported_subscription_target("https://t.me/filmkanal"))
        self.assertTrue(_is_supported_subscription_target("https://youtube.com/@demo"))
        self.assertFalse(_is_supported_subscription_target("joinchat/abc123"))

    def test_build_subscribe_url_uses_original_link_for_external_urls(self) -> None:
        self.assertEqual(build_subscribe_url("https://youtube.com/@demo"), "https://youtube.com/@demo")
        self.assertEqual(build_subscribe_url("@filmkanal"), "https://t.me/filmkanal")

    def test_default_mandatory_channels_include_requested_targets(self) -> None:
        refs = get_default_mandatory_channel_refs()
        self.assertIn("@uzbmediakino", refs)
        self.assertIn("https://t.me/kinoman_000", refs)


if __name__ == "__main__":
    unittest.main()
