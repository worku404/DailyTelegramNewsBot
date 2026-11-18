# Enums and Compile-Time Type Safety (Chapters 2.5, 3.4, 3.5 & 4.4)

> **Chapter:** 2.5 Constants, 3.4 Encapsulation, 3.5 Static Members, 4.4 Enums | **In MedFinder:** `medfinder.model.PharmacyStatus`, `Role`, `Freshness`, `MatchLevel`, `AiOutcome.Kind` | **Source:** MedFinder core foundation

## What is it?

An `enum` is a special kind of class whose instances are a **fixed, closed set of named constants**, created once by the JVM at startup and never again. When you write `enum PharmacyStatus { PENDING, VERIFIED, REJECTED }`, Java creates exactly three `PharmacyStatus` objects — one per constant — with private constructors so nothing outside the enum can create more.

Because each constant is a singleton, you can compare enums safely with `==` instead of `.equals()`. And because the full set of valid values is known at compile time, the compiler rejects anything that isn't on the list.

## Why do we need it?

Before enums, teams used raw `String` constants: `pharmacy.setStatus("Verified")`. This looks fine until someone types `"verified"` or `"Verfied"` — a silent typo that compiles with no warning and breaks comparisons at runtime. With five team members each writing different parts of MedFinder, this kind of inconsistency is almost guaranteed. Making `PharmacyStatus` an enum means the compiler itself becomes the gatekeeper: `PharmacyStatus.VERIFED` doesn't exist, so it's a compile error, caught before the code ever runs.

## How it works

1. The JVM loads the enum class and calls the private constructor once for each constant, in order. Those objects are stored as `public static final` fields on the enum class.
2. Because they're singletons created at class-load time, `PharmacyStatus.VERIFIED == PharmacyStatus.VERIFIED` is always `true` — there's only one instance.
3. An enum can carry private fields and a constructor, letting each constant hold associated data (like a human-readable label).
4. Enums work natively in `switch` statements — no `.equals()` needed, no string matching, and the compiler can warn if you forget a case.
5. Any code that calls a method expecting `PharmacyStatus` and passes a value not in the enum simply does not compile. The error happens before the program runs.

## How MedFinder uses it

**Situation:** `PharmacyRepository.findByStatus(PharmacyStatus status)` needs to filter pharmacies by their approval state, and the status values need human-readable display labels for the console UI.

```java
public enum PharmacyStatus {
    PENDING("Pending"), VERIFIED("Verified"), REJECTED("Rejected");
    private final String label;
    PharmacyStatus(String label) { this.label = label; }
    public String label() { return label; }
}
// Usage - only valid values compile:
List<Pharmacy> verified = repo.findByStatus(PharmacyStatus.VERIFIED);
// repo.findByStatus(PharmacyStatus.APPROVED); → COMPILE ERROR
```

**Walkthrough:** Each constant — `PENDING`, `VERIFIED`, `REJECTED` — passes a string to the constructor, which stores it in the `private final String label` field. The `label()` accessor lets the console print `"Verified"` instead of the raw constant name `"VERIFIED"`. When a service calls `repo.findByStatus(PharmacyStatus.VERIFIED)`, the compiler checks that `VERIFIED` exists on `PharmacyStatus`. Trying to pass `PharmacyStatus.APPROVED` fails at compile time because `APPROVED` is not declared. The repository implementation then compares constants with `==` safely: `pharmacy.getStatus() == PharmacyStatus.VERIFIED`.

MedFinder uses five enums in total: `PharmacyStatus` for the admin approval workflow, `Role` to distinguish `ADMIN` from `PHARMACIST`, `Freshness` to classify stock age, `MatchLevel` to rank medicine search results, and `AiOutcome.Kind` to categorize what the AI response recommended.

## Common mistakes

- **Using `String` for domain states** — `"Verified"` and `"verified"` are different strings. The compiler won't catch the typo. Someone will make it.
- **Adding mutable fields to an enum** — enum constants are shared global singletons. A mutable field on `PharmacyStatus.VERIFIED` would be shared state across the entire application, mutated by any code that touches it.
- **Trying `new PharmacyStatus(...)`** — enum constructors are implicitly private. The compiler rejects this with a clear error. The instances already exist; you're not meant to create more.

## Summary

MedFinder replaces every domain "state" string with an enum: pharmacy approval states in `PharmacyStatus`, user roles in `Role`, AI response categories in `AiOutcome.Kind`, stock freshness in `Freshness`, and search match quality in `MatchLevel`. Each enum is a final class with a private constructor and a fixed set of singleton instances created once at JVM startup. The payoff is compile-time safety — the full set of valid values is known to the compiler, typos become compile errors instead of runtime bugs, `==` comparison is safe, and switch statements can exhaustively cover every case. Carrying a `label` field in `PharmacyStatus` lets the same constant drive both business logic and console display without duplicating strings anywhere.
