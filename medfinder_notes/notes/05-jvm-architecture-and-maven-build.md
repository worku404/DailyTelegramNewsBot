# The JVM Execution Pipeline and Runtime Memory (Chapters 1 & 2)

> **Chapter:** 1.1 Program Development & Problem Solving, 2.1 Compiling & Running Java Programs, 2.2 The Java Execution Environment & JVM Internals | **In MedFinder:** `pom.xml`, `medfinder.Main`, `target/medfinder.jar` | **Source:** MedFinder core foundation

## What is it?

Running a Java program is a two-stage pipeline. Stage one: `javac` (the Java compiler) reads your `.java` source files and produces `.class` files containing **bytecode** — a compact, platform-neutral instruction set that is not quite machine code. Stage two: the **JVM** (Java Virtual Machine) reads those `.class` files and executes them, translating bytecode into native machine instructions for whatever CPU you're running on.

This two-stage split is what makes Java's "Write Once, Run Anywhere" promise work. You compile once; the resulting bytecode runs on any machine that has a JVM, regardless of operating system or CPU.

## Why do we need it?

If Java compiled straight to machine code the way C does, the executable for Windows (x86-64) would be a completely different file from the one for Linux (ARM). We'd have to compile separately for every platform. With bytecode + JVM, we compile once to `.class` files, and every platform's JVM takes it from there.

For MedFinder specifically: `mvn package` produces `target/medfinder.jar`, which is just a zip of `.class` files plus a manifest. That one jar file runs identically on every teammate's machine and on the CI server, regardless of OS, as long as Java 17 is installed. The `pom.xml` compiler plugin setting (`<java.version>17</java.version>`) tells `javac` to target Java 17 bytecode — if someone tries to run the jar on an older JVM, they get a clear `UnsupportedClassVersionError` instead of mysterious failures.

## How it works

1. `mvn compile` calls `javac`, which reads every `.java` file under `src/main/java/` and produces matching `.class` files in `target/classes/`.
2. `mvn package` then calls the shade plugin, which packs all those `.class` files plus Gson's `.class` files into `target/medfinder.jar`, and writes a `MANIFEST.MF` naming `medfinder.Main` as the entry point.
3. `java -jar target/medfinder.jar` starts the JVM. The JVM's **ClassLoader** reads the manifest, finds `medfinder.Main`, loads its `.class` file into memory, and begins execution.
4. At runtime, the JVM manages four key memory areas:
   - **Metaspace** — stores class blueprints (field names, method bytecode) and static members. `TextSimilarity.levenshtein` lives here.
   - **Heap** — stores every object created with `new`. All `Medication` and `SearchResult` instances live here. The **Garbage Collector** automatically reclaims heap objects that nothing references anymore.
   - **Stack** — each thread has its own stack. Each method call gets a **stack frame** holding its local variables and return address. When the method returns, the frame is popped.
   - **PC Register** — per-thread instruction pointer tracking which bytecode instruction to execute next.
5. The JVM starts in **interpreter mode**: it executes bytecode one instruction at a time. The **JIT (Just-In-Time) compiler** watches for "hot" code — methods called repeatedly. It compiles those to native machine code on the fly, so the second time through they run at native speed.

## How MedFinder uses it

**Situation:** understanding exactly what happens between typing `java -jar target/medfinder.jar` and the first line of `medfinder.Main.main` executing.

```text
java -jar target/medfinder.jar
        │
        ▼
   JVM starts up
        │
        ▼
   ClassLoader reads MANIFEST.MF → Main-Class: medfinder.Main
        │
        ▼
   ClassLoader loads medfinder/Main.class into Metaspace
        │
        ▼
   JVM calls main(String[] args) → new Stack frame on thread-0's Stack
        │
        ▼
   main() creates objects (new MedicationRepository(), etc.) → Heap
        │
        ▼
   Static methods (TextSimilarity.levenshtein, etc.) resolved in Metaspace
```

**Walkthrough:** The JVM doesn't load every class at startup — it loads them lazily, the first time they're referenced. `medfinder.Main` is loaded first because the manifest says so. When `main` calls `new MedicationRepository()`, the ClassLoader loads `MedicationRepository.class` into Metaspace (the blueprint) and allocates the new instance on the Heap. Local variables inside `main` (like loop counters or temporary results) live on the Stack and vanish when the method returns. Static utility methods like `TextSimilarity.levenshtein` are already in Metaspace from when their class was first loaded — no object needed to call them.

## Common mistakes

- **Confusing Stack and Heap.** Stack holds local variables and call frames — small, short-lived, one per thread. Heap holds objects created with `new` — shared across threads, managed by GC. Thinking a `new Medication(...)` goes on the Stack, or that a local `int counter` goes on the Heap, is wrong in both directions.
- **Thinking the JVM replaces javac.** They are separate tools. `javac` compiles `.java` to `.class`. The JVM runs `.class`. You need both; neither does the other's job. Maven calls `javac` during `compile` and calls the JVM during `test` and when you run the jar.
- **Not knowing what the ClassLoader does.** The ClassLoader is the component that finds `.class` files (inside the jar, on the classpath) and loads them into Metaspace. If a class can't be found, you get `ClassNotFoundException`, not a compiler error — it fails at runtime because class loading is a runtime activity.
- **Ignoring `UnsupportedClassVersionError`.** This error means the `.class` files were compiled targeting a newer Java version than the JVM running them. The fix is to match the Java version in `pom.xml` with the Java version installed, not to fiddle with the bytecode.

## Summary

Running `java -jar target/medfinder.jar` kicks off a two-stage process: `mvn package` already ran `javac` to produce `.class` bytecode in the jar, and now the JVM's ClassLoader loads those classes into Metaspace, starting with `medfinder.Main`. At runtime, the JVM manages Metaspace (class blueprints and static methods), the Heap (all `new` objects, GC-managed), and per-thread Stacks (local variables and call frames). The JIT compiler turns hot paths into native code automatically. The `<java.version>17</java.version>` setting in `pom.xml` pins both the compilation target and the runtime expectation, so a version mismatch fails loudly with `UnsupportedClassVersionError` rather than silently.
