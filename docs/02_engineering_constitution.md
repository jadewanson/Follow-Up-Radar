# Engineering Constitution v1

## Invariants
1. Backend + PostgreSQL are the only source of truth.
2. Every contour has exactly one owner.
3. Domain-critical paths fail closed.
4. No alias routes or compatibility residue in the core.
5. Contracts are frozen before feature implementation.
6. State transitions are explicit and backend-enforced.
7. Broad exception swallowing is forbidden.
8. Config validation is strict; bad config blocks startup.
9. Schema changes happen via migrations only.
10. Retries are bounded and allowed only for transport-level operations.

## Forbidden patterns
- hidden business state in frontend or extension
- fallback domain behavior
- dual-write truth surfaces
- undocumented side effects
- best-effort success in critical domain transitions
