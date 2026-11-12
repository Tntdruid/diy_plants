---
name: update-changelog
description: "Use when adding or updating a changelog or release notes from repository changes, including preparing entries for a release."
argument-hint: "Describe the changes or release to document"
---

# Update Changelog

Update this repository's changelog accurately and with minimal noise.

## Procedure

1. Read repository instructions and locate the existing changelog. Preserve its filename, language, headings, ordering, and entry style.
2. Determine what changed from the current task and, when available, the working-tree diff. Do not infer changes from generated files alone or claim behavior that has not been verified.
3. Include only meaningful user-facing changes. Group entries under the repository's existing categories. Omit internal refactors, tests, and routine maintenance unless they affect users or the project explicitly tracks them.
4. Add entries to the appropriate unreleased section without removing or rewriting unrelated history. Keep each entry concise and describe the impact, not just the implementation.
5. If no changelog exists, create `CHANGELOG.md` using a `# Changelog` heading and a `## Unreleased` section with only relevant categories (`Added`, `Changed`, `Fixed`, `Removed`, or `Security`).
6. Do not invent version numbers or release dates. Use an unreleased section unless the user explicitly asks to prepare a release and provides, or the repository clearly establishes, its version and date.
7. If the changes or intended release are unclear, ask for the missing details instead of guessing.
8. Review the final diff to confirm that only the intended changelog content changed and that prior entries remain intact.

## Repository Notes

- This repository contains the DIY Plants Home Assistant integration (`custom_components/diy_plants`) and its Lovelace card source (`card/`).
- `custom_components/diy_plants/frontend/diy-plants-card.js` is a generated bundle built from `card/`; avoid treating bundle-only churn as a user-facing changelog entry.
- `CHANGELOG.md` has one `## [x.y.z] - YYYY-MM-DD` section per released version, newest first, with a link reference at the bottom.
- To release: bump `version` in `custom_components/diy_plants/manifest.json`, add the matching changelog section, commit, then push a `vX.Y.Z` tag. The Release workflow checks that the tag matches the manifest and publishes the changelog section as the GitHub release notes.
