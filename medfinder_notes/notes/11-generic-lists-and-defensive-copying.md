# Course Concept: Generic `List<T>` Collections & Defensive Copying (Chapters 2 & 3)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Growable Lists (`List<T>`) vs. Fixed Arrays (`T[]`), Generic Type Safety, Never-Null Lists, and Defensive Copying  
> **Syllabus Reference:** Ch. 2.8 (Arrays & Memory Layout), Ch. 3.1 (Object References vs. Instances), Ch. 3.4 (Defensive Copying: Protecting Internal Mutable State), plus *Approved Beyond-Course Concept (Part 6.2)*  
> **Where in MedFinder:** `UserRepository.findAll()`, `PharmacyRepository.findByStatus(...)`, `MedicineRepository.findActive()`, `StockRepository.findByPharmacy(...)`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

1. **`List<T>` (Generic Collection):** Think of `List<User>` as a **resizable, type-safe array** that can hold only `User` objects. Unlike a plain array (`User[]`), a `List` grows automatically as new records are added.
2. **Defensive Copying (Ch. 3.4):** Returning a **fresh copy** of an internal `List` (e.g., `new ArrayList<>(internalList)`) instead of the repository's original list reference, so callers cannot accidentally mutate or erase the repository's private data.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why does `UserRepository.findAll()` return `List<User>` instead of a plain Java array `User[]`?

**Answer:**
Compare plain arrays (**Ch. 2.8**) with `List<T>` (*Approved Extension, Part 6.2*):
- **Fixed Array (`User[]`):** Once created on the heap (`new User[10]`), its length can **never change**. Every time a new pharmacist registers, you would have to manually allocate a larger array and copy every element with `System.arraycopy`.
- **Growable List (`List<User>`):** Backed by `ArrayList`, it automatically resizes behind the scenes as users, pharmacies, or stock records are inserted or deleted.
- **Notice:** Even here we program to an interface! We declare the return type as the interface **`List<User>`**, NOT the concrete class `ArrayList<User>` (**Ch. 4.6**).

---

### Question 2: What do the angle brackets `<User>` in `List<User>` mean?

**Answer:**
The `<User>` syntax is **Generics** (*Approved Extension, Part 6.2*). It tells the Java compiler:
> *"This list is strictly allowed to hold `User` objects (including subclasses like `Pharmacist` and `Administrator` via polymorphism, **Ch. 5.2**) — nothing else!"*

- **Without Generics (Old Java):** A raw `List` held generic `Object` references, forcing ugly and dangerous **downcasting** (`User u = (User) list.get(0);`), which risks a runtime `ClassCastException` (**Ch. 5.3 — Type Safety Hazards**).
- **With Generics (`List<User>`):** If someone tries to put a `Pharmacy` inside a `List<User>`, the compiler rejects it immediately—giving us **compile-time type safety** with zero manual downcasting!

---

### Question 3: What is "Defensive Copying" (Ch. 3.4), and what bug happens if we forget it?

**Answer:**
In Java, an `ArrayList` is a **mutable object on the Heap** (**Ch. 3.1**). Suppose `FileMedicineRepository` stores its loaded catalogue in a private field:
```java
private final List<Medicine> medicines = new ArrayList<>();
```

**BAD — Returning the internal reference directly (Breaks Encapsulation!):**
```java
public List<Medicine> findActive() {
    return this.medicines; // DANGER: Caller now shares the exact same heap object!
}
```
If a caller does:
```java
List<Medicine> list = medicineRepo.findActive();
list.clear(); // CATASTROPHE! Just wiped out the repository's private data in memory!
```

**GOOD — Returning a Defensive Copy (Ch. 3.4):**
```java
public List<Medicine> findActive() {
    List<Medicine> copy = new ArrayList<>();
    for (Medicine m : medicines) {
        if (m.isActive()) {
            copy.add(m);
        }
    }
    return copy; // Safe! Caller can sort or clear "copy" without touching "medicines"
}
```
Now, even if a caller sorts, removes from, or clears the returned list, the repository's internal `medicines` state stays 100% protected.

---

### Question 4: Why do MedFinder's list methods return an *empty list* instead of `null` when nothing matches?

**Answer:**
Look at the Javadoc across all your repositories:
- `UserRepository.findAll()`: `@return a copy of the list of all users; empty if there are none`
- `MedicineRepository.findActive()`: `@return a copy of the active medicines; empty if there are none`

If a method returns an empty list (`size() == 0`) instead of `null`, callers can safely loop over it with a `for-each` loop (**Ch. 2.8**) without needing an extra `if (list != null)` check:
```java
// Safe even when 0 active medicines exist — loop simply runs 0 times!
for (Medicine m : medicineRepo.findActive()) {
    // ...
}
```
Returning `null` for a list would immediately crash that loop with a `NullPointerException` (**Ch. 6.3**).

---

### Question 5: Concrete Code Example from MedFinder (`MedicineRepository.java`)

```java
package medfinder.repository;

import java.util.List;
import medfinder.model.Medicine;

public interface MedicineRepository {

    // Single entity lookup -> returns null if not found
    Medicine findById(int id);

    // Collection lookup -> NEVER returns null; returns a defensive copy (empty if none)
    List<Medicine> findActive();
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Why `List<T>` instead of `T[]`?** | Arrays have fixed size (**Ch. 2.8**); `List` grows dynamically as records are added. |
| **Why `<User>` generics?** | Enforces compile-time type safety and avoids manual downcasting / `ClassCastException` (**Ch. 5.3**). |
| **What is Defensive Copying?** | Returning a new copy of an internal mutable collection so callers cannot corrupt the object's private state (**Ch. 3.4**). |
| **Why never return `null` for a `List`?** | An empty list lets callers iterate safely without `NullPointerException` checks (**Ch. 6.3**). |
| **Why declare `List<User>` instead of `ArrayList<User>`?** | Programs to the `List` interface rather than a specific implementation (**Ch. 4.6**). |
