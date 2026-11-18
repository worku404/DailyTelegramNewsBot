# Course Concept: Abstraction, Interfaces & Loose Coupling (Chapters 1, 4 & 5)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Abstraction, Interface Contracts (`public interface`), Implicit Modifiers, Low Coupling, and Open-Closed Principle (OCP)  
> **Syllabus Reference:** Ch. 1.3 (High Cohesion vs. Tight Coupling), Ch. 1.4 (Abstraction: Separating Interface from Implementation), Ch. 4.6 (Interfaces & Contract Architecture), Ch. 5.1–5.2 (Polymorphism & OCP)  
> **Where in MedFinder:** `UserRepository`, `PharmacyRepository`, `MedicineRepository`, `StockRepository`, `LocalityRepository`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

An **interface** in Java is a **pure contract**: it specifies **WHAT** operations an object must support, without saying **HOW** those operations are implemented internally.

- You declare it with `public interface Name { ... }`.
- Traditional interface methods have **no body** (they end with `;` instead of `{ ... }`) and are **implicitly `public abstract`**.
- **Golden Rule of OOP Architecture:** *Program to an interface, not to an implementation.* Services depend on `UserRepository` (the contract), NOT `FileUserRepository` (the CSV file details).

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why do MedFinder's services depend on `UserRepository` (an interface) instead of `FileUserRepository` (a concrete class)?

**Answer:**
This is **Abstraction (Ch. 1.4)** and **Loose Coupling (Ch. 1.3)** in action:
1. **Replaceable Storage (Open-Closed Principle — Ch. 5.2):** Right now, MedFinder saves users in a CSV file (`FileUserRepository`). Tomorrow, if we upgrade to a SQL database (`SqlUserRepository`), we just write a new class that `implements UserRepository` and wire it in `AppContext`. **Zero lines of code change inside `AuthService` or any menu!**
2. **Easy Testing with Substitutes:** During automated tests, we can pass a lightweight fake/in-memory implementation of `UserRepository` instead of touching real files on disk.
3. **Parallel Teamwork:** Because P1 published the 5 repository interfaces on 15 Nov (Task T06), P3 Wubet could immediately write `AuthService` against `UserRepository` *before* the CSV file code even existed!

```
          ┌───────────────────────────────┐
          │       AuthService (P3)        │
          │  (only knows the interface!)  │
          └───────────────┬───────────────┘
                          │ depends on
                          ▼
          ┌───────────────────────────────┐
          │  «interface» UserRepository   │  <-- Fixed contract (T06)
          └───────────────▲───────────────┘
                          │ implements
            ┌─────────────┴─────────────┐
            │                           │
┌───────────────────────┐   ┌───────────────────────┐
│  FileUserRepository   │   │   SqlUserRepository   │
│  (CSV file storage)   │   │  (Future DB storage)  │
└───────────────────────┘   └───────────────────────┘
```

---

### Question 2: Why don't we write `public abstract` in front of methods inside an interface?

**Answer:**
In Java (**Ch. 4.6 — Traditional Interface Members**):
- Every normal method inside an interface is **automatically (implicitly) `public abstract`**.
- Writing:
  ```java
  User findById(int id);
  ```
  is 100% identical to writing:
  ```java
  public abstract User findById(int id);
  ```
- Leaving out redundant `public abstract` keywords keeps interfaces clean, concise, and idiomatic Java.
- Similarly, any field declared inside an interface is implicitly `public static final` (a constant).

---

### Question 3: Can you instantiate an interface using `new UserRepository()`? Why or why not?

**Answer:**
**No!** Writing `new UserRepository()` causes a compile-time error.
- An interface has no constructor, no instance fields, and no method bodies—it is only a blueprint of *promises*.
- However, you **can** declare a variable whose **reference type** is the interface, pointing to an instance of a concrete class that implements it (**Ch. 5.1 — Polymorphic References**):
  ```java
  // Valid! Polymorphic reference:
  UserRepository repo = new FileUserRepository(path, csvFile);
  ```
- At runtime, when you call `repo.findById(1)`, Java uses **Dynamic Method Dispatch (Late Binding, Ch. 5.1)** to execute `FileUserRepository`'s version of `findById`.

---

### Question 4: How is an Interface different from an Abstract Class (Ch. 4.5 vs. Ch. 4.6)?

**Answer:**

| Feature | Abstract Class (`abstract class`) | Interface (`interface`) |
|---|---|---|
| **Purpose** | Shares common code & state among closely related classes ("IS-A" hierarchy, e.g., `Menu` → `StartMenu`, `User` → `Pharmacist`). | Defines a capability or contract ("CAN-DO" / role, e.g., `UserRepository`, `RowMapper<T>`). |
| **Instance Fields / State** | Yes (can hold `private`/`protected` fields). | No instance fields (only `public static final` constants). |
| **Constructors** | Yes (called via `super(...)`). | No constructors. |
| **Multiple Inheritance** | A class can `extends` only **one** superclass. | A class can `implements` **many** interfaces (e.g., `FileUserRepository implements UserRepository, RowMapper<User>`). |

---

### Question 5: Concrete Code Example from MedFinder (`UserRepository.java`)

```java
package medfinder.repository;

import java.util.List;
import medfinder.model.User;

public interface UserRepository {

    // All five methods are implicitly "public abstract" — no { } body!
    User findById(int id);

    User findByEmail(String email);

    List<User> findAll();

    void save(User user);

    int nextId();
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **What is an interface?** | A contract defining *what* operations exist without exposing *how* they are implemented (**Ch. 1.4, 4.6**). |
| **Why do services take `UserRepository` instead of `FileUserRepository`?** | Loose coupling (**Ch. 1.3**) and Open-Closed Principle (**Ch. 5.2**): storage can switch from CSV to a database without touching any service or menu. |
| **What modifiers are implicit on interface methods?** | `public` and `abstract` (**Ch. 4.6**). |
| **Can you do `new UserRepository()`?** | No, interfaces cannot be instantiated directly; you hold a polymorphic interface reference pointing to an implementing class (**Ch. 5.1**). |
| **How did T06 help the team?** | Publishing interfaces early unblocked P3 (`AuthService`) and P5 (`FileXRepository`) to work in parallel. |
