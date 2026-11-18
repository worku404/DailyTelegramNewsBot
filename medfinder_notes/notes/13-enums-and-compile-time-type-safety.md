# Course Concept: Enums & Compile-Time Type Safety (Chapters 3 & 4 + Approved Extension)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Enumerations (`enum`), Fixed Sets of Constants, Compile-Time Type Safety vs. Raw `String` Parameters  
> **Syllabus Reference:** Ch. 3.4 (Invariant Protection & Encapsulation), Ch. 4.4 (`final` Classes & Constants conceptually), plus *Approved Beyond-Course Concept (Part 6.2)*  
> **Where in MedFinder:** `medfinder.model.PharmacyStatus` used in `PharmacyRepository.findByStatus(PharmacyStatus status)` (also `Role`, `Freshness`, `MatchLevel`)  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

An **`enum`** (enumeration) is a special Java type that represents a **fixed, closed set of named constant values**—for example, a pharmacy can ONLY ever be `PENDING`, `VERIFIED`, or `REJECTED`.

- Think of an `enum` as a **`final` class with a `private` constructor and a fixed list of `public static final` instances** (**Ch. 3.4 & 4.4**).
- Using an `enum` instead of a plain `String` gives you **compile-time type safety**: invalid values or spelling typos become impossible to compile!

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why does `PharmacyRepository.findByStatus` accept a `PharmacyStatus` enum instead of a `String`?

**Answer:**
Compare the two designs:

**BAD — Using a raw `String`:**
```java
List<Pharmacy> findByStatus(String status);

// Bug 1: Spelling typo compiles without warning, fails silently at runtime!
List<Pharmacy> list1 = repo.findByStatus("Verifed");

// Bug 2: Wrong domain term compiles without warning!
List<Pharmacy> list2 = repo.findByStatus("APPROVED");
```

**GOOD — Using the `PharmacyStatus` enum (MedFinder's actual code):**
```java
List<Pharmacy> findByStatus(PharmacyStatus status);

// Only the exact three valid values are legally accepted by javac:
List<Pharmacy> pending  = repo.findByStatus(PharmacyStatus.PENDING);
List<Pharmacy> verified = repo.findByStatus(PharmacyStatus.VERIFIED);
List<Pharmacy> rejected = repo.findByStatus(PharmacyStatus.REJECTED);

// repo.findByStatus(PharmacyStatus.APPROVED); -> COMPILE ERROR immediately!
```

By using `PharmacyStatus`, **entire categories of runtime bugs are eliminated at compile time**.

---

### Question 2: How does an `enum` with fields and a constructor work in Java?

**Answer:**
In Java, an `enum` is much more powerful than a simple integer list—it is a real class that can hold `private final` fields, a constructor, and getter methods! Look at P4 Tesnim's real [PharmacyStatus.java](file:///c:/class/OOP/groupProject/MedFinder-java/src/main/java/medfinder/model/PharmacyStatus.java):

```java
package medfinder.model;

/** The review state of a pharmacy (SRS BR-11). */
public enum PharmacyStatus {
    // 1. The three fixed constant instances (each invokes the constructor below)
    PENDING("Pending"),
    VERIFIED("Verified"),
    REJECTED("Rejected");

    // 2. Private final field storing the human-friendly display label (Ch. 3.4 & 4.4)
    private final String label;

    // 3. Constructor (implicitly private — nobody outside can call "new PharmacyStatus()")
    PharmacyStatus(String label) {
        this.label = label;
    }

    // 4. Getter method returning the display label
    public String label() {
        return label;
    }
}
```

- Notice that the constructor is **implicitly `private`**: no code anywhere in the program can ever create a fourth `PharmacyStatus`.
- Because `label` is **`private final`** (**Ch. 4.4**), once created it is completely **immutable**.

---

### Question 3: How can you compare two `enum` values safely?

**Answer:**
Unlike `String` (where you must use `.equals()`), `enum` constants are **guaranteed singletons**—there is literally only ONE `PharmacyStatus.VERIFIED` object in the entire JVM!
- Therefore, comparing enums with **`==`** is **both valid and preferred** (it is faster and `null`-safe—never throws `NullPointerException` even if one side is `null`):
  ```java
  if (pharmacy.getStatus() == PharmacyStatus.VERIFIED) {
      // Safe even if getStatus() were somehow null!
  }
  ```
- Enums also work seamlessly in classic **`switch` statements** (**Ch. 2.5**), such as `switch (user.role())` in `StartMenu`.

---

### Question 4: Where are enums used across MedFinder, and why are they on the "Approved Beyond-Course" list?

**Answer:**
In MedFinder (Document 02 Section 15.3 & `AGENTS-P1-worku.md` Part 6.2), enums are an approved extension outside Chapters 1–6 because they make domain invariants crystal clear:
1. `PharmacyStatus`: `PENDING`, `VERIFIED`, `REJECTED` (used in `PharmacyRepository.findByStatus`)
2. `Role`: `PHARMACIST`, `ADMIN` (used in `User` hierarchy and `StartMenu` routing)
3. `Freshness`: `FRESH`, `AGING`, `STALE` (used in `FreshnessClassifier` and `SearchResult`)
4. `MatchLevel`: `SAME_DISTRICT`, `OTHER_AREA` (used in `Location` and `SearchService`)
5. `AiOutcome.Kind`: `SEARCH`, `UNSUPPORTED`, `FALLBACK` (the only nested enum allowed, inside `AiOutcome`)

---

### Question 5: Concrete Code Example from MedFinder (`PharmacyRepository.java`)

```java
package medfinder.repository;

import java.util.List;
import medfinder.model.Pharmacy;
import medfinder.model.PharmacyStatus;

public interface PharmacyRepository {

    /**
     * Lists the pharmacies that have a given status.
     *
     * @param status the status to match
     * @return a copy of the matching pharmacies; empty if there are none
     */
    List<Pharmacy> findByStatus(PharmacyStatus status);
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **What is an `enum`?** | A fixed, closed set of constant object instances—conceptually like a `final` class with a private constructor (**Part 6.2, Ch. 4.4**). |
| **Why `PharmacyStatus` instead of `String`?** | Compile-time type safety: typos like `"Verifed"` cannot even compile. |
| **Can anyone create a new `PharmacyStatus` with `new`?** | No, enum constructors are implicitly `private`. |
| **Can you compare enums with `==`?** | Yes! Each enum constant is a single unique instance in the JVM, making `==` safe and null-proof. |
| **What does `PharmacyStatus.PENDING.label()` return?** | The formatted display text `"Pending"` stored in its `private final String label` field. |
