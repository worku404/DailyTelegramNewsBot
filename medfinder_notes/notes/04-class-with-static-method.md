# Course Concept: Class with Static Methods (Chapters 2 & 3)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Methods, Memory, and Class Design (`static` keyword, Utility Classes, Pure Functions)  
> **Where in MedFinder:** `medfinder.logic.TextSimilarity`, `medfinder.logic.FreshnessClassifier`, `medfinder.logic.PasswordHasher`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

In Java, the keyword `static` means: **"This member belongs to the class itself, NOT to individual objects created from the class."**

- **Instance Method (Regular):** Needs an object (`new MyClass()`) to be called. It operates on the internal state (instance variables) of that specific object.
- **Static Method:** Does **not** need an object. You call it directly using the class name: `ClassName.methodName()`. It does not store state; it takes inputs, calculates, and returns a result.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: What is a `static` method, and how is it fundamentally different from an instance method?

**Answer:**
An **instance method** is tied to a specific object in heap memory. It uses the `this` reference to inspect or modify that object's instance fields. For example:
```java
Pharmacy p = new Pharmacy(...);
p.approve(); // Instance method: changes the status of this specific pharmacy
```

A **static method** belongs to the class blueprint itself. It is loaded once into the JVM's Metaspace/Method Area when the class is loaded. It runs without creating any object in heap memory:
```java
double score = TextSimilarity.relevance("paracetamol", "paracetamol 500mg");
// Static method: no "new TextSimilarity()" needed!
```

---

### Question 2: Why do `TextSimilarity`, `FreshnessClassifier`, and `PasswordHasher` use static methods in MedFinder?

**Answer:**
Because they are **stateless pure calculation engines (utility/logic classes)**:

1. **`TextSimilarity`** computes Levenshtein edit distance between two strings. It does not need to remember anything between calls. Passing two words into `levenshtein("amox", "amoxicillin")` will always return `7`, regardless of who calls it or when.
2. **`FreshnessClassifier`** evaluates hours: `classify(5)` always returns `Freshness.FRESH`. It has no internal memory or state to preserve.
3. **`PasswordHasher`** takes a password and salt and produces a SHA-256 hash.

Creating `new TextSimilarity()` every time a customer searches for a medicine would waste CPU cycles and garbage-collection memory by allocating objects that hold zero instance data. Making these methods `static` makes the code cleaner, faster, and more expressive.

---

### Question 3: Can a `static` method use the `this` keyword or access instance variables? Why or why not?

**Answer:**
**No, absolutely not.** 

A static method is called without an object instance (e.g. `Math.sqrt(16)` or `TextSimilarity.normalise(text)`). Because there is no object instance associated with the call:
- The `this` reference **does not exist** inside a static context.
- There are no instance variables to read.

If you try to write `this.id` or access a non-static variable inside a static method, the Java compiler will immediately throw a compilation error:
> `non-static variable cannot be referenced from a static context`

A static method can only access:
1. Its own parameters (`double calculate(int a, int b)`).
2. Its own local variables declared inside the method body.
3. Other `static` methods or `static` constants (e.g. `Math.PI` or `AppConfig.SEARCH_MAX_RESULTS`).

---

### Question 4: What is a "Pure Function", and how does it relate to static methods?

**Answer:**
A **pure function** is a mathematical concept borrowed by computer science:
1. Given the exact same inputs, it **always returns the exact same output**.
2. It has **no side effects** (it does not modify any external variables, does not alter files on disk, does not change the database, and does not alter the caller's objects).

In MedFinder:
- `TextSimilarity.levenshtein(String a, String b)` is a **pure function**.
- `FreshnessClassifier.classify(long ageHours)` is a **pure function**.

In Java, pure functions are almost always implemented as `public static` methods because they depend solely on their parameters and produce no side effects.

---

### Question 5: Why should a class with only static methods have a `private` constructor?

**Answer:**
If you don't write a constructor in Java, the compiler automatically generates a `public` default no-argument constructor:
```java
// If you don't write a constructor, someone could accidentally do:
TextSimilarity ts = new TextSimilarity(); // Compiles, but is meaningless!
```

To prevent developers from accidentally instantiating a utility class that has no state, good OOP practice (Chapter 3 Encapsulation) adds a **`private` constructor**:

```java
public final class TextSimilarity {

    // Suppress default constructor for non-instantiability
    private TextSimilarity() {
        throw new UnsupportedOperationException("Utility class cannot be instantiated");
    }

    public static double relevance(String query, String target) { ... }
}
```
This guarantees that `TextSimilarity` can **only** be accessed via its static methods.

---

### Question 6: Doesn't having static methods violate Object-Oriented Programming (OOP)? When is it good vs. bad?

**Answer:**
Static methods do **not** violate OOP when used correctly, but they must be used for the right reasons:

* **Appropriate Use of Static Methods:**
  - **Mathematical & String Utilities:** `Math.min()`, `Integer.parseInt()`, `TextSimilarity.normalise()`.
  - **Factory Methods:** e.g., `AiOutcome.search(keywords, subCity)` (constructs an immutable object cleanly).
  - **Constants:** `public static final double FRESH_WEIGHT = 1.0;`.

* **Inappropriate / Anti-Pattern Use of Static Methods:**
  - Using static methods with **mutable static variables** (creating global state). This creates hidden dependencies and makes unit testing impossible.
  - Making business entities or services static (e.g. `PharmacyService.approve()` as static would prevent using interfaces, dependency injection, and polymorphism).

In MedFinder, **only stateless mathematical and string logic** (`medfinder.logic`) is static. Everything else (`Pharmacy`, `User`, `SearchService`, `FileUserRepository`) is strictly object-oriented with interfaces and instance encapsulation.

---

### Question 7: Concrete Code Example from MedFinder

Here is how `TextSimilarity` is designed and called in our project:

```java
package medfinder.logic;

public final class TextSimilarity {

    // 1. Private constructor prevents instantiation
    private TextSimilarity() { }

    // 2. Static method: called without an instance
    public static int levenshtein(String s1, String s2) {
        if (s1 == null || s2 == null) {
            throw new IllegalArgumentException("Strings cannot be null");
        }
        
        int[][] dp = new int[s1.length() + 1][s2.length() + 1];

        for (int i = 0; i <= s1.length(); i++) dp[i][0] = i;
        for (int j = 0; j <= s2.length(); j++) dp[0][j] = j;

        for (int i = 1; i <= s1.length(); i++) {
            for (int j = 1; j <= s2.length(); j++) {
                int cost = (s1.charAt(i - 1) == s2.charAt(j - 1)) ? 0 : 1;
                dp[i][j] = Math.min(
                    Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1),
                    dp[i - 1][j - 1] + cost
                );
            }
        }
        return dp[s1.length()][s2.length()];
    }
}
```

**How callers use it:**
```java
// In SearchService or LocalityService:
int distance = TextSimilarity.levenshtein("amoxcillin", "amoxicillin");
// Direct class call — zero object allocation!
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **What does `static` mean?** | Belongs to the class blueprint, not to individual objects on the heap. |
| **How is it called?** | Using `ClassName.methodName()`, without using `new`. |
| **Where is it in MedFinder?** | In `medfinder.logic` (`TextSimilarity`, `FreshnessClassifier`, `PasswordHasher`). |
| **Why not instance methods?** | These are pure, stateless algorithms. Creating objects for them would waste memory with zero benefit. |
| **Why private constructor?** | To enforce non-instantiability so nobody can do `new TextSimilarity()`. |
| **Can it access `this`?** | No, because no object exists when a static method is executed. |
