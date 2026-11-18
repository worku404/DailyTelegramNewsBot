# Course Concept: JVM Execution Pipeline & Maven Build System (Chapters 1 & 2)

> **Course:** Object-Oriented Programming (Java)  
> **Topic:** Java Platform Architecture, Bytecode, JVM Execution Pipeline, and Standardized Builds (`pom.xml`)  
> **Syllabus Reference:** Ch. 1.1 (Program Development Lifecycle), Ch. 2.1 (Java Platform Architecture), Ch. 2.2 (The Java Execution Environment & JVM Internals)  
> **Where in MedFinder:** `pom.xml`, `src/main/java/medfinder/Main.java`, `target/medfinder.jar`  
> **Folder:** `notes/course-concepts/` (git-ignored personal study notes)

---

## 📖 Concept Overview in 30 Seconds

Unlike C or C++, Java does **not** compile directly into operating-system-specific machine code. Instead, Java follows a **two-stage execution pipeline**:

```
Source Code (.java)  ──[ javac compiler ]──►  Bytecode (.class)  ──[ JVM ]──►  OS / CPU Machine Code
(Human readable)                              (Platform-neutral)               (Windows, Linux, macOS)
```

- **Bytecode (`.class`)** makes Java **architecture-neutral and portable** (*"Write Once, Run Anywhere"*).
- **Maven (`pom.xml`)** automates compiling, dependency downloading, testing (`mvn clean test`), and packaging (`mvn package`) so all five teammates build the exact same way on any machine.

---

## 🎯 Question & Answer Study Guide (for Defense & Exams)

### Question 1: What happens step by step from writing a `.java` file to seeing output in the terminal?

**Answer:**
1. **Editing:** You write human-readable Java source code in a `.java` file (e.g., `Main.java`).
2. **Compilation (`javac`):** The Java compiler checks syntax and type rules. If valid, it translates `.java` into platform-neutral **bytecode** stored in a `.class` file (e.g., `target/classes/medfinder/Main.class`).
3. **Class Loading:** When you run `java -jar target/medfinder.jar`, the JVM's **ClassLoader Subsystem** loads the `.class` files into memory.
4. **Bytecode Verification:** The **Bytecode Verifier** checks that the bytecode obeys Java's safety rules (no illegal memory access or broken type casts).
5. **Execution Engine:** The JVM executes bytecode using an **Interpreter** (fast start-up) and a **Just-In-Time (JIT) Compiler** (converts frequently run "hot" methods into native CPU instructions for high performance).

---

### Question 2: What are the key runtime memory areas inside the JVM?

**Answer:**
According to **Ch. 2.2 (JVM Runtime Memory Model)**, the JVM divides memory into key regions:
- **Metaspace / Method Area:** Stores class blueprints, method bytecode, and `static` variables/constants (loaded once per class).
- **Stack Memory (Stack Frames):** Stores local variables and method call frames. Every time a method is called, a new stack frame is pushed; when it returns, the frame is popped.
- **Heap Memory:** Stores all objects created with `new` (such as `User`, `Pharmacy`, `ArrayList`, and arrays).
- **Garbage Collector (GC):** Automatically frees objects in Heap Memory that are no longer reachable by any reference variable.

---

### Question 3: Why does MedFinder use Maven (`pom.xml`) instead of running `javac` manually?

**Answer:**
In a 5-person group project (Ch. 1.1 Program Development Lifecycle), running `javac` by hand fails quickly because:
- Teammates may have different Java versions installed (e.g., Java 17 vs. Java 21).
- Everyone needs the exact same versions of external libraries (**Gson** and **JUnit 5**).
- Manual classpath commands become error-prone once there are 57 classes across 10 packages.

Maven's `pom.xml` (*Project Object Model*) solves this by declaring:
1. **Compiler Target (`<maven.compiler.release>17</maven.compiler.release>`):** Guarantees our code compiles strictly as Java 17, even on a machine running Java 21.
2. **UTF-8 Encoding:** Prevents text/character corruption between Windows and Linux.
3. **Pinned Plugins:** Fixes `maven-compiler-plugin` (3.11.0), `maven-surefire-plugin` (3.2.5), and `maven-shade-plugin` (3.5.2) so every build behaves identically.
4. **Dependency Scopes:** Keeps `junit-jupiter` in `<scope>test</scope>`, ensuring test code never leaks into production code (`src/main/java/`).

---

### Question 4: What is the difference between `mvn clean test` and `mvn clean package`?

**Answer:**
- **`mvn clean test`**:
  1. `clean` deletes the old `target/` folder (removing stale `.class` files).
  2. Compiles `src/main/java/` and `src/test/java/`.
  3. Runs JUnit 5 tests via the Surefire plugin and reports `BUILD SUCCESS` or failures.
- **`mvn clean package`**:
  1. Runs everything in `mvn clean test`.
  2. Uses `maven-shade-plugin` to bundle all our `.class` files **plus Gson** into a single executable archive: `target/medfinder.jar`, with `medfinder.Main` configured as its entry point.

---

### Question 5: Concrete Configuration Example from MedFinder (`pom.xml`)

```xml
<properties>
    <maven.compiler.release>17</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <gson.version>2.10.1</gson.version>
    <junit.version>5.10.2</junit.version>
</properties>

<dependencies>
    <!-- Only two libraries are allowed: Gson (AI JSON) and JUnit 5 (tests) -->
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>${gson.version}</version>
    </dependency>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>${junit.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

---

## 📋 Quick Review Checklist for Oral Presentation / Defense

| Concept | Key Point to Say to Instructor |
|---|---|
| **Why is Java portable?** | `javac` compiles `.java` into platform-neutral `.class` bytecode, which any OS's JVM can execute (**Ch. 2.1–2.2**). |
| **Where do objects vs. local variables live?** | Local variables live on the **Stack**; objects live on the **Heap**; class definitions & `static` members live in **Metaspace** (**Ch. 2.2**). |
| **Why `<maven.compiler.release>17`?** | Forces Java 17 bytecode compatibility even if a teammate has Java 21 installed. |
| **Why `<scope>test</scope>` on JUnit?** | Ensures production code in `src/main/` never depends on test libraries, so the app runs cleanly even if `src/test/` is removed. |
| **What does `target/medfinder.jar` contain?** | All compiled MedFinder `.class` bytecode, Gson, and a manifest pointing to `medfinder.Main`. |
