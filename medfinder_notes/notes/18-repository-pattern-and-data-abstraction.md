# The Repository Pattern and Data Abstraction (Chapter 4)

> **Chapter:** 4.6 Interfaces & Contract Architecture | **In MedFinder:** `medfinder.repository.*` | **PR:** #5 by @worku404

## What is it?

The **Repository Pattern** is a design approach that acts as a mediator between your application's business logic and the underlying data storage. Instead of letting your code interact directly with a database or a file system, you define an **interface** that describes the operations you need. This interface acts as a contract, hiding the messy details of how data is actually retrieved or saved.

## Why do we need it?

In MedFinder, we need to store and retrieve users, pharmacies, and medicine records. If we wrote code to read from a CSV file directly inside our business logic, our code would become tightly coupled to that file format. If we later decided to switch to a database, we would have to rewrite every part of our application that touches data. Without this abstraction, our code becomes fragile, hard to test, and difficult to maintain.

## How it works

1. You define an interface (e.g., `UserRepository`) that lists the methods needed to interact with a specific type of data.
2. The business logic only interacts with this interface, never knowing if the data comes from a file, a database, or even a hardcoded list in memory.
3. You create a separate class that implements this interface, containing the actual logic to read or write the data.
4. This separation allows you to swap the implementation later without changing any of the business logic that uses the repository.

## How MedFinder uses it

### Defining Storage Contracts

**Situation:** We need a consistent way to interact with different types of data, such as users and pharmacies, without worrying about the storage implementation.

**Code:**
```java
public interface UserRepository {
    User findById(int id);
    User findByEmail(String email);
    List<User> findAll();
    void save(User user);
    int nextId();
}
```

**Walkthrough:** The `UserRepository` interface defines the *what* (finding, saving, listing users) without defining the *how*. By using this interface, the rest of the MedFinder application can request a user by ID without needing to know if that user is stored in a JSON file or a SQL database. If we didn't use this interface, we would have to hardcode the file-reading logic everywhere we need a user, making the code impossible to update or test.

## Common mistakes

One common mistake is putting business logic inside the repository implementation. Remember that the repository should only be responsible for fetching and saving data. Another mistake is making the interface too specific to one storage type, such as including methods that only make sense for a database, which defeats the purpose of the abstraction.

## Summary

The Repository Pattern uses interfaces to create a clean boundary between your application and its data storage. By defining clear contracts for data access, we ensure that our business logic remains independent of the storage technology. This makes our MedFinder application more modular, easier to test, and ready for future changes.
