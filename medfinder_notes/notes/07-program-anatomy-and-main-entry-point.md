# Program Anatomy and the Main Entry Point (Chapters 2 & 3)

> **Chapter:** 2.3 Variables & Data Types, 2.6 Standard Output, 2.8 Comments & Documentation, 3.1 Writing a Java Class, 3.4 Access Modifiers, 3.6 Static Members | **In MedFinder:** `src/main/java/medfinder/Main.java` | **Source:** MedFinder core foundation

## What is it?

Every Java program needs exactly one place where the JVM starts running. That place is the `main` method — a method with a very specific signature that the JVM looks for by name. Without it, the JVM has nowhere to begin and the program won't start.

A Java source file also has a strict anatomy around that method: a package declaration, optional imports, a class declaration whose name must match the filename, Javadoc comments on public things, and `System.out.println` to send text to the terminal. These aren't stylistic suggestions — most of them are rules the compiler enforces.

## Why do we need it?

If the `main` method signature is even slightly wrong — say, `static` is missing — the JVM launches, finds the class, but can't locate a valid entry point. It throws `Main method not found in class medfinder.Main` and exits immediately, before a single line of our code runs. Similarly, if the file is named `App.java` but the class inside is `public class Main`, the compiler refuses to compile it at all. These rules exist because the JVM needs a guaranteed contract it can rely on across every Java program ever written — it can't guess at intent.

## How it works

1. The JVM is told to start at a specific class (by Maven's manifest or the `-jar` flag). It loads that class.
2. It looks for a method with this exact signature: `public static void main(String[] args)`. Every word matters:
   - `public` — the JVM, which is outside our package, must be able to call this method.
   - `static` — the JVM calls it without creating an instance of `Main` first. There's no object at startup, only the class.
   - `void` — `main` hands control back to the JVM when it's done; it doesn't return a value to anyone.
   - `String[] args` — the JVM passes any command-line arguments as an array of strings. MedFinder doesn't use them, but the parameter must be there.
3. The class's filename must exactly match the `public class` name. `public class Main` must be in `Main.java`.
4. Javadoc comments (`/** ... */`) on public classes and methods generate the HTML documentation that teammates read without opening source files. They use `@param` to document each parameter and `@return` to document the return value.
5. `System.out.println("text")` breaks down as: `System` is a class in `java.lang` (auto-imported), `out` is a `static` field on `System` of type `PrintStream`, and `println` is an instance method on that `PrintStream` object.

## How MedFinder uses it

**Situation:** MedFinder needs a single, clean entry point that wires up the application and starts the menu loop. It should document itself with Javadoc, and it should contain no business logic of its own.

```java
package medfinder;

/**
 * Entry point of MedFinder.
 * <p>Starts the application by wiring {@code AppContext} and running
 * {@code StartMenu} inside a {@code try ... finally} block.
 */
public class Main {

    /**
     * Starts the program.
     * @param args command-line arguments passed at launch
     */
    public static void main(String[] args) {
        System.out.println("MedFinder placeholder: the project builds and starts.");
    }
}
```

**Walkthrough:** `package medfinder;` places this class in the top-level `medfinder` package, which matches its folder `src/main/java/medfinder/Main.java`. The outer Javadoc comment describes the class's purpose — that it wires `AppContext` and runs `StartMenu`. The inner Javadoc on `main` uses `@param args` to document the command-line parameter (even though MedFinder ignores it). The method signature is exactly `public static void main(String[] args)` — all four keywords required. The body calls `System.out.println`, which reaches `out` (a static `PrintStream` field on the `System` class) and calls `println` on it. In the real application this placeholder line is replaced with the `AppContext`/`StartMenu` wiring, but it stays very short — `main` is not the place for logic.

## Common mistakes

- **Missing `static` on `main`.** The JVM can't call an instance method before any object is created. It throws `Main method not found` and the program never starts.
- **Wrong filename.** A `public class Main` inside a file called `App.java` causes a compile error. The filename and the public class name must match exactly.
- **God Main anti-pattern.** Putting all application logic directly inside `main()` — reading input, parsing files, running menus — makes the code impossible to test and impossible for teammates to work on in parallel. `main` should do only one thing: wire up the objects and hand off to them.
- **Skipping Javadoc on public methods.** Single-line `//` comments don't generate documentation. Public methods and classes should have `/** */` Javadoc so teammates understand the contract without reading the implementation.

## Summary

`Main.java` is the guaranteed starting point that the JVM looks for by its exact method signature. Each keyword in `public static void main(String[] args)` serves a specific purpose, and changing or omitting any one of them stops the program from launching. The filename must match the public class name, Javadoc comments (`/** */` with `@param` and `@return`) document public contracts, and `System.out.println` is shorthand for reaching the `PrintStream` stored in `System.out`. MedFinder's `main` stays intentionally thin — it wires `AppContext` and starts `StartMenu`, then stops, leaving all real logic to the classes it delegates to.
