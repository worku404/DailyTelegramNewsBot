# Encapsulation and Invariant Enforcement (Chapter 3)

> **Chapter:** 3.4 Encapsulation & Access Control | **In MedFinder:** `Pharmacy.java`, `Medicine.java` | **PR:** #3 by @tesnimabdi16-netizen

## What is it?

**Encapsulation** is the practice of bundling data (fields) and the methods that operate on that data into a single unit, like a class, while restricting direct access to the internal state. By making fields `private`, we prevent external code from putting an object into an invalid state. We then use methods to enforce **invariants**—rules that must always be true for an object to be considered valid.

## Why do we need it?

In MedFinder, a `Pharmacy` must always have a valid status. If we allowed any part of the program to change the `status` field directly, someone might accidentally set a `REJECTED` pharmacy to `VERIFIED` without providing the necessary documentation or following the required business rules. Without encapsulation, our objects become fragile, and bugs spread across the entire codebase because the object cannot protect its own integrity.

## How it works

1. We mark all internal fields as `private` so they cannot be accessed from outside the class.
2. We provide public methods (like `approve()` or `reject()`) that act as the only way to change the state.
3. Inside these methods, we check if the requested change is allowed based on the current state.
4. If the change violates a rule, we throw an exception to stop the operation immediately.

## How MedFinder uses it

### Protecting Pharmacy State

MedFinder ensures that a pharmacy can only transition between statuses in specific ways. The `Pharmacy` class hides its `status` field and forces all changes through controlled methods.

```java
public void approve() {
    if (status != PharmacyStatus.PENDING) {
        throw new ValidationException("Only a pending pharmacy can be approved.");
    }
    status = PharmacyStatus.VERIFIED;
}
```

**Walkthrough:** The `status` field is `private`. The `approve()` method checks if the current `status` is `PENDING`. If it is not, it throws a `ValidationException`. This prevents the pharmacy from being approved if it is already `REJECTED` or `VERIFIED`, ensuring our business rules are never bypassed.

### Validating Constructor Inputs

We also use private helper methods to ensure that when a new object is created, it starts in a valid state.

```java
private static String requireText(String value, String fieldName) {
    if (value == null || value.trim().isEmpty()) {
        throw new ValidationException(fieldName + " must not be empty.");
    }
    return value.trim();
}
```

**Walkthrough:** The `requireText` method is a private utility used by constructors to validate strings. By calling this in the constructor, we guarantee that a `Pharmacy` or `Medicine` cannot exist with an empty name or address. If the input is invalid, the object is never created, preventing "garbage" data from entering our system.

## Common mistakes

1. **Exposing mutable state:** A common mistake is providing a public setter for every field. This defeats encapsulation because it allows external code to bypass your validation logic. Only provide methods that represent actual business actions, like `approve()` or `update()`.
2. **Trusting the caller:** Never assume the data passed to your constructor or methods is correct. Always validate inputs inside the class to maintain the object's invariants.

## Summary

Encapsulation is about protecting the integrity of your objects by hiding their internal state. By using `private` fields and controlled methods, we ensure that an object can only change in ways that make sense for our business. This makes our code much easier to debug and maintain, as we know exactly where and how the state can change.
