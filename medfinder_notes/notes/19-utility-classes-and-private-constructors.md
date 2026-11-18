# Utility Classes and Private Constructors (Chapter 3)

> **Chapter:** 3.1 Class Anatomy & Object Lifecycle, 3.5 Constructors & Initialization Pipelines, 3.6 Methods & Static Architecture | **In MedFinder:** `PasswordHasher.java` | **PR:** #2 by @wubettamrat525-prog

## What is it?

A **utility class** is a class that contains only static methods and static fields, serving as a container for related helper functions rather than representing a specific object. Because these classes do not hold state for individual objects, they should not be instantiated. We enforce this by defining a **private constructor**, which prevents any other class from using the `new` keyword to create an instance of the utility class.

## Why do we need it?

In MedFinder, we need a way to hash passwords. Since hashing is a stateless operation—it takes an input and returns a result without needing to remember anything about previous calls—we do not need to create a `PasswordHasher` object. If we allowed instantiation, developers might accidentally write `new PasswordHasher().hash(...)`, which wastes memory and creates unnecessary objects. A private constructor ensures the class is used only as a static library of functions.

## How it works

1. You declare the class as usual.
2. You define a constructor with the `private` access modifier.
3. Because the constructor is private, the compiler prevents any code outside this class from calling it.
4. You mark all methods and fields as `static`, allowing them to be accessed directly via the class name (e.g., `PasswordHasher.hash()`).

## How MedFinder uses it

### Preventing Instantiation

**Situation:** We want to ensure that `PasswordHasher` is used strictly as a static utility, preventing developers from creating instances of it.

**Code:**
```java
public class PasswordHasher {
    private static final int SALT_LENGTH = 16;
    private static final SecureRandom RANDOM = new SecureRandom();

    private PasswordHasher() {
    }
    // ...
}
```

**Walkthrough:** The `private PasswordHasher() {}` constructor has no parameters and no body. By making it `private`, we hide it from the rest of the application. If a developer tries to call `new PasswordHasher()`, the Java compiler will throw an error, enforcing our design choice that this class is a collection of tools, not an object.

## Common mistakes

A common mistake is forgetting to make the constructor private, which allows other parts of the program to create useless instances of your utility class. Another mistake is adding instance fields (non-static variables) to a utility class; if you find yourself needing instance fields, the class should likely be a regular object-oriented class instead of a utility class.

## Summary

Utility classes provide a clean way to group related static methods together. By using a private constructor, we prevent unnecessary object creation and clarify the intent of the class. This keeps our MedFinder codebase organized and prevents misuse of our helper logic.
