# Primitive Types, Reference Types, and `null` (Chapters 2 & 3)

> **Chapter:** 2.3 Java Syntax & Program Structure (Primitive vs. Reference Types), 3.1 Class Anatomy & Object Lifecycle (`null` References), 3.3 Parameter Passing Architecture | **In MedFinder:** `medfinder.repository.UserRepository`, `PharmacyRepository`, `MedicineRepository` | **Source:** MedFinder core foundation

## What is it?

In Java, every variable holds one of two kinds of data: a **primitive type** or a **reference type**. A primitive type (`int`, `double`, `boolean`, `char`, `long`, and three smaller integer/decimal types) stores the raw value directly inside the variable itself.

A reference type (any class, interface, or array, such as `User`, `Pharmacy`, `String`, or `List<User>`) does not store the object directly inside the variable. Instead, it stores a **reference** — a memory address pointing to where the actual object lives in the JVM's **Heap** (the shared memory area where `new` creates objects).

Because a reference is just an address, it can also be empty. In Java, that empty address is written `null`, which means "this variable currently points to no object at all." A primitive variable can never be `null`; it always holds a real value such as `0` or `false`.

## Why do we need it?

Suppose a pharmacist logs in to MedFinder and our code looks up their pharmacy using `pharmacyRepo.findByOwner(userId)`, or a new user registers and we check `userRepo.findByEmail(email)`. Sometimes a matching record exists, and sometimes it does not.

If we did not understand how primitives, references, and `null` behave, three bugs would show up immediately:

- **Unexpected crashes (`NullPointerException`):** calling `pharmacy.getName()` when `findByOwner` returned `null` crashes the program at runtime because there is no object at that address to call a method on.
- **Misusing exceptions for normal checks:** if `findByEmail` threw an exception whenever an email was missing, registering a new user would trigger an error on the normal, expected path where the email is still available.
- **Confusing parameter changes:** assuming Java passes objects "by reference" leads to bugs when a method reassigns a parameter variable and expects the caller's variable to change.

## How it works

1. **Where values live in memory.** Local primitive variables like `int id = 7;` live directly in the method's **Stack frame** (the temporary workspace for that method call). For a reference variable like `Pharmacy p = new Pharmacy(...);`, the `Pharmacy` object lives on the Heap, while `p` in the Stack frame stores only the address of that object.
2. **How Java passes arguments (strictly pass-by-value).** Whenever you call a method, Java copies what is inside the caller's variable into the method's parameter. For a primitive `int`, it copies the number, so changing the parameter never changes the caller's number. For a reference `Pharmacy`, it copies the address — both variables point to the same Heap object, so calling mutator methods on that object affects it, but reassigning `p = null;` inside the method does not change the caller's variable.
3. **What happens when you dereference `null`.** Using the dot operator (`.`) on a reference tells the JVM to follow the address to the Heap object and read a field or run a method. If that reference is `null`, there is nothing to follow, and the JVM immediately throws a `NullPointerException`.
4. **Choosing the right return type for absence.** A method returning primitive `int` (like `nextId()`) guarantees at compile time that a real number is always returned. A single-entity lookup (like `findById`) returns a reference type that may be `null` when nothing matches. A collection lookup (like `findAll`) returns an empty `List`, never `null`, so loops stay safe.

## How MedFinder uses it

### Primitive inputs and nullable reference outputs

**Situation:** our `PharmacyRepository` needs methods to look up one pharmacy, generate the next numeric ID, and save changes.

```java
public interface PharmacyRepository {
    // ...
    Pharmacy findById(int id);

    Pharmacy findByOwner(int ownerUserId);

    void save(Pharmacy pharmacy);

    int nextId();
}
```

**Walkthrough:** `id` and `ownerUserId` are primitive `int` values, so callers cannot accidentally pass `null` as an ID. Likewise, `nextId()` returns primitive `int`, which guarantees a usable number every time. Both `findById` and `findByOwner` return the reference type `Pharmacy`, which holds either the matching object or `null` if no record exists. Without clear return contracts here, every service calling the repository would have to guess whether an ID could be `null` or whether a missing pharmacy throws an exception.

### Guarding a nullable reference in the service layer

**Situation:** when a logged-in pharmacist opens their pharmacy profile, the service must check whether `findByOwner` actually found a pharmacy before using it.

```java
Pharmacy pharmacy = pharmacyRepo.findByOwner(currentUserId);
if (pharmacy == null) {
    throw new NotFoundException("You have not registered a pharmacy yet.");
}
// Safe to call methods on pharmacy below this check
```

**Walkthrough:** `findByOwner` returns `null` as a normal lookup answer because not having a pharmacy yet is not a storage failure. The service layer inspects `pharmacy == null` right away and decides what absence means in this context: here it raises a clear `NotFoundException`. If we skipped that `if` check and called `pharmacy.getStatus()` directly, the console app would crash with an unhelpful `NullPointerException`.

## Common mistakes

- **Calling a method on a lookup result without checking for `null`.** Always inspect single-entity repository results (`if (user == null)`) before using `.` on them.
- **Returning `null` from a method that returns a `List`.** Returning `null` forces every caller to add a null check before a `for-each` loop. Return an empty `List` instead so loops simply run zero times.

## Summary

Java divides all data into primitive types, which store raw values directly and can never be `null`, and reference types, which store Heap addresses and can be `null` when no object is present. Java passes every argument by value, copying either the raw number or the object's address. In MedFinder, our repositories use primitives for mandatory IDs, nullable references for single-record lookups, and empty lists for collections, while our services check for `null` before touching any returned object.
