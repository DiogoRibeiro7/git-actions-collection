# PR triage

Date: 2026-01-27

## Inventory (open PRs)

| PR | Title | Type | Ecosystem | Major? | Lockfiles | Risk | Recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| #49 | chore: group GitHub Actions bumps | GitHub Actions (grouped) | CI workflows | Yes (golangci-lint-action v9) | None | Medium | **Merge** after CI | Includes metadata-action, setup-qemu, attest-build-provenance, zaproxy action, golangci-lint action. Golangci-lint-action v9 requires Node 24 runtime. citeturn0search1turn0search2 |
| #48 | build(deps): update packaging requirement from <26.0.0,>=25.0 to >=25.0,<27.0.0 | Dependabot runtime dep | Python | No | None | Low | **Merge** | Upper-bound relaxation only; packaging 26.0 is available on PyPI. citeturn0search0 |
| #47 | build(deps): bump docker/metadata-action from 5.8.0 to 5.10.0 | Dependabot GH Actions | CI workflows | No | None | Low | **Close (superseded by #49)** | Included in grouped PR. |
| #46 | build(deps): bump actions/attest-build-provenance | Dependabot GH Actions | CI workflows | No | None | Low | **Close (superseded by #49)** | Included in grouped PR. |
| #45 | build(deps): bump docker/setup-qemu-action | Dependabot GH Actions | CI workflows | No | None | Low | **Close (superseded by #49)** | Included in grouped PR. |
| #44 | build(deps): bump zaproxy/action-api-scan | Dependabot GH Actions | CI workflows | Pre‑1 (0.x) | None | Low–Medium | **Close (superseded by #49)** | Pre‑1 action; grouped PR includes bump. citeturn0search0 |
| #43 | build(deps): bump golangci/golangci-lint-action from 8.0.0 to 9.1.0 | Dependabot GH Actions | CI workflows | **Yes** | None | Medium | **Close (superseded by #49)** | Major bump; v9 requires Node 24 runtime. citeturn0search1turn0search2 |
| #42 | chore: upgrade pyproject constraints | Maintenance | Python deps (runtime + dev) | **Yes** (packaging 25→26) | None | Medium | **Review + merge** after CI | packaging 26.0 released Jan 21, 2026; check for behavior changes in packaging semantics. citeturn0search0 |

## Grouping plan

- **Grouped PR created:** #49 (`deps/github-actions-bumps-grouped`).
- **Action:** close superseded Dependabot PRs #43–#47 and #44 after #49 merges.

## Lockfiles

- No lockfiles changed in any of the PRs above (no `yarn.lock`, `poetry.lock`, or similar changes reported in PR file lists).

## Risk notes (major bumps)

- **golangci-lint-action v9**: requires Node 24 on GitHub runners. citeturn0search1turn0search2
- **packaging 26.x**: new major release, published Jan 21, 2026. citeturn0search0

## Recommended next actions

1) Merge **#49** after CI passes; close #43–#47 and #44 as superseded.  
2) Merge **#48** (low risk, upper‑bound only).  
3) Review **#42** for packaging 26 behavior changes and then merge if CI green.
