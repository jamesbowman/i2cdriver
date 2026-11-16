# Publishing i2cdriver

Releases are built and published by `.github/workflows/release.yml` using
PyPI Trusted Publishing. No PyPI API token or `.pypirc` file is required.
The publishing action creates attestations for both the source archive and wheel.

## One-time setup

1. On GitHub, open `jamesbowman/i2cdriver` → Settings → Environments.
   Create an environment named `pypi`. Add yourself as a required reviewer
   if you want to approve every publication. Leave “Prevent self-review”
   disabled if you also initiate the releases.
2. On PyPI, open https://pypi.org/manage/project/i2cdriver/settings/publishing/.
   Add a GitHub Trusted Publisher with these exact values:

   | Field | Value |
   | --- | --- |
   | Owner | `jamesbowman` |
   | Repository | `i2cdriver` |
   | Workflow filename | `release.yml` |
   | Environment | `pypi` |

   The workflow filename has no `.github/workflows/` prefix.

## Release

1. Update the package version, commit, and push. For I2CDriver, keep the
   module version and `pyproject.toml` version in sync.
2. Optionally use Actions → Publish to PyPI → Run workflow on the intended
   branch. Manual runs build and test only; they never publish.
3. Create and publish a GitHub Release for a tag matching the version,
   for example `v1.0.7` (or `1.0.7`). Select the commit containing
   the version bump and this workflow. Publishing a prerelease also runs it.
4. Approve the `pypi` environment deployment if required reviewers are configured.
5. Check the workflow result and the release's Security tab on PyPI. Both
   files should have provenance.

Publishing a GitHub Release triggers the upload; pushing a tag alone does not.
An already-published PyPI version cannot be replaced. Make a new version for
subsequent releases. The workflow does not silently skip existing files.

The build and tests run without publishing credentials. Only the separate
publish job has permission to request a short-lived PyPI credential. Action
references are pinned to commits; review and update those pins periodically.

References: [Trusted Publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
and [attestations](https://docs.pypi.org/attestations/producing-attestations/).
