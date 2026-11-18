# Exception Wrapping and IllegalStateException (Chapter 6)

> **Chapter:** 6.2 The Java Throwable Hierarchy, 6.3 Checked vs. Unchecked Exceptions, 6.6 Custom Domain Exceptions & Enterprise Architecture | **In MedFinder:** `PasswordHasher.java` | **PR:** #2 by @wubettamrat525-prog

## What is it?

**Exception wrapping** is the practice of catching a low-level exception and throwing a different, more meaningful exception in its place, often including the original error as the "cause." An `IllegalStateException` is an unchecked exception used to signal that a method has been invoked at an inappropriate time or in an environment where the requested operation cannot be performed.

## Why do we need it?

In MedFinder, we use `MessageDigest` to hash passwords, which requires the "SHA-256" algorithm. The Java API forces us to handle `NoSuchAlgorithmException`, a checked exception that occurs if the algorithm is missing. However, SHA-256 is guaranteed to exist in every standard Java environment. We don't want to force every caller of our `hash` method to handle an error that should never happen, so we wrap it in an unchecked `IllegalStateException`.

## How it works

1. You wrap the code that might throw a checked exception in a `try-catch` block.
2. In the `catch` block, you create a new exception (like `IllegalStateException`).
3. You pass the original exception object into the constructor of the new exception. This preserves the stack trace, allowing us to see the root cause if something truly goes wrong.

## How MedFinder uses it

### Preserving Root Causes

**Situation:** We need to perform cryptographic operations that technically throw checked exceptions, but we want to keep our method signature clean for the rest of the application.

**Code:**
```java
} catch (NoSuchAlgorithmException e) {
    throw new IllegalStateException(
        "SHA-256 algorithm is unavailable.", e
    );
}
```

**Walkthrough:** Here, we catch `NoSuchAlgorithmException`. Instead of forcing the caller to handle it, we throw a new `IllegalStateException`. By passing `e` as the second argument to the constructor, we "chain" the exceptions. If the program crashes, the error log will show our custom message and the original `NoSuchAlgorithmException`, making debugging much easier.

## Common mistakes

A common mistake is to catch an exception and do nothing with it (swallowing the exception), which makes debugging impossible. Another mistake is creating a new exception without passing the original one as a cause, which discards the valuable information about why the error occurred in the first place.

## Summary

Exception wrapping allows us to simplify our method signatures while still maintaining diagnostic information. By using `IllegalStateException` for impossible errors, we keep our code readable and robust. Always remember to pass the original exception as a cause to ensure that the root problem remains visible.
