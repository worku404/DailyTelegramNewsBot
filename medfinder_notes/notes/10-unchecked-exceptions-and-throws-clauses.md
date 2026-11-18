# Course Concept: Checked vs. Unchecked Exceptions & `throws` Clauses (Chapter 6)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** The `Throwable` Hierarchy, Checked vs. Unchecked Exceptions, Stack Unwinding, Exception Translation, and `throws` Clauses  
> **Syllabus Reference:** Ch. 6.1 (Principles of Exception Handling), Ch. 6.2 (Throwable Hierarchy), Ch. 6.3 (Checked vs. Unchecked Exceptions), Ch. 6.4 (`throws` & Stack Unwinding), Ch. 6.6 (Custom Domain Exceptions & Exception Translation)  
> **Where in MedFinder:** `DataStorageException`, `MedFinderException`, all 5 repository interfaces (`UserRepository`, `PharmacyRepository`, `MedicineRepository`, `StockRepository`, `LocalityRepository`)  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

In Java, all errors and exceptions inherit from `java.lang.Throwable`. The most important distinction for developers is between **Checked** and **Unchecked** exceptions:

- **Checked Exceptions** (e.g., `IOException`): Enforced by the compiler (`javac`). Every method that might trigger one **must** either `catch` it or declare `throws IOException` in its method signature.
- **Unchecked Exceptions** (subclasses of `RuntimeException`, e.g., `DataStorageException`, `NullPointerException`): **Not** enforced by the compiler. They do **not** require a `throws` clause and propagate automatically up the call stack until caught at a central handler.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why does `UserRepository` mention `DataStorageException` in Javadoc, yet NONE of its methods have a `throws DataStorageException` clause?

**Answer:**
Because in MedFinder, `MedFinderException` extends **`RuntimeException`** (making `DataStorageException` an **unchecked exception**, **Ch. 6.3**):

```
java.lang.Throwable
  └── java.lang.Exception
        ├── java.io.IOException          <-- CHECKED (must declare "throws" or catch)
        └── java.lang.RuntimeException   <-- UNCHECKED (no "throws" clause needed)
              └── MedFinderException
                    ├── DataStorageException
                    ├── ValidationException
                    ├── AuthorizationException
                    └── NotFoundException
```

- Because `DataStorageException` is unchecked, callers (`AuthService`, `SearchService`, etc.) are **not forced** to write boilerplate `try/catch` blocks or clutter every method header with `throws DataStorageException`.
- Instead, we document it clearly in the interface's **Javadoc** so callers know it can happen if disk I/O fails.

---

### Question 2: What happens if a hard disk error occurs while reading `users.csv`? (Exception Translation & Stack Unwinding)

**Answer:**
This combines two Chapter 6 concepts: **Exception Translation (Ch. 6.6)** and **Stack Unwinding (Ch. 6.4)**:

1. **Low-Level Checked Failure:** Inside `CsvFile` (Task T07), reading a broken or locked file throws Java's built-in **checked** `IOException`.
2. **Translation at the Boundary (Ch. 6.6):** `FileUserRepository` catches that `IOException` and wraps it into our **unchecked** domain exception—preserving the original root cause (**Exception Chaining**):
   ```java
   try {
       return csvFile.readAll(path);
   } catch (IOException e) {
       throw new DataStorageException("Could not read users.csv", e);
   }
   ```
3. **Stack Unwinding (Ch. 6.4):** `DataStorageException` automatically unwinds (bubbles up) through `AuthService` straight to `Menu.run()`, which catches `MedFinderException` in **one central place** and prints a clean error message to the user!

---

### Question 3: Why shouldn't `UserRepository` declare `throws IOException` directly?

**Answer:**
Declaring `throws IOException` on the interface would **leak an implementation detail** into the abstraction (**Ch. 1.4 & Ch. 6.6**):
- `IOException` specifically means a file or network I/O error.
- What if we later implement `UserRepository` using a SQL database (which throws `SQLException`, not `IOException`)? The interface signature would no longer fit!
- By using our own storage-neutral `DataStorageException`, the interface stays 100% independent of whether storage is CSV files, SQL, or cloud storage.

---

### Question 4: What is the difference between `throw` and `throws`?

**Answer:**
Students frequently mix these two keywords up (**Ch. 6.4**):
- **`throw` (verb, inside a method body):** Actively creates and launches one specific exception object right now:
  ```java
  throw new DataStorageException("Failed to write file", cause);
  ```
- **`throws` (declaration, on a method header):** Warns callers that this method *might* pass a checked exception upward instead of catching it:
  ```java
  public List<Map<String, String>> readAll(Path path) throws IOException
  ```

---

### Question 5: Concrete Code Example from MedFinder (`UserRepository.java`)

```java
/**
 * Storage contract for user accounts (pharmacists and the administrator).
 *
 * <p>Every operation throws the unchecked {@code DataStorageException}
 * when the underlying storage cannot be read or written.
 */
public interface UserRepository {

    // Notice: NO "throws DataStorageException" and NO "throws IOException"!
    User findById(int id);

    void save(User user);
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Checked vs. Unchecked?** | Checked (`IOException`) must be caught or declared with `throws`; unchecked (`RuntimeException` subclasses) do not require `throws` (**Ch. 6.3**). |
| **Why no `throws DataStorageException`?** | Because `DataStorageException` extends `MedFinderException` → `RuntimeException` (unchecked), keeping service signatures clean. |
| **Why not `throws IOException` on repositories?** | That would leak CSV file details into the abstract interface; instead, `FileXRepository` translates `IOException` into `DataStorageException` (**Ch. 6.6**). |
| **What happens when `DataStorageException` is thrown?** | Stack unwinding (**Ch. 6.4**) propagates it straight to `Menu.run()`, where it is caught centrally. |
| **What is Exception Chaining?** | Passing the original `IOException` as the `cause` parameter into `new DataStorageException(msg, cause)` so diagnostic details are never lost (**Ch. 6.6**). |
