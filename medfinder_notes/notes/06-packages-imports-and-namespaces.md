# Course Concept: Packages, Imports & Architectural Modularity (Chapters 1 & 3)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Packages, Namespaces, Directory Hierarchies, `import` Statements, and Layered Architecture  
> **Syllabus Reference:** Ch. 1.3 (High Cohesion vs. Tight Coupling), Ch. 3.7 (Packages, Namespaces & Modularity)  
> **Where in MedFinder:** All files (`package medfinder;`, `package medfinder.repository;`, `import medfinder.model.User;`, etc.)  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

A **package** in Java is a named namespace that groups related classes and interfaces together.

- **Physical Rule:** Package names **must exactly match** the folder path on disk. For example, `package medfinder.repository;` **must** live inside `src/main/java/medfinder/repository/`.
- **Imports:** To use a class from another package (outside `java.lang`), you declare an `import` statement at the top of the file.
- **Architectural Benefit:** Packages let us enforce **high cohesion** (grouping files with one shared responsibility) and **low coupling** (controlling which layer is allowed to call which).

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: Why does Java use packages instead of putting all 57 MedFinder files into a single folder?

**Answer:**
Packages solve three critical software engineering problems (**Ch. 1.3 & Ch. 3.7**):
1. **Preventing Name Collisions (Namespaces):** Two different libraries can both have a class named `Location` or `Date` (e.g., `java.util.Date` vs. `java.sql.Date`). Packages give each class a unique fully qualified name (like `medfinder.model.Location`).
2. **Modularity & High Cohesion:** Related responsibilities stay together. Every storage contract lives in `medfinder.repository`; every data entity lives in `medfinder.model`; every custom error lives in `medfinder.exception`.
3. **Access Control & Layer Boundaries:** Java's package-private (default) and `protected` modifiers work across packages, and code reviewers can immediately spot illegal architectural dependencies just by reading the `import` lines at the top of a file!

---

### Question 2: What is the difference between built-in packages and user-defined packages?

**Answer:**
- **Standard Built-in Packages (Java Standard Library):** Provided by the JDK.
  - `java.lang`: Automatically imported into every Java file (`String`, `System`, `Math`, `RuntimeException`). You **never** need to write `import java.lang.String;`.
  - `java.util`: Collections and utilities (`List`, `ArrayList`, `Map`, `Scanner`, `Arrays`). Must be explicitly imported.
  - `java.nio.file` / `java.io`: File reading, writing, and `IOException`. Must be explicitly imported.
- **User-Defined Packages (MedFinder's packages):** Created by our team under the base package `medfinder`:
  - `medfinder` (root: `Main`, `AppContext`)
  - `medfinder.model` (entities & enums)
  - `medfinder.exception` (custom exceptions)
  - `medfinder.logic` (pure static calculations)
  - `medfinder.repository` (storage interfaces)
  - `medfinder.repository.file` (subpackage for CSV implementations)
  - `medfinder.service`, `medfinder.ai`, `medfinder.console`, `medfinder.config`

---

### Question 3: Why do we write explicit imports (`import medfinder.model.Pharmacy;`) instead of wildcard imports (`import medfinder.model.*;`)?

**Answer:**
Compare these two styles in `PharmacyRepository.java`:

```java
// GOOD: Explicit imports (used in MedFinder)
import medfinder.model.Pharmacy;
import medfinder.model.PharmacyStatus;

// AVOID: Wildcard import
import medfinder.model.*;
```

Explicit imports are better because:
1. **Transparency in Code Review:** A reviewer immediately sees the exact list of external types this file relies on.
2. **Avoids Ambiguity:** If two wildcard-imported packages both define a class with the same name, the compiler throws an ambiguity error.
3. **Zero Runtime Overhead:** Note that `import` is a **compile-time shortcut** only—it does not make the `.class` file larger or slower.

---

### Question 4: How do package imports enforce MedFinder's Architecture Rules?

**Answer:**
In MedFinder (Document 03, Section 4), every package has strict rules about which other packages it is allowed to import:

| Package | May Import | Forbidden to Import |
|---|---|---|
| `medfinder.model` | `medfinder.exception` | `service`, `repository`, `console`, `ai` |
| `medfinder.repository` | `medfinder.model`, `medfinder.exception` | `service`, `console`, `repository.file` |
| `medfinder.service` | `repository`, `logic`, `model`, `exception`, `config` | `console`, `repository.file` |
| `medfinder.console` | `service`, `ai`, `model`, `exception` | `repository`, `repository.file` |

Because of these rules, if P2 or P1 sees `import medfinder.repository.UserRepository;` inside a `console` menu class during a pull request review, they immediately know the layered architecture rule was violated!

---

### Question 5: Concrete Code Example from MedFinder (`PharmacyRepository.java`)

```java
// 1. Package declaration MUST be the very first non-comment statement in the file
package medfinder.repository;

// 2. Standard library import (outside java.lang)
import java.util.List;

// 3. Cross-package imports from our own project (allowed: repository -> model)
import medfinder.model.Pharmacy;
import medfinder.model.PharmacyStatus;

public interface PharmacyRepository {
    // Because Pharmacy and PharmacyStatus are imported, we write their short names:
    List<Pharmacy> findByStatus(PharmacyStatus status);
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **What is a `package`?** | A namespace organizing related classes that must match the directory hierarchy on disk (**Ch. 3.7**). |
| **Why don't we import `String` or `System`?** | Because they live in `java.lang`, which Java automatically imports into every file. |
| **Why explicit imports over `*`?** | Makes exact dependencies visible to reviewers and avoids class name ambiguity. |
| **What does `medfinder.repository.file` represent?** | A **subpackage** separating CSV file implementations from the pure storage contracts in `medfinder.repository`. |
| **How do packages improve architecture?** | They group cohesive classes together and let us verify low coupling across layers (**Ch. 1.3**). |
