# OpenIDEA community plugins

The registry of community plugins for [OpenIDEA](https://github.com/l0ng-ai/openidea).
Each plugin lives in its author's repository; this repository lists who
publishes what. Its index is merged into OpenIDEA's marketplace (Settings ›
Plugins › Available) within the hour of a change.

OpenIDEA's official plugins (`openidea.*`) are maintained in the OpenIDEA
repository, in `plugins/official/`.

## How it works

- A **publisher** owns a plugin id prefix: publisher `alice` publishes
  `alice.*`. It lists its Ed25519 public keys and the GitHub accounts that may
  change its entries.
- A **plugin entry** pins one released package: its URL and SHA-256. The
  package is signed with the publisher's key.
- On every change, CI downloads each package, checks its SHA-256, runs
  `openidea-plugin check` (the checks installing runs, against the latest
  OpenIDEA release), verifies its signature against the publisher's keys, and
  publishes `index.json` with copies of the packages in the
  [`index` release](../../releases/tag/index).
- A scheduled run checks every plugin daily against the latest release.

## Publishing a plugin

1. Get `openidea-plugin`: from an OpenIDEA release
   (`openidea-plugin-linux-x86_64.gz`), or
   `cargo install --locked --git https://github.com/l0ng-ai/openidea ide-host --bin openidea-plugin`.
2. Create your key once and keep the file secret:
   `openidea-plugin keygen alice.key` prints the public key.
3. Name your plugin `<publisher>.<name>` in `plugin.toml`, build and sign it:

   ```sh
   openidea-plugin build
   openidea-plugin pack . --key alice.key --publisher alice
   ```

4. Attach `alice.arthas-0.1.0.oiplugin` to a release of your repository and
   note its SHA-256 (`shasum -a 256 alice.arthas-0.1.0.oiplugin`).
5. Open a pull request here with your publisher (first time only) and the
   plugin entry:

   `publishers/alice.toml`

   ```toml
   name = "Alice"
   owners = ["alice"]                 # GitHub accounts that may change these entries
   keys = ["<public key>"]            # add new keys here; older ones stay valid
   revoked-keys = []                  # keys whose packages must no longer install
   ```

   `plugins/alice.arthas.toml`

   ```toml
   repository = "https://github.com/alice/openidea-arthas"
   version = "0.1.0"
   package = "https://github.com/alice/openidea-arthas/releases/download/v0.1.0/alice.arthas-0.1.0.oiplugin"
   sha256 = "<sha-256 of the package file>"
   ```

A new version is a pull request that changes `version`, `package` and
`sha256`. Removing the file delists the plugin (installed copies keep
working).

## Rules

**Listing.** New publishers and new plugins are reviewed by a maintainer:
the source, the capabilities it asks for and why, and that it doesn't
duplicate an existing plugin (improve that one instead). Version updates by an
owner need passing checks and a maintainer's merge; owners are checked
against the publisher file as it was before the pull request.

A plugin must:

- have a public source repository under an open-source licence, and the
  package must be built from it;
- say in its README what it does, and why it needs each `network:`,
  `process:` or other high-risk capability;
- contain no obfuscated or minified code that isn't built from that source.

**Maintenance.** A plugin that fails the checks against a new OpenIDEA
release is reported in an issue; if no fixed version is listed within 30 days,
it is delisted. Owners can hand a publisher over by adding owners.

**Revocation.** Maintainers revoke plugin versions or keys (in `revoked.toml`
or `revoked-keys`) for malware, a security problem the owner doesn't fix, or a
lost key; OpenIDEA then disables them where they are installed. Owners ask for
it in an issue.

**Becoming official.** A widely useful plugin can move to OpenIDEA's
`plugins/official/` when its owner and the maintainers agree; it then takes an
`openidea.*` id.

## Files

| Path | What |
| --- | --- |
| `publishers/<id>.toml` | a publisher: name, owners, keys |
| `plugins/<publisher>.<name>.toml` | a plugin's current version |
| `revoked.toml` | `[[plugin]]` entries: `id`, `versions` (empty: all), `reason` |
| `scripts/registry.py` | the checks and the index skeleton CI runs |
