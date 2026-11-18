# Course Concept: Program Anatomy, Javadoc & The `main` Entry Point (Chapters 2 & 3)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Java Program Structure, Identifiers, Comments/Javadoc, Access Modifiers, and `public static void main(String[] args)`  
> **Syllabus Reference:** Ch. 2.3 (Java Syntax & Program Structure), Ch. 2.6 (Standard Utilities), Ch. 2.8 (Arrays), Ch. 3.1 (Class Anatomy), Ch. 3.4 (Access Control), Ch. 3.6 (Methods & Static Architecture)  
> **Where in MedFinder:** `src/main/java/medfinder/Main.java`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

Every standalone Java application begins execution at one exact method signature:

```java
public static void main(String[] args)
```

When you launch a program via `java -jar target/medfinder.jar`, the **JVM** locates the designated entry class (`medfinder.Main`), finds this exact `main` method, and executes the statements inside its curly braces `{ ... }` line by line.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: What does every single keyword in `public static void main(String[] args)` mean?

**Answer:**
Every single word has a strict, mandatory purpose (**Ch. 2.3, 3.4, 3.6**):

1. **`public` (Access Modifier — Ch. 3.4):** Makes the method visible from outside its class and package. The JVM sits outside your code, so if `main` were `private`, the JVM could not call it.
2. **`static` (Class Method — Ch. 3.2 & 3.6):** Means the method belongs to the class `Main` itself rather than an object instance. When the program starts, **zero objects exist yet in memory**—so the JVM calls `Main.main(...)` directly without needing `new Main()`.
3. **`void` (Return Type — Ch. 3.6):** Indicates that `main` does not return any data value when it finishes executing.
4. **`main` (Identifier — Ch. 2.3):** The exact reserved entry-point name that the JVM looks for. (Note: Java is case-sensitive; `Main(...)` will not work!)
5. **`String[] args` (Parameter List — Ch. 2.7 & 2.8):** A 1-dimensional **array of `String` objects** holding any command-line arguments typed by the user when launching the program (e.g., `java medfinder.Main arg1 arg2`). Even if unused, the parameter must be present for the JVM to recognize the method.

---

### Question 2: What is the difference between the three types of comments in Java?

**Answer:**
Java supports three comment styles (**Ch. 2.3**), all ignored by the compiler during execution:

1. **Single-line comment (`// ...`):** Explains one quick inline detail.
   ```java
   // Placeholder until T21 replaces it
   ```
2. **Multi-line / Block comment (`/* ... */`):** Temporarily comments out a block of notes or code.
   ```java
   /* This spans
      multiple lines */
   ```
3. **Javadoc documentation comment (`/** ... */`):** Placed directly above classes, interfaces, and public methods. Tools parse tags like `@param`, `@return`, and `{@code ...}` to automatically build official HTML API documentation.
   ```java
   /**
    * Finds a user by id.
    *
    * @param id the user id
    * @return the user, or null if there is none with that id
    */
   ```
   In MedFinder (Team Convention 6.4), **every public class, interface, and method must have a Javadoc comment**.

---

### Question 3: How does `System.out.println(...)` actually work?

**Answer:**
Breaking down the dot-operator chain (**Ch. 2.3, Ch. 2.6, Ch. 3.1, Ch. 3.2**):
- **`System`**: A built-in `final` utility class inside `java.lang`.
- **`.` (Dot operator)**: Accesses a member (field or method) belonging to a class or object.
- **`out`**: A `public static final` reference field inside `System` (of type `PrintStream`) representing the terminal's standard output stream.
- **`println(...)`**: An instance method called on the `out` stream object that prints the given text and automatically appends a newline (`\n`) so the next output begins on a fresh line. (By contrast, `System.out.print(...)` stays on the same line.)

---

### Question 4: Why must the filename `Main.java` match `public class Main`?

**Answer:**
This is a strict Java language rule (**Ch. 2.3 & Ch. 3.1**):
- Whenever a file declares a **`public class`** or **`public interface`**, the file name **must match the exact spelling and capitalization** of that type, followed by `.java`.
- Example: `public class Main` → `Main.java`; `public interface UserRepository` → `UserRepository.java`.
- Why? So the compiler (`javac`) and JVM ClassLoader can instantly locate the file corresponding to any class name without scanning the whole disk.

---

### Question 5: Concrete Code Example from MedFinder (`Main.java`)

```java
package medfinder; // Ch. 3.7: Root package matching src/main/java/medfinder/

/**
 * Entry point of MedFinder. (Ch. 2.3: Javadoc documentation comment)
 *
 * <p>PLACEHOLDER (task T02): it only proves that the packaged jar starts.
 * Task T21 replaces this class with the real start-up: create
 * {@code AppContext}, run {@code StartMenu} inside {@code try ... finally}.
 */
public class Main { // Ch. 3.1 & 3.4: Public class blueprint matching filename Main.java

    /**
     * Starts the program. In this placeholder version it prints one line.
     *
     * @param args command-line arguments (not used)
     */
    public static void main(String[] args) { // Ch. 2.3: JVM Entry Point
        // Ch. 2.6 & 2.7: Printing a String literal to standard output
        System.out.println("MedFinder placeholder: the project builds and starts.");
    }
}
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Why is `main` `static`?** | So the JVM can invoke it directly on the class without instantiating `new Main()` first (**Ch. 3.6**). |
| **Why is `main` `public`?** | Because the JVM invokes it from outside the class and package (**Ch. 3.4**). |
| **What is `String[] args`?** | An array of command-line text arguments passed when launching the program (**Ch. 2.7–2.8**). |
| **What makes `/** ... */` special?** | It is a **Javadoc comment** used to document public contracts (`@param`, `@return`) (**Ch. 2.3**). |
| **What does `System.out.println` mean?** | Static field `out` on class `System`, calling its `println` method to output text plus a newline (**Ch. 2.3, 2.6**). |
