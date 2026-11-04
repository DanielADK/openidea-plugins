import base64
import unittest

import registry as r

KEY = base64.b64encode(bytes(32)).decode()
SHA = "0" * 64


def publisher(owners='["alice"]'):
    return f'name = "Alice"\nowners = {owners}\nkeys = ["{KEY}"]\n'


def plugin(version="0.1.0", package="https://example.com/a.oiplugin"):
    return (
        f'repository = "https://github.com/alice/arthas"\nversion = "{version}"\n'
        f'package = "{package}"\nsha256 = "{SHA}"\n'
    )


class Load(unittest.TestCase):
    def test_a_valid_registry(self):
        reg = r.load({"publishers/alice.toml": publisher(), "plugins/alice.arthas.toml": plugin()})
        self.assertEqual(reg.plugins["alice.arthas"].file, "alice.arthas-0.1.0.oiplugin")
        skeleton = r.index_skeleton(reg)
        self.assertEqual(skeleton["publishers"][0]["keys"], [{"key": KEY, "revoked": False}])

    def test_problems_are_all_reported(self):
        files = {
            "publishers/Bad.toml": publisher(),
            "publishers/bob.toml": 'name = "Bob"\nowners = ["bob"]\nkeys = ["short"]\n',
            "plugins/carol.x.toml": plugin(),
            "plugins/alice.toml": plugin(),
            "plugins/alice.y.toml": plugin(version="1"),
            "plugins/alice.z.toml": plugin(package="http://example.com/z"),
            "publishers/alice.toml": publisher(),
            "revoked.toml": '[[plugin]]\nid = "dave.x"\nreason = "malware"\n',
        }
        with self.assertRaises(r.Invalid) as e:
            r.load(files)
        message = str(e.exception)
        for expected in [
            "publishers/Bad.toml",
            "not an Ed25519 public key",
            "no publishers/carol.toml",
            "plugins/alice.toml: the file name",
            "semver",
            "https URL",
            "dave.x is not a plugin",
        ]:
            self.assertIn(expected, message)


class Review(unittest.TestCase):
    base = r.load({"publishers/alice.toml": publisher(), "plugins/alice.arthas.toml": plugin()})

    def test_owners_update_their_plugins(self):
        head = r.load({"publishers/alice.toml": publisher(), "plugins/alice.arthas.toml": plugin("0.2.0")})
        problems, notes = r.review(self.base, head, ["plugins/alice.arthas.toml"], "alice")
        self.assertEqual(problems, [])
        self.assertEqual(notes, ["`alice.arthas` 0.1.0 → 0.2.0"])

    def test_others_cannot_change_them_or_add_themselves_as_owners(self):
        head = r.load(
            {"publishers/alice.toml": publisher('["alice", "mallory"]'), "plugins/alice.arthas.toml": plugin("0.2.0")}
        )
        changed = ["publishers/alice.toml", "plugins/alice.arthas.toml"]
        problems, _ = r.review(self.base, head, changed, "mallory")
        self.assertEqual(len(problems), 2)
        self.assertEqual(r.review(self.base, head, changed, "l0ng-ai")[0], [])

    def test_a_new_publisher_is_noted_and_owned_by_its_author(self):
        files = {
            "publishers/alice.toml": publisher(),
            "plugins/alice.arthas.toml": plugin(),
            "publishers/bob.toml": publisher('["bob"]'),
            "plugins/bob.tool.toml": plugin(),
        }
        head = r.load(files)
        changed = ["publishers/bob.toml", "plugins/bob.tool.toml"]
        problems, notes = r.review(self.base, head, changed, "bob")
        self.assertEqual(problems, [])
        self.assertEqual(notes, ["new publisher `bob`", "new plugin `bob.tool`"])
        self.assertTrue(r.review(self.base, head, changed, "mallory")[0])

    def test_other_files_are_the_maintainers(self):
        problems, _ = r.review(self.base, self.base, ["scripts/registry.py", "revoked.toml"], "alice")
        self.assertEqual(len(problems), 2)


if __name__ == "__main__":
    unittest.main()
