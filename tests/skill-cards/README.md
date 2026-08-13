# Skill Test Cards

Place one JSON test card per skill in this directory using the filename `<skill-name>.json` and the contract in `governance/skill_test_card.schema.json`.

A card documents the request, whether the skill should be invoked, and the observable safe outcome. It does not need a live credential or external service unless that capability is being tested in a controlled integration fixture.

Use the following case mix as a minimum:

| Risk level | Minimum cases | Required mix |
|---|---:|---|
| Low or medium | 3 | At least one positive, one negative, and one failure or safety case. |
| High | 6 | At least two positive, two negative, and two failure or safety cases. |

Keep prompts specific enough to distinguish neighboring skills. For example, a negative case for a scheduling skill should describe a one-time deterministic action that does not warrant a scheduler, rather than a completely unrelated task.
