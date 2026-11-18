# Course Concept: Primitive vs. Reference Types & `null` Semantics (Chapters 2 & 3)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Primitive Data Types, Reference Types, `null` References, Method Signatures (`void` vs. Return Types), and Descriptive Parameter Naming  
> **Syllabus Reference:** Ch. 2.3 (Primitive vs. Reference Types, Identifiers), Ch. 3.1 (Object References vs. Instances & `null`), Ch. 3.6 (Method Signatures & Return Types)  
> **Where in MedFinder:** `UserRepository.java`, `PharmacyRepository.java`, `MedicineRepository.java`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

Every variable, parameter, and return type in Java falls into one of two categories:

1. **Primitive Types** (`int`, `double`, `boolean`, `long`, `char`, etc.): Store the **actual raw value directly** in memory. They can **never** be `null`.
2. **Reference Types** (`User`, `Pharmacy`, `String`, `List<User>`, arrays): Store a **memory address (pointer)** referring to an object living on the **Heap**. A reference variable **can** hold `null`, meaning *"points to no object"*.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Compare the primitive and reference types used in `UserRepository.java`.

**Answer:**
Look at the method signatures in `UserRepository.java`:

```java
User findById(int id);       // Parameter: primitive int  | Return: reference User (or null)
User findByEmail(String email); // Parameter: reference String | Return: reference User (or null)
void save(User user);        // Parameter: reference User | Return: void (nothing)
int nextId();                // Parameter: none           | Return: primitive int (never null!)
```

- **`int id` and `int nextId()` (Primitives — Ch. 2.3):** A 32-bit integer value stored directly on the stack. `nextId()` is guaranteed to return a real number (like `1`, `2`, `3`); it can never return `null`.
- **`User` and `String` (References — Ch. 3.1):** Variables pointing to objects on the heap. Because `User` is a reference type, `findById(int id)` is legally allowed to return `null` if no matching user exists.
- **`void` (No Return Value — Ch. 3.6):** Used on `save(User user)` because saving is a command/action, not a query that computes an answer.

---

### Question 2: Why does `findById(int id)` return `null` instead of throwing a `NotFoundException`?

**Answer:**
This is a deliberate design distinction between **normal lookup outcomes** and **exceptional errors** (**Ch. 3.1 & Ch. 6.1**):
- Asking *"Does a user with email `abc@example.com` exist?"* has two completely normal answers: **Yes (here is the `User`)** or **No (`null`)**.
- Consider registration vs. login:
  - During **login**, `findByEmail` returning `null` means invalid credentials.
  - During **registration**, `findByEmail` returning `null` is actually **good news**—it means the email is available and not taken!
- If the repository threw `NotFoundException`, registration would have to catch an exception just to confirm an email is free (an anti-pattern in **Ch. 6.6: flow-control via exceptions**).
- Therefore, repositories return `null`, and the **Service layer** decides whether `null` is acceptable or should become a `NotFoundException`.

---

### Question 3: What happens if a caller forgets to check for `null`?

**Answer:**
If a method returns `null` and the caller immediately tries to call a method on it using the dot operator (`.`):
```java
User u = userRepo.findById(999); // returns null
String name = u.getFullName();   // CRASH! NullPointerException
```
The JVM throws an unchecked **`NullPointerException`** (**Ch. 6.3**), because you tried to follow a reference pointing to nothing.

That is why MedFinder enforces two clear conventions:
1. Javadoc **explicitly warns callers**: `@return the user, or null if there is none with that id`.
2. Callers always guard single-entity lookups with `if (u == null) { ... }`.

---

### Question 4: Why does `PharmacyRepository` distinguish `findById(int id)` vs. `findByOwner(int ownerUserId)`?

**Answer:**
Both methods accept a primitive `int` (**Ch. 2.3**), so the compiler sees both parameters as identical integers:
```java
Pharmacy findById(int id);
Pharmacy findByOwner(int ownerUserId);
```
1. **Different Method Names:** In Java (**Ch. 3.6**), two methods in the same interface cannot have the same name and the exact same parameter type list (`findById(int)` and `findById(int)` would not compile).
2. **Self-Documenting Identifiers (Ch. 2.3):** Naming the parameter `ownerUserId` clarifies *whose* ID must be passed (the pharmacist's `User` ID, not the `Pharmacy` ID).
3. **Domain Rule Reflected in Return Type:** Because each pharmacist owns **at most one pharmacy** (SRS), `findByOwner` returns a single `Pharmacy` (or `null`), rather than a `List<Pharmacy>`.

---

### Question 5: Concrete Code Example from MedFinder (`PharmacyRepository.java`)

```java
public interface PharmacyRepository {

    // Primitive int input -> Reference Pharmacy output (or null if missing)
    Pharmacy findById(int id);

    // Clear identifier tells caller to pass the User ID, not Pharmacy ID
    Pharmacy findByOwner(int ownerUserId);

    // Action method returning nothing (void)
    void save(Pharmacy pharmacy);

    // Always returns a primitive integer >= 1 (cannot be null)
    int nextId();
}
```

**How a Service safely handles the `null` contract:**
```java
Pharmacy pharmacy = pharmacyRepo.findByOwner(currentUserId);
if (pharmacy == null) {
    throw new NotFoundException("You have not registered a pharmacy yet.");
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Primitive vs. Reference type?** | Primitives (`int`, `boolean`) hold raw values directly and cannot be `null`; references (`User`, `String`) hold addresses to heap objects and can be `null` (**Ch. 2.3, 3.1**). |
| **Why return `null` on `findById` instead of throwing?** | "Not found" is a normal lookup result (e.g., checking if an email is free). The Service layer decides whether to throw `NotFoundException` (**Ch. 6.1, 6.6**). |
| **What does `void` mean on `save(...)`?** | The method executes an action (persisting data) and returns no value (**Ch. 3.6**). |
| **What does `nextId()` return when storage is empty?** | Primitive `int` value `1` (largest existing ID + 1). |
| **Why name the parameter `ownerUserId`?** | Clear identifiers prevent passing a pharmacy ID by mistake when both are `int` (**Ch. 2.3**). |
