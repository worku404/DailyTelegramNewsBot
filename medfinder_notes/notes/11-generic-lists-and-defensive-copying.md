# Generic Lists and Defensive Copying (Chapters 2.8, 3.1, 3.4, 4.6 & 5.2–5.3)

> **Chapter:** 2.8 Arrays, 3.1 Object References, 3.4 Encapsulation, 4.6 Interfaces, 5.2–5.3 Generics | **In MedFinder:** `UserRepository.findAll()`, `PharmacyRepository.findByStatus(...)`, `MedicineRepository.findActive()`, `StockRepository.findByPharmacy(...)` | **Source:** MedFinder core foundation

## What is it?

A `List<T>` is a resizable, ordered collection where `T` is the element type — `List<Medicine>`, `List<User>`, and so on. The `<T>` part is called a **generic type parameter**, and it tells the compiler exactly what kind of object this list holds.

**Defensive copying** is the practice of returning a *new* list built from your internal one, rather than handing out the internal list directly. It's the difference between giving a customer a photocopy of your records versus handing them the original filing cabinet.

## Why do we need it?

The MedFinder team has five people. Person A owns `FileUserRepository` and maintains the internal `List<User>`. Person B writes `AuthService` and calls `findAll()` to loop through users. If `findAll()` returns the actual internal list, Person B could call `userList.clear()` or `userList.add(fakeUser)` — not maliciously, just by accident. The in-memory list that the repository has been building from the CSV file is now corrupted, and the next `save()` call writes garbage to `users.csv`. Defensive copying makes that physically impossible without touching `FileUserRepository` at all.

Generics solve a related problem. Without `<T>`, you'd use a raw `List` and store everything as `Object`, requiring casts everywhere: `(Medicine) list.get(0)`. A wrong cast compiles fine but throws `ClassCastException` at runtime. With `List<Medicine>`, the compiler rejects type mismatches at compile time — you never get to runtime with the wrong type.

## How it works

1. You declare a field like `private final List<Medicine> medicines = new ArrayList<>()` — the backing store.
2. `final` on the reference means you can't reassign `medicines` to point at a different list object. It does **not** mean the list contents are locked — you can still call `medicines.add(...)` or `medicines.clear()`.
3. When a caller asks for the list via `findActive()`, you create a **new** `ArrayList`, iterate over the internal one, and add only the items you want to expose.
4. The caller receives a completely separate list object. They can modify it however they like; the internal list is untouched.
5. The return type should be declared as `List<Medicine>` (the interface), never `ArrayList<Medicine>` (the concrete class). This keeps callers decoupled from your storage choice.
6. If the query finds nothing, return an empty list — never `null`. An empty list is safe to loop over; `null` causes `NullPointerException` the moment a caller writes `for (Medicine m : repo.findActive())`.

## How MedFinder uses it

**Situation:** `MedicineRepository.findActive()` needs to return only active medicines, without letting callers reach into or modify the repository's internal collection.

```java
private final List<Medicine> medicines = new ArrayList<>();

// BAD — returns internal reference, caller can call .clear():
public List<Medicine> findActiveBroken() { return this.medicines; }

// GOOD — returns a defensive copy:
public List<Medicine> findActive() {
    List<Medicine> copy = new ArrayList<>();
    for (Medicine m : medicines) {
        if (m.isActive()) copy.add(m);
    }
    return copy;
}
```

**Walkthrough:** `findActiveBroken()` hands out `this.medicines` directly — the caller now holds a reference to the same object on the heap. Any mutation the caller makes is a mutation of the repository's private state. `findActive()` creates a fresh `ArrayList` called `copy`, walks through `medicines` with a for-each loop, and adds only the medicines where `isActive()` returns true. The caller gets a snapshot: a new list, populated with the right items, completely disconnected from the internal collection. The filtering also happens here in one place — no caller needs to remember to filter out discontinued medicines themselves.

## Common mistakes

- **Returning `this.list` directly** — the caller holds your internal list. Any `.add()`, `.remove()`, or `.clear()` they call corrupts the repository state without going through any save logic.
- **Thinking `final List` means immutable** — `final` only freezes the reference (you can't do `this.medicines = otherList`). The list's *contents* remain fully mutable.
- **Returning `null` for an empty result** — always return `new ArrayList<>()`. Every caller would need a null-check before looping, and someone will forget.
- **Declaring the return type as `ArrayList<Medicine>` instead of `List<Medicine>`** — this locks callers to your implementation detail. If you ever switch from `ArrayList` to `LinkedList`, every caller's code breaks. Program to the interface.

## Summary

MedFinder's repository methods — `UserRepository.findAll()`, `PharmacyRepository.findByStatus(...)`, `MedicineRepository.findActive()`, and `StockRepository.findByPharmacy(...)` — all return `List<T>` with a generic type parameter so the compiler enforces type correctness end-to-end. Each implementation returns a defensive copy built from its private `final List<T>` field, so no service or menu can accidentally corrupt the in-memory data the repository has loaded from CSV. The filtering (like `isActive()`) lives inside the repository method, not scattered across every caller — and an empty list is always returned instead of null, keeping for-each loops crash-free across the whole codebase.
