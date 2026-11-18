# What is Maven and Why Do We Use It? (Chapters 1 & 2)

> **Chapter:** 1.1 Program Development & Problem Solving, 2.2 The Java Execution Environment & JVM Internals | **In MedFinder:** `pom.xml`, `src/main/java/medfinder/`, `target/medfinder.jar` | **Source:** MedFinder core foundation

## What is it?

**Maven** (command: `mvn`) is a tool that builds your Java project for you. "Building" means turning the `.java` files you wrote into a program that can actually run, and Maven does every step of that from one command.

It also manages **dependencies**. A dependency is a library written by someone else (for example, Gson, which reads and writes JSON) that your code uses. Instead of downloading these libraries by hand, you write their names and versions in one file, `pom.xml`, and Maven fetches them.

Recall that Java code goes through a pipeline: `.java` source, then the compiler `javac` produces `.class` bytecode, then the JVM runs it. Maven does not replace `javac` or the JVM. It calls them in the right order, with the right settings.

## Why do we need it?

Suppose MedFinder had no Maven, and five of us built it using only `javac` and `java` in the terminal.

- Every compile needs a long command listing every source folder and every library `.jar` file. One typo and the build fails. Windows separates paths with `;` and Linux/macOS with `:`, so a script that works for one teammate breaks for another.
- Each person downloads Gson and JUnit manually. If one of us has a different version, the code works on one machine and fails on another.
- Everyone puts source files, CSV data and config files in different folders, so merging work becomes painful.
- To produce a runnable `.jar`, we would have to package it by hand, including the libraries and a manifest file that names the main class.

Maven removes all of this: one file describes the project, and one command builds it the same way for everyone.

## How it works

1. Maven reads `pom.xml` (the project descriptor). It tells Maven what the project is called, which Java version it uses, and which libraries it needs.
2. Maven downloads each required library from Maven Central (a public online library store) and adds it to the **classpath**, the list of places where Java looks for classes.
3. Maven expects files in a fixed layout. Source code goes in `src/main/java/`, non-code files in `src/main/resources/`, and tests in `src/test/java/`. This is called **convention over configuration**: because everyone follows the same layout, you don't have to configure it.
4. You run a **lifecycle command**. Each one performs all the steps before it as well:
   - `mvn clean` deletes the `target/` folder (all generated output).
   - `mvn compile` compiles `src/main/java/` into `.class` files in `target/classes/`.
   - `mvn test` compiles and runs the tests.
   - `mvn package` also bundles everything into a `.jar` file.

## How MedFinder uses it

### One layout for everyone

**Situation:** we need all team members to know where every kind of file lives, without discussing it.

```text
MedFinder-java/
├── pom.xml
└── src/
    ├── main/
    │   ├── java/medfinder/      <- production Java code
    │   └── resources/           <- seed/*.csv, ai/system-prompt.txt
    └── test/
        └── java/medfinder/      <- JUnit 5 tests
```

**Walkthrough:** `pom.xml` sits at the root and describes the build. Our Java code lives under `src/main/java/medfinder/`, and our CSV seed data and the AI prompt file live under `src/main/resources/`. Because Maven knows these locations, it compiles the code and copies the resources into `target/classes/` automatically. Without this agreement, we would need our own scripts to find and copy those files.

### Our daily commands

**Situation:** before we open a Pull Request, we must be sure the project builds from nothing and the tests pass.

```text
mvn clean test
mvn clean package
java -jar target/medfinder.jar
```

**Walkthrough:** `mvn clean test` first deletes `target/`, then recompiles every class and runs every test. We use `clean` on purpose. If a class was renamed or deleted, its old `.class` file may still be inside `target/`, and a build without `clean` could pass using that leftover file while failing on a teammate's machine. `mvn clean package` does the same and then produces `target/medfinder.jar`, which contains our compiled classes and Gson. The last command starts the JVM, which loads the classes from that jar and runs `main` in `medfinder.Main`.

## Common mistakes

- **Committing `.jar` files into a `lib/` folder.** Declare the library in `pom.xml` instead, so every teammate gets the same version.
- **Committing `target/`.** It contains only generated files that Maven recreates, so it belongs in `.gitignore`. Committing it bloats the repository and causes pointless merge conflicts.
- **Putting code in the wrong folder.** Production code in `src/test/` (or test helpers in `src/main/`) breaks packaging, because Maven treats each folder differently.

## Summary

Maven is the tool that builds our Java project. It reads `pom.xml`, downloads libraries such as Gson and JUnit 5, compiles our code with `javac`, runs the tests and packages `target/medfinder.jar`. It relies on one agreed folder layout, so every teammate builds the same way. Before every Pull Request we run `mvn clean test`, so we know a fresh build from the current source passes.
