# Read-Only Interfaces and Encapsulation Guardrails (Chapters 1, 3 & 4)

> **Chapter:** 1.4 Core Pillars of Object-Oriented Programming (Abstraction & Encapsulation), 3.4 Encapsulation & Access Control, 4.6 Interfaces & Contract Architecture | **In MedFinder:** `medfinder.repository.MedicineRepository`, `medfinder.repository.LocalityRepository` | **Source:** MedFinder core foundation

## What is it?

**Abstraction** means showing callers only the operations they actually need while hiding everything else. A **read-only interface** applies this idea by declaring only query methods (such as `findById` and `findActive`) and intentionally leaving out every write method (`save`, `update`, `delete`, or `nextId`).

Together with **encapsulation** — protecting internal state so external code cannot break the rules of the data — a read-only interface acts as a compile-time guardrail. If an operation is not on the interface, callers cannot even compile code that tries to mutate the data.

## Why do we need it?

In MedFinder, some data changes while the app is running: pharmacists register new accounts, add pharmacies, and update stock. Other data is fixed reference data: the master medicine catalogue (`medicines.csv`) and the Addis Ababa locality directory (`localities.csv`) are loaded as reference lists and are never edited from the console.

If we copy-pasted `save`, `delete`, and `nextId` into `MedicineRepository` and `LocalityRepository` anyway, three problems would follow:

- **Broken domain rules:** any future service or menu could accidentally overwrite or delete reference medicines, violating the rule that the catalogue stays fixed at runtime.
- **Fake methods that crash at runtime:** `FileMedicineRepository` would be forced to implement `save(Medicine)` just to throw `UnsupportedOperationException`, turning a compile-time guarantee into a runtime crash.
- **Repeated filtering across callers:** if `MedicineRepository` exposed a generic `findAll()` instead of `findActive()`, every service that searches or lists medicines would have to remember to filter out discontinued medicines, and forgetting once would show inactive drugs to customers.

## How it works

1. **Design each interface around what callers are allowed to do.** Before adding a method to an interface, check whether the domain actually permits that action. A read-write repository (`UserRepository`, `PharmacyRepository`) needs `save` and `nextId`; a reference-data repository (`MedicineRepository`, `LocalityRepository`) does not.
2. **Let the compiler enforce the boundary.** Because callers declare fields and parameters using the interface type (`MedicineRepository`), `javac` only permits calls to methods listed in that interface. Any attempt to call `medicineRepo.save(med)` fails immediately during compilation.
3. **Pair minimal interfaces with defensive copies.** Even without a `save` method, returning an internal `List` directly would let a caller run `.clear()` on it. Returning a fresh copy of the list closes that back door so the internal catalogue remains untouched.
4. **Respect the Liskov Substitution Principle.** A class implementing an interface should honor every method the interface promises. Leaving write methods off read-only interfaces avoids implementing dummy methods that break callers' expectations by throwing `UnsupportedOperationException`.

## How MedFinder uses it

### A deliberately minimal read-only contract

**Situation:** `SearchService` and `CatalogueService` need to look up medicines by ID and list currently active medicines, without ever modifying the master catalogue.

```java
package medfinder.repository;

import java.util.List;
import medfinder.model.Medicine;

public interface MedicineRepository {

    Medicine findById(int id);

    List<Medicine> findActive();
}
```

**Walkthrough:** `MedicineRepository` exposes only two methods. `findActive()` hides inactive or discontinued medicines behind the repository boundary so callers never have to filter them by hand, while `findById(int id)` still lets the app resolve an older medicine referenced by a stock record. Just as important is what is absent: there is no `save`, `delete`, or `nextId`. If we added `save` here, a developer could accidentally mutate reference data or force the file implementation to write a stub method that throws at runtime.

### Contrasting read-only vs. read-write repositories

**Situation:** unlike the fixed medicine catalogue, user accounts do change at runtime when new pharmacists register, so `UserRepository` needs write operations.

```java
public interface UserRepository {

    User findById(int id);

    User findByEmail(String email);

    List<User> findAll();

    void save(User user);

    int nextId();
}
```

**Walkthrough:** comparing `UserRepository` with `MedicineRepository` shows why MedFinder does not force every repository to share one generic CRUD interface. `UserRepository` and `PharmacyRepository` include `save` and `nextId` because the application creates and updates users and pharmacies; `MedicineRepository` and `LocalityRepository` omit them because reference data is read-only. Forcing both kinds onto one template would either expose dangerous writes on fixed data or hide needed writes on user data.

## Common mistakes

- **Adding `save()` "just in case" and throwing `UnsupportedOperationException`.** That turns a mistake the compiler could catch immediately into a surprise runtime crash. Omit methods that the domain forbids instead.
- **Downcasting an interface back to its concrete class to reach extra methods.** Writing `((FileMedicineRepository) medicineRepo)` bypasses the interface guardrail and tightly couples your code to one implementation. Always depend only on the interface contract.

## Summary

Good abstraction is defined as much by what you leave out of an interface as by what you put in. In MedFinder, `MedicineRepository` and `LocalityRepository` intentionally omit `save`, `delete`, and `nextId` so the Java compiler prevents any service or menu from mutating fixed reference data. Combined with defensive copying and `findActive()` filtering, this design protects our domain rules at compile time instead of relying on runtime checks.
