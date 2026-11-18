# Course Concept: `String` Immutability & Normalization Contracts (Chapter 2)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** The `String` Class, Immutability, String Constant Pool, `==` vs. `.equals()` vs. `.equalsIgnoreCase()`, and Behavioral Search Contracts  
> **Syllabus Reference:** Ch. 2.7 (Strings & Character Data: Immutability, SCP, Common String Operations)  
> **Where in MedFinder:** `UserRepository.findByEmail(String email)`, `PharmacyRepository.findByLicence(String licenceNumber)`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

In Java, `String` is **not a primitive type**—it is an **immutable reference class** (`java.lang.String`).

- **Immutable** means once a `String` object is created in memory, its characters can **never be changed**. Methods like `.toLowerCase()`, `.trim()`, or `.replace(...)` always return a **brand-new `String` object**.
- **Never compare Strings with `==`!** `==` checks whether two variables point to the same memory address; `.equals()` and `.equalsIgnoreCase()` compare the actual text characters.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why must you NEVER use `==` to compare two `String` values in Java?

**Answer:**
Because `String` is a **reference type** (**Ch. 2.7 & Ch. 3.1**):
- **`a == b`** compares **memory addresses** (do `a` and `b` refer to the exact same object in memory?).
- **`a.equals(b)`** compares **character contents** (do `a` and `b` spell the exact same text?).

```java
String fromCsv = new String("admin@medfinder.et");
String typedByUser = "admin@medfinder.et";

System.out.println(fromCsv == typedByUser);               // FALSE! Different objects on Heap vs. SCP
System.out.println(fromCsv.equals(typedByUser));          // TRUE! Same characters
System.out.println(fromCsv.equalsIgnoreCase("ADMIN@MEDFINDER.ET")); // TRUE! Ignores case
```

---

### Question 2: What is the String Constant Pool (SCP) and why is `String` immutable?

**Answer:**
According to **Ch. 2.7**:
- **String Constant Pool (SCP):** A special area of heap memory where Java stores string literals (like `"Pending"` or `"admin@medfinder.et"`). If two parts of your program use the same literal, Java reuses the single pooled copy (**memory deduplication**).
- **Why Immutability Matters:** Because multiple variables can safely share the same `String` object in the SCP, changing one variable's string could corrupt another if strings were mutable. Immutability guarantees thread-safety, security (e.g., emails, file paths, licence numbers cannot be silently altered after validation), and safe sharing.

---

### Question 3: Explain the two different String search rules in your Task T06 repository interfaces.

**Answer:**
Even though interfaces contain no implementation code, their Javadoc specifies exact **String normalization contracts** that every implementing class must obey:

1. **`UserRepository.findByEmail(String email)`** — *"ignoring upper/lower case"*:
   - If a user registered as `"Worku@MedFinder.et"` and logs in typing `"worku@medfinder.et"`, they must match!
   - Implementation uses **Ch. 2.7**: `user.getEmail().equalsIgnoreCase(email.trim())`.

2. **`PharmacyRepository.findByLicence(String licenceNumber)`** — *"ignoring upper/lower case and spaces"*:
   - Real-world Ethiopian pharmacy licences may be typed with or without spaces or different casing (e.g., `"AA-102 45"` vs. `"aa-10245"`).
   - If we didn't ignore spaces and case, a pharmacist could accidentally register the same licence twice!
   - Implementation normalizes both strings using **Ch. 2.7** operations before comparing:
     ```java
     String normalizedTarget = licenceNumber.replace(" ", "").toLowerCase();
     String normalizedStored = pharmacy.getLicenceNumber().replace(" ", "").toLowerCase();
     if (normalizedStored.equals(normalizedTarget)) {
         return pharmacy;
     }
     ```
   - Notice: `.replace(" ", "")` does **not** alter the original `licenceNumber` string—because `String` is immutable, it creates and returns a new normalized string!

---

### Question 4: Why does `String` immutability matter when joining many strings in a loop (like in `CsvFile`)?

**Answer:**
Because `String` is immutable (**Ch. 2.7**):
- Writing `result = result + column + ",";` inside a loop allocates a brand-new `String` object on every iteration, copying all previous characters again and again ($O(n^2)$ memory churn).
- That is why MedFinder uses **`StringBuilder`** (a mutable character buffer, **Ch. 2.7**) inside `CsvFile` and `PromptBuilder` when assembling lines from many pieces, then converts it once via `.toString()`.

---

### Question 5: Concrete Code Examples from MedFinder (`UserRepository.java` & `PharmacyRepository.java`)

```java
// In UserRepository.java:
/**
 * Finds a user by e-mail address, ignoring upper/lower case.
 *
 * @param email the e-mail address to look for
 * @return the user, or null if there is none with that e-mail
 */
User findByEmail(String email);

// In PharmacyRepository.java:
/**
 * Finds a pharmacy by licence number, ignoring upper/lower case and spaces.
 *
 * @param licenceNumber the licence number to look for
 * @return the pharmacy, or null if no pharmacy has that licence
 */
Pharmacy findByLicence(String licenceNumber);
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Is `String` primitive or reference?** | Reference class (`java.lang.String`), immutable by design (**Ch. 2.7**). |
| **Why `.equals()` instead of `==`?** | `==` compares memory addresses; `.equals()` / `.equalsIgnoreCase()` compare actual text characters (**Ch. 2.7**). |
| **What does immutability mean?** | Methods like `.toLowerCase()` or `.replace()` never mutate the original `String`; they return a new `String` object. |
| **How does `findByEmail` match?** | Case-insensitively (`equalsIgnoreCase`). |
| **How does `findByLicence` match?** | Ignores both case and spaces so `"AA 123"` and `"aa123"` are recognized as the same licence. |
