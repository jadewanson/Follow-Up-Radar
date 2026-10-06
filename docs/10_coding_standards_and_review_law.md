# 10. Coding Standards and Review Law

- **Owner role:** Tech Lead
- **Тип истины:** implementation discipline
- **Gate:** applies to every PR

## 1. Code standards
- Strong typing required where language/framework supports it.
- Public interfaces must be explicit.
- Naming must follow domain vocabulary.
- No ambiguous abbreviations for domain objects.
- Functions should have one clear responsibility.
- Side effects must be visible.

## 2. Naming law
Allowed core names:
- User
- FollowUpItem
- Reminder
- Subscription
- EventLog

Avoid vague names:
- Task
- Entity
- Object
- Thing
- Manager (unless truly orchestration layer)

## 3. Module law
A module must have:
- clear owner;
- clear responsibility;
- clear inputs/outputs;
- explicit dependency boundaries.

## 4. Comment/docstring policy
Code should be readable without excessive comments.
Required documentation belongs on:
- public service methods;
- non-obvious domain invariants;
- integration boundaries;
- error semantics.

## 5. Review checklist
Every PR must answer:
1. Does this strengthen the core loop?
2. Does it preserve SSOT?
3. Does it preserve one-owner rule?
4. Does it avoid fallback/best-effort in domain core?
5. Are failures explicit?
6. Are state transitions enforced by backend?
7. Are tests added/updated?
8. Is event logging still correct?
9. Does it avoid introducing scope drift?
10. Is there any compatibility residue?

## 6. Mandatory rejection conditions
A PR is rejected if it introduces:
- broad exception swallowing;
- duplicated domain truth;
- hidden mutations;
- silent fallbacks;
- “temporary” alternate paths in the core;
- undocumented config surface;
- missing tests for domain transition.

## 7. Refactor law
Refactoring is allowed only if it:
- reduces ambiguity;
- reduces duplication;
- sharpens ownership;
- does not enlarge scope.

## 8. Code generation/AI assistance law
Generated code is not trusted by default.
It must pass the same review gates as handwritten code.
