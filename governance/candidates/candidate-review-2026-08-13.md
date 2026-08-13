# External Skill Candidate Review

**Review date:** 2026-08-13  
**Purpose:** Identify broadly useful additions to the collection without importing unreviewed instructions, unlicensed content, or executable code.

## Admission Standard

A community skill is not copied into this repository merely because it is formatted as a Skill. It must fill an observed gap, avoid materially overlapping triggers, present no unreviewed execution path, and have a license that permits the intended reuse. Manus also advises reviewing community skills before use because they may include code or shell commands. [1]

| Candidate | Observed value | Review finding | Decision |
|---|---|---|---|
| `abcnuts/manus-skills` → `systematic-debugging` | Provides a clear root-cause-first debugging workflow, a gap in the current 32-skill baseline. | The repository did not expose a license through GitHub metadata during review. The guide also contains an unsafe diagnostic example that could expose environment values if copied without redaction. | **Do not copy.** Create an independent, repository-owned `systematic-debugging` skill with a redaction-first evidence policy and new wording. |
| `abcnuts/manus-skills` → `testing-framework` | General test planning is useful for web and integration work. | The guide is 752 lines, tied to particular JavaScript tools, includes installation commands, and the repository did not expose a license through GitHub metadata. | **Do not import.** Keep the compact cross-skill test-card framework already added; consider a self-authored testing skill only when a concrete application-testing gap recurs. |
| `abcnuts/manus-skills` → `skill-development-workflow` | Addresses creation of new skills. | It duplicates the purpose of the existing `skill-creator` skill. | **Reject as duplicate.** Improve the existing `skill-creator` skill instead. |
| `WebWakaHub/manus-agency-skills` | Advertises a collection adapted for Manus. | Repository-level metadata did not expose a license during review; no candidate with a demonstrated non-overlapping trigger was selected. | **Quarantine.** Do not clone, execute, or copy until a specific candidate and license can be verified. |
| `yuanqi99/manus-skills` → `pdf-watermark-remover` | Supplies a specialized PDF operation. | The offered capability is not a demonstrated general gap for this collection and could create rights-sensitive usage concerns. | **Reject.** No import or adaptation. |

## Approved Action

Create one self-authored skill: `systematic-debugging`. Its scope is investigation of reproducible technical failures in code, tests, builds, runtime behavior, performance, and integrations. It must require evidence collection before code changes, prohibit logging secrets or raw sensitive payloads, prescribe a single-hypothesis test loop, and require regression verification.

No community code, scripts, templates, or wording is imported by this decision. The candidate is treated as a design signal only.

## References

[1]: https://manus.im/docs/features/skills "Manus Skills Documentation — Verifying Community Skills"
[2]: https://github.com/abcnuts/manus-skills "Candidate repository: abcnuts/manus-skills"
[3]: https://github.com/WebWakaHub/manus-agency-skills "Candidate repository: WebWakaHub/manus-agency-skills"
[4]: https://github.com/yuanqi99/manus-skills "Candidate repository: yuanqi99/manus-skills"
