"""Theme invariants independent of a local Zen installation."""
import json
import re
import unittest

from chezmoi_testlib import Fixture


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


class ZenThemeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        self.data = json.loads(self.fixture.chezmoi(
            "execute-template", input="{{ .zen | toJson }}").stdout)

    def test_snow_text_meets_aa_on_all_three_surfaces(self):
        palette = self.data["palette"]
        for foreground in ("nord4", "nord5", "nord6"):
            for background in ("nord1", "nord2", "nord3"):
                ratio = ((luminance(palette[foreground]) + 0.05) /
                         (luminance(palette[background]) + 0.05))
                self.assertGreaterEqual(ratio, 4.5, (foreground, background, ratio))

    def test_distinct_aurora_accents_in_both_rendered_stylesheets(self):
        accents = set()
        for profile, config in self.data["profiles"].items():
            for file in ("userChrome.css", "userContent.css"):
                css = self.fixture.render(f"dot_zen/{profile}/chrome/{file}.tmpl")
                names = set(re.findall(r"--nord-profile-accent:\s*var\(--(nord\d+)\)", css))
                self.assertEqual(names, {config["accent"]})
                self.assertIn('color-scheme: dark !important', css)
                self.assertNotIn("light-dark(", css)
                accents.update(names)
        self.assertEqual(len(accents), 3)
        self.assertTrue(accents <= {"nord11", "nord12", "nord13", "nord14", "nord15"})

    def test_persistent_dark_inputs_are_shared(self):
        rendered = [self.fixture.render(f"dot_zen/{profile}/user.js.tmpl")
                    for profile in self.data["profiles"]]
        self.assertEqual(len(set(rendered)), 1)
        preferences = {
            json.loads(key): json.loads(value)
            for key, value in re.findall(r"user_pref\((\"[^\"]+\"),\s*([^)]+)\);", rendered[0])
        }
        self.assertTrue(preferences["toolkit.legacyUserProfileCustomizations.stylesheets"])
        self.assertEqual(preferences["zen.view.window.scheme"], 0)
        self.assertEqual(preferences["ui.systemUsesDarkTheme"], 1)
        self.assertEqual(preferences["layout.css.prefers-color-scheme.content-override"], 0)
        self.assertEqual(preferences["browser.display.background_color.dark"],
                         self.data["palette"]["nord1"])


if __name__ == "__main__":
    unittest.main()
