# Course Concept: Read-Only Abstraction & Encapsulation Guardrails (Chapters 1, 3 & 4)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Read-Only Interfaces, Information Hiding, Encapsulation & Invariant Enforcement  
> **Syllabus Reference:** Ch. 1.4 (Abstraction & Information Hiding), Ch. 3.4 (Encapsulation & Invariant Protection), Ch. 4.6 (Interfaces & Contract Architecture)  
> **Where in MedFinder:** `medfinder.repository.MedicineRepository` and `medfinder.repository.LocalityRepository` (compared to `UserRepository` & `PharmacyRepository`)  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

Good **Abstraction (Ch. 1.4)** is not just about what methods you *include* in an interface—it is equally about what methods you **intentionally leave out**.

By giving `MedicineRepository` **only read methods** (`findById` and `findActive`) and omitting `save()`, `delete()`, and `nextId()`, the Java compiler itself guarantees that **no service or menu can ever modify or corrupt the medicine catalogue**.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why does `MedicineRepository` have only 2 methods, while `UserRepository` has 5 and `PharmacyRepository` has 6?

**Answer:**
Compare the business rules (SRS) of each entity in MedFinder:

| Repository | Operations Allowed | Why? |
|---|---|---|
| `UserRepository` | `findById`, `findByEmail`, `findAll`, **`save`**, **`nextId`** | New pharmacists register at runtime → **Read + Write** |
| `PharmacyRepository` | `findById`, `findByOwner`, `findByLicence`, `findByStatus`, **`save`**, **`nextId`** | Pharmacists register/edit pharmacies; admins approve/reject → **Read + Write** |
| `MedicineRepository` | `findById`, `findActive` *(no `save`, no `delete`, no `nextId`!)* | The medicine catalogue (`medicines.csv`) is fixed reference data → **Read-Only** |

Because MedFinder has **no feature** to add, rename, or delete medicines from the console, exposing a `save(Medicine)` method would be an unnecessary risk. Leaving it out enforces the business rule at compile time!

---

### Question 2: How does a Read-Only Interface demonstrate Encapsulation and Information Hiding (Ch. 1.4 & Ch. 3.4)?

**Answer:**
- **Information Hiding (Ch. 1.4):** A caller like `SearchService` only needs to ask *"Which medicines are active?"* It does not need to know how `medicines.csv` is loaded, stored, or parsed—and it has zero access to any mutating operations.
- **Invariant Protection (Ch. 3.4):** An *invariant* is a rule that must always stay true while the program runs (here: *"the master medicine catalogue never changes during runtime"*). Because `MedicineRepository` has no mutator methods **and** returns defensive copies from `findActive()`, this invariant cannot be violated anywhere in the service or console layers.

---

### Question 3: Why does `MedicineRepository` have `findActive()` instead of `findAll()`?

**Answer:**
Look at the domain requirement in MedFinder's High-Level Design (HLD 4.9 & 7.3):
- A medicine record in `medicines.csv` has an `active` boolean flag (e.g., discontinued medicines may be marked `false` while old stock history still references their ID).
- **`findById(int id)`** can look up any medicine by ID (even if needed for historical records).
- **`findActive()`** returns **only active medicines** so `SearchService` and `CatalogueService` never show discontinued medicines to customers.
- Putting that filtering behind the `findActive()` contract keeps callers simpler and prevents them from forgetting to filter inactive medicines!

---

### Question 4: Why does `MedicineRepository`'s Javadoc say *"when the underlying storage cannot be read"* instead of *"read or written"*?

**Answer:**
Attention to detail in documentation reflects accurate design:
- `UserRepository` Javadoc: *"when the underlying storage cannot be **read or written**."*
- `MedicineRepository` Javadoc: *"when the underlying storage cannot be **read**."*

Since `MedicineRepository` never writes to disk, it can only encounter read failures when loading `medicines.csv`.

---

### Question 5: Concrete Code Example from MedFinder (`MedicineRepository.java`)

```java
package medfinder.repository;

import java.util.List;
import medfinder.model.Medicine;

/**
 * Storage contract for the medicine catalogue (read only).
 *
 * <p>Every operation throws the unchecked {@code DataStorageException}
 * when the underlying storage cannot be read.
 */
public interface MedicineRepository {

    /**
     * Finds a medicine by id.
     *
     * @param id the medicine id
     * @return the medicine, or null if there is none with that id
     */
    Medicine findById(int id);

    /**
     * Lists the medicines that are active in the catalogue.
     *
     * @return a copy of the active medicines; empty if there are none
     */
    List<Medicine> findActive();

    // Intentionally NO save(), delete(), or nextId() — enforces read-only invariant!
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Why is `MedicineRepository` read-only?** | The medicine catalogue is fixed reference data; omitting `save`/`delete`/`nextId` enforces this business rule at compile time (**Ch. 1.4, 3.4, 4.6**). |
| **What OOP principle does omitting methods demonstrate?** | **Information Hiding & Invariant Protection** (only expose the minimal contract callers genuinely need). |
| **Why `findActive()` instead of `findAll()`?** | Ensures searches and catalogue listings only ever display active medicines, preventing discontinued drugs from appearing. |
| **Can `SearchService` accidentally erase a medicine?** | No—not through the interface (no mutators) and not through the returned list (defensive copy, **Ch. 3.4**). |
