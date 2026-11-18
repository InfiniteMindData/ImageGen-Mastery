import json
from pathlib import Path
import unittest

from imagegen_mastery.prompt import optimize


class PromptTests(unittest.TestCase):
    def test_minimal_brief_preserves_the_entire_request(self):
        intent = 'A two-line sign reading exactly “Open\n late”, in pencil.'
        self.assertEqual(optimize({"intent": intent}), intent)

    def test_object_key_order_does_not_change_the_prompt(self):
        brief = {
            "intent": "A heron on thin ice.",
            "style": "Blue ink.",
            "composition": "Square crop.",
            "lighting": "Diffuse dawn.",
            "constraints": ["One bird.", "Keep both feet visible."],
            "avoid": ["Lettering."],
        }
        rendered = optimize(brief)
        for phrase in (
            "A heron on thin ice.", "Blue ink.", "Square crop.", "Diffuse dawn.",
            "One bird.", "Keep both feet visible.", "Lettering.",
        ):
            self.assertIn(phrase, rendered)
        self.assertLess(rendered.index("One bird."), rendered.index("Keep both feet visible."))
        self.assertEqual(rendered, optimize(dict(reversed(brief.items()))))

    def test_reference_descriptions_keep_each_subjects_anchors_together(self):
        rendered = optimize({
            "intent": "Two friends in the garden.",
            "references": [
                {"image": "Mina portrait", "anchors": [
                    {"aspect": "Mina's coat", "detail": "Red wool."},
                    {"aspect": "Mina's hair", "detail": "Black bob."},
                ]},
                {"image": "Bo portrait", "anchors": [
                    {"aspect": "Bo's coat", "detail": "Green linen."},
                ]},
            ],
        })
        mina = rendered.index("Mina portrait")
        bo = rendered.index("Bo portrait")
        self.assertIn("Mina's coat", rendered[mina:bo])
        self.assertIn("Red wool.", rendered[mina:bo])
        self.assertIn("Black bob.", rendered[mina:bo])
        self.assertIn("Bo's coat", rendered[bo:])
        self.assertIn("Green linen.", rendered[bo:])

    def test_revision_pairs_observed_defect_with_requested_change(self):
        brief = {"intent": "Bird study.", "constraints": ["Two birds."]}
        base = optimize(brief)
        brief["revisions"] = [
            {"observed": "Left wing cropped.", "change": "Widen the frame."},
            {"observed": "Background too dark.", "change": "Lighten the sky."},
        ]
        output = optimize(brief)
        self.assertTrue(output.startswith(base))
        first = output.index("Left wing cropped.")
        second = output.index("Background too dark.")
        self.assertIn("Widen the frame.", output[first:second])
        self.assertIn("Lighten the sky.", output[second:])

    def test_malformed_briefs_report_field_paths(self):
        cases = [
            (None, "brief"), ({}, "intent"), ({"intent": " \t"}, "intent"),
            ({"intent": 3}, "intent"), ({"lang": "en"}, "lang"),
            ({"style": None}, "style"), ({"composition": []}, "composition"),
            ({"constraints": "green"}, "constraints"),
            ({"avoid": [""]}, "avoid[0]"),
            ({"references": ["picture"]}, "references[0]"),
            ({"references": [{"image": "image", "anchors": []}]}, "references[0].anchors"),
            ({"references": [{"anchors": []}]}, "references[0].image"),
            ({"references": [{"image": "i", "anchors": [{}]}]}, "references[0].anchors[0].aspect"),
            ({"references": [{"image": "i", "anchors": [{"aspect": "shirt", "detail": "red", "x": 2}]}]}, "x"),
            ({"revisions": [{"change": "Recover detail."}]}, "revisions[0].observed"),
            ({"revisions": [{"observed": "Too dark.", "change": 5}]}, "revisions[0].change"),
        ]
        for value, path in cases:
            with self.subTest(value=value):
                if isinstance(value, dict) and value and "intent" not in value:
                    value = {"intent": "Study.", **value}
                with self.assertRaises(ValueError) as error:
                    optimize(value)
                self.assertIn(path, str(error.exception))

    def test_example_is_a_usable_brief(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "brief.json"
        brief = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn(brief["intent"], optimize(brief))

    def test_creative_options_guide_generation_without_becoming_requirements(self):
        from imagegen_mastery.prompt import review_requirements
        brief = {"intent": "Make a lantern icon.", "constraints": ["Exactly one lantern."],
                 "creative_options": ["A dark handle could separate it from the backdrop."]}
        self.assertIn("Optional artistic choices", optimize(brief))
        self.assertIn(brief["creative_options"][0], optimize(brief))
        self.assertEqual(review_requirements(brief), ["Make a lantern icon.", "Exactly one lantern."])

    def test_creative_options_validate_and_empty_list_preserves_legacy_prompt(self):
        brief = {"intent": "An ink sketch."}
        self.assertEqual(optimize({**brief, "creative_options": []}), optimize(brief))
        for value in ("wide crop", [""], [3]):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "creative_options"):
                optimize({**brief, "creative_options": value})
