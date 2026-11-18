# Checked vs Unchecked Exceptions (Chapters 6.1–6.4 & 6.6)

> **Chapter:** 6.1 Principles of Exception Handling, 6.2 Throwable Hierarchy, 6.3 Checked vs Unchecked, 6.4 throw/throws/Stack Unwinding, 6.6 Custom Exceptions & Chaining | **In MedFinder:** `medfinder.exception.MedFinderException`, `DataStorageException`, `CsvFile`, `FileUserRepository`, all 5 repository interfaces | **Source:** MedFinder core foundation

## What is it?

When something goes wrong at runtime, Java lets you throw an exception object up the call stack until something catches it. The language draws a hard line between two kinds: **checked exceptions** and **unchecked exceptions**.

A **checked exception** (like `IOException`) is one the compiler forces you to deal with right now — either catch it, or add `throws IOException` to your method signature so the caller handles it. Think of it like a certified parcel that needs a signature at every handoff until someone accepts it.

An **unchecked exception** (any subclass of `RuntimeException`, like `NullPointerException` or MedFinder's own `DataStorageException`) needs no signature on method headers. It travels up the call stack automatically, like a fire alarm that rings all the way to the top floor without anyone needing to pass it along manually.

## Why do we need it?

Imagine `FileUserRepository` just let its `IOException` bubble out uncaught. The `UserRepository` interface would have to declare `throws IOException`, which means `AuthService`, `PharmacyService`, and every menu class that calls a repository would all need `throws IOException` on their signatures too — or be wrapped in try/catch boilerplate everywhere. Worse, the repository interface would be permanently locked to file I/O details: swap storage to SQL and now you need `throws SQLException` everywhere instead. The whole codebase becomes a chain of leaking plumbing.

## How it works

1. `CsvFile.readAll(Path path)` is a low-level file helper that wraps `java.nio.file.Files`. It declares `throws IOException` — a checked exception — because the compiler insists.
2. `FileUserRepository.findById(int id)` calls `csvFile.readAll(...)`. Because `readAll` is checked, `FileUserRepository` must handle it right there at the boundary.
3. Inside a `try/catch`, `FileUserRepository` catches `IOException` and throws a **new** `DataStorageException` instead — an unchecked exception that extends `MedFinderException → RuntimeException`.
4. Because `DataStorageException` is unchecked, none of the repository interfaces, services, or menus need to declare it. It travels up the stack silently.
5. **Stack unwinding**: when the exception is thrown and not caught locally, the JVM pops the current stack frame, moves to the caller's frame, and repeats until a `catch` is found. `Menu.run()` has one central `catch (MedFinderException e)` that handles all of them in one place.
6. A `finally` block, if present, runs no matter what — whether the try succeeded or an exception was thrown — before the frame is popped.

## How MedFinder uses it

**Situation:** `FileUserRepository` calls `CsvFile.readAll(...)`, which can throw a checked `IOException`. We need the repository interface to stay clean (no `throws IOException`) and upper layers to stay decoupled from file-system details.

```java
// CsvFile.readAll declares throws IOException (checked)
// FileUserRepository translates it at the boundary:
try {
    return csvFile.readAll(path);
} catch (IOException e) {
    throw new DataStorageException("Could not read users.csv", e);
}
```

**Walkthrough:** The `try` block calls `csvFile.readAll(path)` — if the file is missing or unreadable, `readAll` throws `IOException`. The `catch` block intercepts it and throws a brand-new `DataStorageException`. Notice the second argument `e` — that's exception chaining. Passing `e` as the cause means anyone who calls `getCause()` on the `DataStorageException` later (or reads the stack trace) can still see the original `IOException` and the exact line in `CsvFile` where it happened. Without `e`, that diagnostic information is gone forever.

The exception hierarchy looks like this:

```
java.lang.Throwable
  ├── Error                    ← catastrophic JVM failures, never catch
  └── Exception
        ├── IOException        ← CHECKED: must catch or declare throws
        └── RuntimeException   ← UNCHECKED: no throws clause required
              └── MedFinderException
                    ├── DataStorageException
                    ├── ValidationException
                    ├── NotFoundException
                    ├── AuthorizationException
                    └── AiServiceException
```

## Common mistakes

- **Swallowing exceptions** — writing `catch (IOException e) {}` with an empty body. The error disappears silently; a corrupted file or failed save looks like success.
- **Losing the root cause** — throwing `new DataStorageException("Failed")` without passing `e`. The original `IOException` and its stack trace are destroyed, making production debugging nearly impossible.
- **Using exceptions for normal control flow** — throwing `NotFoundException` from a repository when the caller simply asked "does this email exist?" and `null` is a perfectly valid answer. Reserve exceptions for genuinely unexpected failures.
- **Catching `Throwable` or `Error`** — `OutOfMemoryError` and `StackOverflowError` signal the JVM is broken. Catching them and carrying on will produce unpredictable behavior. Catch `Exception` or your own domain base class at most.

## Summary

MedFinder's exception design has one job: keep low-level file I/O details from leaking into high-level code. `CsvFile` uses Java's checked `IOException` because it directly wraps file APIs that require it. `FileUserRepository` acts as the translation boundary — it catches `IOException` and re-throws it as the unchecked `DataStorageException`, preserving the original cause via exception chaining. Because `DataStorageException` is unchecked, all five repository interfaces stay clean with no `throws` clauses, and stack unwinding carries any storage failure straight to the single `catch (MedFinderException e)` handler in `Menu.run()` — one place, clean error display, no boilerplate scattered across the codebase.
