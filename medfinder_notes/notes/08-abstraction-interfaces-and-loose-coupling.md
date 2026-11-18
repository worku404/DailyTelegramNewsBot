# Abstraction, Interfaces, and Loose Coupling (Chapters 1, 4 & 5)

> **Chapter:** 1.3 Software Architecture — High Cohesion vs. Tight Coupling, 1.4 Abstraction, 4.6 Interfaces, 5.1–5.2 Polymorphism & Dynamic Dispatch | **In MedFinder:** `medfinder.repository.UserRepository`, `PharmacyRepository`, `MedicineRepository`, `StockRepository`, `LocalityRepository` | **Source:** MedFinder core foundation

## What is it?

A Java **interface** is a contract that says *what* a class must be able to do, without saying *how* it does it. It lists method signatures — names, parameters, and return types — but contains no implementation. Any class that declares `implements UserRepository` is promising to provide a real body for every method the interface lists.

The key idea is that the rest of the application talks to the contract, not to any specific implementation. `AuthService` knows about `UserRepository`. It doesn't know — and doesn't care — whether users are stored in CSV files, a database, or memory. That detail is hidden behind the interface.

## Why do we need it?

Suppose `AuthService` was written to call `FileUserRepository` directly. Now imagine the team decides to swap CSV storage for a database halfway through the project. Every single method call in `AuthService` that touches `FileUserRepository` has to be found and changed. And if another service also imported `FileUserRepository`, that class changes too. And the tests that set up a real file on disk just to test a login — they all break.

With an interface, `AuthService` only knows `UserRepository`. Swapping `FileUserRepository` for `DatabaseUserRepository` means changing one line in `AppContext` — the place that wires everything together. Nothing else in the codebase touches it.

## How it works

1. An interface declares method signatures. Every method in an interface is implicitly `public` and `abstract` — you don't write those keywords, but they're there.
2. You cannot instantiate an interface directly. `new UserRepository()` is a compile error. You can only instantiate a class that implements it.
3. A class can implement multiple interfaces (e.g., `implements UserRepository, Serializable`), but can only extend one class. This is why interfaces are the preferred way to define behavioral contracts.
4. When a service calls a method through an interface reference, Java uses **Dynamic Method Dispatch** (also called Late Binding): the actual method that runs is determined at runtime by the real type of the object, not the type of the reference. The service doesn't know which implementation is running — and that's the point.
5. `AppContext` is the one place that knows the concrete type. It creates `FileUserRepository` and assigns it to a `UserRepository` variable, then hands that variable to every service that needs it.

## How MedFinder uses it

**Situation:** `AuthService` needs to look up users. It shouldn't know whether users are stored in a CSV file, a database, or anywhere else. We need to define what `AuthService` can ask for, without locking it to any storage technology.

```java
public interface UserRepository {
    User findById(int id);
    User findByEmail(String email);
    List<User> findAll();
    void save(User user);
    int nextId();
}

// In AppContext:
UserRepository repo = new FileUserRepository(path, csvFile);
// AuthService only knows UserRepository — not FileUserRepository!
```

**Walkthrough:** The interface lists five method signatures. There are no method bodies, no fields, no `private` members — just a promise. `FileUserRepository` is the class that fulfills that promise by reading and writing CSV files. In `AppContext`, `new FileUserRepository(...)` creates the real object, but it's immediately assigned to a `UserRepository` variable. When that variable is handed to `AuthService`, the service has no way to call any CSV-specific method — it only sees the five methods the interface guarantees. The dependency flows like this:

```
AuthService → UserRepository (interface) ← FileUserRepository
```

`AuthService` depends on the abstraction. `FileUserRepository` also depends on the abstraction (by implementing it). Neither depends on the other directly. This is the Dependency Inversion Principle: high-level classes (`AuthService`) don't depend on low-level details (`FileUserRepository`).

## Common mistakes

- **Depending on `FileUserRepository` directly** in a service class. This defeats the entire point of the interface and makes the service impossible to test without real files on disk.
- **Downcasting back to the concrete class.** Writing `((FileUserRepository) repo).readCsvLine()` inside a service breaks the abstraction. If you need that method, it belongs in the interface or the service is in the wrong layer.
- **Putting fields or state in an interface.** Interfaces define behavior, not data. Fields in an interface are implicitly `public static final` — they're constants, not instance state. If you need shared state, that belongs in an abstract class.
- **One giant interface.** If `UserRepository` had 20 methods, most implementations would be forced to stub out methods they don't use. Interfaces should be narrow and focused on one behavioral role.

## Summary

MedFinder's five repository interfaces — `UserRepository`, `PharmacyRepository`, `MedicineRepository`, `StockRepository`, and `LocalityRepository` — define what the service layer can ask for without saying anything about how that data is stored. `AppContext` is the only place that creates `FileUserRepository` objects and wires them in. Every service receives an interface reference and uses Dynamic Method Dispatch to call whichever concrete implementation was provided at startup. This design means the storage layer can be replaced, tested with fakes, or extended with a new implementation by changing one place in `AppContext`, leaving every service untouched.
