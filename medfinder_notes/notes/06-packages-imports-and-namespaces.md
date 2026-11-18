# Packages, Imports, and Namespaces (Chapters 1 & 3)

> **Chapter:** 1.3 Software Architecture — High Cohesion vs. Tight Coupling, 3.7 Packages, Namespaces & Modularity | **In MedFinder:** All source files (`package medfinder;`, `package medfinder.repository;`, `package medfinder.repository.file;`, etc.) | **Source:** MedFinder core foundation

## What is it?

A **package** in Java is a named namespace that groups related classes together and matches the exact folder structure on disk. If a file declares `package medfinder.repository;`, it must physically live at `src/main/java/medfinder/repository/`. The two things — declaration and folder — must always agree.

Think of it like labeled departments in a hospital. Cardiology files stay in Cardiology (`medfinder.model`), storage records stay in Medical Records (`medfinder.repository`), and the front desk stays in Reception (`medfinder.console`). When one department needs a form from another, it declares an explicit `import` at the top of the file — like filing a formal inter-department request.

## Why do we need it?

Imagine all 57 MedFinder classes dumped into one unnamed default package. There's no folder structure, no boundaries. A console menu class could reach directly into the CSV file parsers, completely skipping `AuthService`'s validation rules — and nobody would even notice until something breaks in production. Meanwhile, if two different packages (say, our code and a library) both define a class called `Date`, the compiler has no way to tell them apart. Packages solve both problems: they give every class a unique full name, and they let us draw hard architectural lines between layers.

## How it works

1. The first non-comment line in every `.java` file is the `package` declaration. It tells the compiler which namespace this class belongs to.
2. The declared package name must exactly match the folder path under `src/main/java/`. A mismatch causes a compile or class-loading error.
3. Everything in `java.lang` (like `String`, `System`, `Math`) is auto-imported by the compiler. Everything else — `java.util.List`, `medfinder.model.Pharmacy` — needs an explicit `import` statement.
4. Import statements are compile-time only. They are shorthand so you can write `Pharmacy` instead of `medfinder.model.Pharmacy`. They add nothing to the bytecode.
5. Classes in the same package can see each other's package-private members (no access modifier). Classes in different packages cannot — which is how `medfinder.repository.file` hides CSV internals from the rest of the codebase.

## How MedFinder uses it

**Situation:** `PharmacyRepository` lives in the repository layer. It needs to reference `Pharmacy` and `PharmacyStatus` from the model layer, and `List` from the standard library. We need to declare exactly where this file belongs and what it's allowed to see.

```java
package medfinder.repository;

import java.util.List;
import medfinder.model.Pharmacy;
import medfinder.model.PharmacyStatus;

public interface PharmacyRepository {
    List<Pharmacy> findByStatus(PharmacyStatus status);
}
```

**Walkthrough:** The `package medfinder.repository;` line tells the compiler this interface lives in the repository layer — and the file must be at `src/main/java/medfinder/repository/PharmacyRepository.java`. `java.util.List` needs an explicit import because only `java.lang` is automatic. `medfinder.model.Pharmacy` and `medfinder.model.PharmacyStatus` are imported explicitly — not with a wildcard — so anyone reading a pull request diff can see at a glance exactly which model types this interface depends on. If a reviewer ever saw `import medfinder.console.*;` here, that's an immediate architecture violation: repository has no business knowing about console menus.

The allowed import directions in MedFinder are:

| Package | May import | Must never import |
|---|---|---|
| `medfinder.model` | `medfinder.exception` | service, repository, console, ai |
| `medfinder.repository` | model, exception | service, console, repository.file |
| `medfinder.service` | repository, logic, model, exception, config | console, repository.file |
| `medfinder.console` | service, ai, logic, model, exception | repository, repository.file |

## Common mistakes

- **Wildcard imports** (`import medfinder.model.*;`) hide exactly what a class depends on. During code review, explicit imports are the fastest way to spot a layer violation.
- **Mismatched package declaration and folder path.** If the file is in `medfinder/repository/` but declares `package medfinder.model;`, Maven can't resolve it and the build fails.
- **Console importing from `repository.file` directly.** This skips the service layer entirely, bypassing all validation and authorization logic in `AuthService` and its siblings.
- **Assuming all `java.*` packages are auto-imported.** Only `java.lang` is. `java.util.List`, `java.io.IOException`, and everything else still need explicit imports.

## Summary

Packages give every MedFinder class a unique full name and enforce the layered architecture by controlling which classes can see which others. The `package` declaration must match the folder path exactly, or the build fails. Imports are compile-time only, and explicit imports are preferred because they make dependency direction visible in every pull request. The five main layers — `model`, `repository`, `repository.file`, `service`, and `console` — each have a strict list of what they may import, ensuring that console menus never reach into CSV parsers and that business rules always flow through the service layer.
