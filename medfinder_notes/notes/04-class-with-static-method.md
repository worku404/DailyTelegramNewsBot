# Static Methods and Utility Classes (Chapters 2 & 3)

> **Chapter:** 2.6 Static Variables & Methods, 3.2 Writing Classes, 3.4 Method Design, 3.5 Static Methods, 3.6 Method Overloading | **In MedFinder:** `medfinder.logic.TextSimilarity`, `medfinder.logic.FreshnessClassifier`, `medfinder.logic.PasswordHasher` | **Source:** MedFinder core foundation

## What is it?

Every regular method in Java belongs to an **instance** — you need to create an object first, then call the method on it. A **static** method belongs to the **class itself**. No object needed. You call it directly on the class name.

A **utility class** is a class that exists purely to group related static methods. It holds no data, keeps no state, and is never meant to be instantiated. `medfinder.logic.TextSimilarity` is a utility class: it offers `levenshtein` to calculate the edit distance between two strings, and nothing else. There's no "TextSimilarity object" in the program — just the method, available anywhere.

## Why do we need it?

The Levenshtein distance calculation has nothing to do with any particular medication or search session. It's a pure mathematical operation: give it two strings, it gives back a number. If we put this in a service class, we'd have to instantiate that service just to call a math function, dragging along all its dependencies. Instead, we put it in `TextSimilarity` as a static method. Any class that needs it calls `TextSimilarity.levenshtein(a, b)` — no object, no dependencies, no ceremony. The same reasoning applies to `FreshnessClassifier` and `PasswordHasher`.

## How it works

1. When the JVM loads a class, it stores its static methods in **Metaspace** (a memory area for class metadata). Static methods stay there for the lifetime of the program.
2. When you call a regular instance method, the JVM uses the `invokevirtual` bytecode instruction, which looks up the actual runtime type of the object to find the right method. When you call a static method, it uses `invokestatic`, which resolves directly to the class — no object lookup needed, no polymorphism.
3. A **pure function** is a method whose output depends only on its inputs and has no side effects. Static utility methods should be pure functions. `TextSimilarity.levenshtein("amoxcillin", "amoxicillin")` always returns the same number for the same input, touches nothing outside itself, and changes nothing.
4. The `private` constructor prevents `new TextSimilarity()` from compiling. The `final` keyword prevents subclassing. Together they enforce the contract: this class is a namespace for functions, not a blueprint for objects.

## How MedFinder uses it

**Situation:** when a user types a medication name, we need to find the closest match in our database even if they misspelled it — without instantiating any object to do it.

```java
public final class TextSimilarity {
    private TextSimilarity() {
        throw new UnsupportedOperationException("Utility class");
    }

    public static int levenshtein(String s1, String s2) {
        // dynamic programming implementation
        // ...
    }
}

// Caller (somewhere in the search service):
int distance = TextSimilarity.levenshtein("amoxcillin", "amoxicillin");
```

**Walkthrough:** `public final class` — `final` means no subclass can override or misuse this class. `private TextSimilarity()` — the constructor is private so `new TextSimilarity()` won't compile anywhere. The `throw` inside it is a safeguard for reflection: if someone uses reflection to bypass the private modifier, they get a clear runtime error instead of a silently broken object. `public static int levenshtein` — `static` means the caller writes `TextSimilarity.levenshtein(...)` with no object on the left side. The JVM resolves this at compile time using `invokestatic`. The calling code passes two strings and gets back an integer. No TextSimilarity instance is created or stored anywhere.

## Common mistakes

- **Mutable static variables.** A `static` field is shared across the entire program — every thread, every call. If `TextSimilarity` had a `static int lastResult` field, one search could overwrite another's result. Utility classes must have no static fields (except constants like `static final`).
- **Making services static.** `medfinder.service.MedicationService` manages state (a list of medications, a reference to the repository). Making it static would turn that state into global state — shared, hard to test, and impossible to have two independent instances of. Static is for stateless utilities only.
- **Forgetting the private constructor.** Without it, nothing stops a teammate from writing `new TextSimilarity()` and creating a useless object. The private constructor is the signal — and the enforcement — that this class is a functions-only namespace.
- **Skipping `final`.** Without `final`, someone could subclass `TextSimilarity` and override its behaviour. That opens the door to polymorphic confusion in a class that was never meant to participate in inheritance.

## Summary

Static methods belong to the class, not to any instance; the JVM resolves them with `invokestatic` from Metaspace at compile time. Utility classes like `medfinder.logic.TextSimilarity`, `medfinder.logic.FreshnessClassifier`, and `medfinder.logic.PasswordHasher` collect pure functions that need no object state. They are marked `final` to block subclassing and given a `private` constructor (with a defensive `throw`) to block instantiation. This pattern keeps stateless logic portable, easy to test, and completely free of the coupling that comes with object lifecycle management.
