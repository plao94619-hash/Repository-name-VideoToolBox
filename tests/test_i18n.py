import ast
import string
import tempfile
import unittest
from pathlib import Path

from engine import (
    ConversionOptions, MediaInfo, MODE_EXTRACT, RAW_AUDIO,
    make_output_path,
)
from i18n import (
    EN_US, ZH_TW, LANGUAGE_LABELS, SUPPORTED_LANGUAGES,
    language_for_system_locale, translate,
)
from version import APP_VERSION


class TranslationTests(unittest.TestCase):
    def test_catalogs_cover_same_messages_and_placeholders(self):
        self.assertEqual(set(EN_US), set(ZH_TW))
        formatter = string.Formatter()
        for key in EN_US:
            original_fields = {
                field for _text, field, _spec, _conversion
                in formatter.parse(key) if field is not None
            }
            for catalog in (EN_US, ZH_TW):
                translated_fields = {
                    field for _text, field, _spec, _conversion
                    in formatter.parse(catalog[key]) if field is not None
                }
                self.assertEqual(original_fields, translated_fields, key)

    def test_all_literal_translations_have_catalog_entries(self):
        root = Path(__file__).resolve().parents[1] / "src"
        used = set()
        for path in (
            root / "main.py", root / "engine.py", root / "music_unlock.py",
            root / "direct_download.py", root / "clarity_enhance.py",
        ):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                func = node.func
                name = func.id if isinstance(func, ast.Name) else (
                    func.attr if isinstance(func, ast.Attribute) else ""
                )
                if name in {"_t", "translate"} and isinstance(node.args[0], ast.Constant):
                    key = node.args[0].value
                    if isinstance(key, str):
                        used.add(key)
        self.assertFalse(used - set(EN_US), f"Untranslated source messages: {used - set(EN_US)}")

    def test_supported_languages_and_safe_fallback(self):
        self.assertEqual(set(SUPPORTED_LANGUAGES), set(LANGUAGE_LABELS))
        self.assertEqual(translate("开始处理", "en_US"), "Start")
        self.assertEqual(translate("开始处理", "zh_TW"), "開始處理")
        self.assertEqual(translate("开始处理", "xx_XX"), "开始处理")
        self.assertEqual(language_for_system_locale("zh_HK"), "zh_TW")
        self.assertEqual(language_for_system_locale("zh-Hant-TW"), "zh_TW")
        self.assertEqual(language_for_system_locale("zh-Hans-CN"), "zh_CN")
        self.assertEqual(language_for_system_locale("en_SG"), "en_US")
        self.assertEqual(language_for_system_locale("zh_CN"), "zh_CN")

    def test_locale_does_not_change_engine_option_identifiers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for language in SUPPORTED_LANGUAGES:
                options = ConversionOptions(
                    mode=MODE_EXTRACT, target=RAW_AUDIO, quality="均衡压缩",
                    encoder="自动选择", resolution="保持原分辨率",
                    output_dir=root, locale=language,
                )
                output = make_output_path(
                    root / "media.mkv", options,
                    MediaInfo(duration=1, audio_codec="aac"),
                )
                self.assertEqual(output.name, "media_audio.m4a")

    def test_version_and_installer_languages_match_release(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/build-windows.yml").read_text(
            encoding="utf-8"
        )
        installer = (root / "installer/videotoolbox.iss").read_text(
            encoding="utf-8"
        )
        metadata = (root / "packaging/version_info.txt").read_text(encoding="utf-8")
        self.assertIn(f'APP_VERSION: "{APP_VERSION}"', workflow)
        self.assertIn(f'#define MyAppVersion "{APP_VERSION}"', installer)
        self.assertIn(f"StringStruct('ProductVersion', '{APP_VERSION}')", metadata)
        version_tuple = ", ".join((*APP_VERSION.split("."), "0"))
        self.assertIn(f"filevers=({version_tuple})", metadata)
        self.assertIn(f"prodvers=({version_tuple})", metadata)
        for name in ("english", "chinese", "traditional"):
            self.assertIn(f'Name: "{name}"', installer)
        for name in ("ChineseSimplified.isl", "ChineseTraditional.isl"):
            self.assertTrue((root / "installer/languages" / name).is_file())
