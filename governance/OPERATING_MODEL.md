# Operating Model for the Skills Collection

## Purpose

This repository manages skills as operational assets. A skill is not approved merely because its Markdown is well formed; it must route the right request, provide an actionable path, state how success is checked, and identify a safe response when the task cannot proceed.

## Change Rules

Every skill change must preserve a recoverable Git history and run `python3 scripts/audit_skills.py`. Changes that alter a skill's trigger, safety boundary, external integration, or output contract must add or update its behavioral test card in `tests/skill-cards/`.

A change may improve a skill, add a missing reference or script, split an overlong core guide into progressive references, or introduce a new skill after duplication and safety review. It must not silently delete a working path, embed real credentials, or create a duplicate trigger that conflicts with an existing skill.

## Quality Gate

The repository uses `governance/quality_gates.json` as the source of truth. Approval requires a score of at least 85/100 and passage of the mandatory structural-integrity, invocation-boundaries, workflow, and verification gates. High-risk integration skills also require explicit failure and safety evidence before they can be considered operationally ready.

## Behavioral Test Cards

Each card uses the JSON contract in `governance/skill_test_card.schema.json`. A normal-risk skill requires at least three cases: one positive invocation, one negative invocation, and one failure or safety case where relevant. High-risk skills require at least six cases because their trigger boundaries and error paths need broader evidence.

The card tests expected behavior rather than language similarity. A good expected outcome says which skill should be invoked or avoided, which operating path should be followed, and what safe next step should happen when a dependency, credential, confirmation, or data input is missing.

## Freshness and External Sources

The collection does not use personal ownership fields as a release prerequisite. Instead, any skill containing time-sensitive API, pricing, quota, platform, or security information must identify the authoritative source category in the central registry and be rechecked during its development wave. No review may treat a stale example as proof of an external service's current behavior.

## New Skill Admission

A candidate skill is added only if it fills a documented workflow gap, has no materially overlapping trigger with an existing skill, is safe to distribute, includes its necessary references or scripts, and passes the same quality gate as native skills. Candidate material from the web is evidence only; it is never executed or trusted without review.
