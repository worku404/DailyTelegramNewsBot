# Strings and Normalization Contracts (Chapter 2.7)

> **Chapter:** 2.7 The String Class | **In MedFinder:** `UserRepository.findByEmail(String email)`, `PharmacyRepository.findByLicence(String licenceNumber)`, `TextSimilarity`, `CsvFile`, `PromptBuilder` | **Source:** MedFinder core foundation

## What is it?

`String` in Java is an immutable reference type. "Immutable" means that once a `String` object is created, its characters can never change. When you call `.trim()`, `.toLowerCase()`, or `.replace(...)` on a string, Java does not modify the original — it creates and returns a **brand new** `String` object with the result applied.

Because strings are immutable, the JVM maintains a **String Constant Pool (SCP)**: string literals like `"admin"` written in source code are interned — stored once in a shared pool and reused. This is safe only because no one can mutate them.

## Why do we need it?

MedFinder stores email addresses and pharmacy licence numbers entered by real users through a console. Users type inconsistently: `"Alice@Example.COM"` and `"alice@example.com"` are the same person. `"AA 1234"` and `"AA1234"` are the same licence. If `findByEmail` did a straight character-by-character comparison with no normalization, the same pharmacist would fail to log in half the time depending on how they typed their email that day. The team needs an explicit, agreed **normalization contract** baked into every lookup method — not left to individual callers to remember.

## How it works

1. `String` variables store a reference (a heap address), not the characters themselves. Two different `String` objects can hold identical characters but live at different memory addresses.
2. `==` compares addresses — it asks "are these the same object in memory?" For strings, that is almost always the wrong question.
3. `.equals(String other)` compares the actual characters, one by one. `.equalsIgnoreCase(String other)` does the same but treats uppercase and lowercase as identical.
4. Every transformation method returns a new `String`. The original is unaffected. If you don't assign the result, the transformation is lost.
5. When building a `String` inside a loop (like `PromptBuilder` assembling an AI prompt), use `StringBuilder`. Concatenating with `+` inside a loop creates a new `String` object on every iteration — O(n²) object allocations. `StringBuilder.append(...)` modifies a single internal buffer — O(n).

## How MedFinder uses it

**Situation:** `UserRepository.findByEmail(String email)` needs to match the stored email against user input regardless of how the user capitalized it.

```java
// Case-insensitive email:
if (user.getEmail().equalsIgnoreCase(email.trim())) { return user; }
```

**Walkthrough:** `email.trim()` returns a new `String` with leading and trailing whitespace stripped — the kind of whitespace that sneaks in when a user copies and pastes their email. `.equalsIgnoreCase(...)` then compares characters case-insensitively: `"Alice@Example.COM"` matches `"alice@example.com"` without either string being mutated. Note that `.equalsIgnoreCase` is called on `user.getEmail()` (the stored value), not on `email` (the input), which avoids a `NullPointerException` if the input is null.

**Situation:** `PharmacyRepository.findByLicence(String licenceNumber)` must match licence numbers whether or not the user typed spaces, since `"AA 1234"` and `"AA1234"` are the same licence.

```java
// Licence normalization (remove spaces + lowercase):
String normalizedTarget = licenceNumber.replace(" ", "").toLowerCase();
String normalizedStored = pharmacy.getLicenceNumber().replace(" ", "").toLowerCase();
if (normalizedStored.equals(normalizedTarget)) { return pharmacy; }
```

**Walkthrough:** `.replace(" ", "")` returns a new `String` with all space characters removed. `.toLowerCase()` returns another new `String` with all characters lowercased. Both are chained and their results assigned to new variables — the original `licenceNumber` and `pharmacy.getLicenceNumber()` are completely untouched. Both sides are normalized the same way before `.equals()` compares them, so the comparison is fair regardless of how either was typed or stored.

## Common mistakes

- **Calling a transformation and discarding the result** — writing `licenceNumber.toLowerCase();` on its own line does nothing. The returned string is immediately garbage-collected. You must assign it: `licenceNumber = licenceNumber.toLowerCase();`.
- **Using `==` to compare strings** — `"hello" == new String("hello")` is `false` because they are different objects. Always use `.equals()` or `.equalsIgnoreCase()` for content comparison.
- **Calling `.equals()` on a potentially null string** — `email.equals(storedEmail)` throws `NullPointerException` if `email` is null. Put the known non-null value on the left: `storedEmail.equals(email)`, or use `Objects.equals(email, storedEmail)`.
- **Concatenating with `+` inside a loop** — building a prompt by doing `result = result + line` in a loop creates a new `String` object on every iteration. Use `StringBuilder` and call `.append(line)` instead.

## Summary

`String` immutability is not just a trivia fact — it shapes every lookup in MedFinder. Because strings can never be mutated, every normalization step (`trim`, `toLowerCase`, `replace`) must be explicitly captured in a new variable. `UserRepository.findByEmail` applies `.equalsIgnoreCase()` to absorb case variation, while `PharmacyRepository.findByLicence` strips spaces and lowercases both sides before comparing — these are deliberate normalization contracts, not afterthoughts. `PromptBuilder` and `CsvFile` use `StringBuilder` wherever strings are assembled iteratively, keeping performance linear. The rule across all of MedFinder: never use `==` on strings, never discard a transformation result, and always normalize both sides of a lookup the same way.
