# What is Maven (`mvn`) and Why Do We Use It?

> **Personal Study Notes** — Kept in `notes/` (git-ignored so it doesn't affect the team repository).

---

## 1. What is Maven in Plain English?

In Java, code starts as human-readable `.java` source files and must be compiled into `.class` bytecode files that run on the Java Virtual Machine (JVM).

When you build a real-world application like **MedFinder**:
- You have **57 Java classes** across 9 different packages.
- You have external libraries to download (like **Gson** for parsing AI JSON).
- You have automated tests (**JUnit 5**) that need to be compiled and executed automatically.
- You need to bundle everything into a single runnable `.jar` file so anyone can double-click or run `java -jar medfinder.jar`.

If you did this by hand with plain terminal commands (`javac` and `java`), you would have to type dozens of complicated commands with massive classpaths every single time you changed one line of code.

**Apache Maven (`mvn`) is a build automation and dependency management tool for Java.** It automates compiling, downloading libraries, testing, and packaging into single, repeatable commands.

---

## 2. The 3 Main Jobs of Maven

### 1. Build Automation
Maven knows how to compile your code in the right order, copy resource files (like `medicines.csv` and `system-prompt.txt`), and produce the final `.jar` file without you ever typing `javac`.

### 2. Dependency Management
Instead of manually hunting down `.jar` files on the internet, downloading them, and placing them into a `lib/` folder, you just write the library name and version inside `pom.xml`. Maven automatically downloads it from the central Maven repository and links it.
- In our project, we only use **Gson** and **JUnit 5**.

### 3. Standardized Project Structure (Convention over Configuration)
Every Maven project in the world uses the exact same folder structure:
```
project-root/
├── pom.xml                 <- The project configuration file
└── src/
    ├── main/
    │   ├── java/           <- All production Java code
    │   └── resources/      <- Non-code files (CSVs, config, prompt templates)
    └── test/
        └── java/           <- Unit tests
```
Because of this convention, any Java developer or AI agent who opens the project immediately knows where everything lives.

---

## 3. What is `pom.xml`?

`POM` stands for **Project Object Model**. It is the single configuration file at the root of our project:
- **Project Identity:**
  - `<groupId>`: The organization/package namespace (`medfinder`)
  - `<artifactId>`: The project name (`medfinder`)
  - `<version>`: Version number (`1.0-SNAPSHOT`)
- **Properties:** Sets Java version (Java 17 in our project).
- **Dependencies (added in T02):** Lists external libraries like Gson.
- **Build Plugins:** Configures plugins like `maven-compiler-plugin` and `maven-surefire-plugin` (which runs the tests).

---

## 4. Everyday Maven Commands Explained

You run these commands in the project root directory (where `pom.xml` is located):

| Command | What it actually does |
|---|---|
| `mvn clean` | Deletes the `target/` directory completely. This wipes away old compiled `.class` files so you start with a clean slate. |
| `mvn compile` | Compiles the code inside `src/main/java/` and places the `.class` files into `target/classes/`. |
| `mvn test` | Compiles your test classes in `src/test/java/` and runs all JUnit 5 test cases. If any test fails, the build fails and reports the error. |
| `mvn clean test` | **The golden command for our team!** Wipes old output, recompiles everything, and runs all tests. This is what must pass before submitting a Pull Request. |
| `mvn clean package` | Wipes old output, recompiles, runs tests, and packages the entire app into a runnable JAR file (`target/medfinder.jar`). |
| `mvn -v` | Prints your installed Maven version, Java version, and OS info. |

---

## 5. Where Does Our Project Already Mention Maven?

If you haven't read all the project docs yet, here is where Maven is specifically defined in our repository:

1. **`docs/03-architecture-and-folder-structure.md` (Section 2 - Technology and Build):**
   - States: *"Build tool: Maven (single module)"*.
   - Specifies: *"Packaging: `mvn package` produces one runnable file `target/medfinder.jar` containing Gson"*.
   - Lists everyday commands table.
2. **`docs/04-implementation-plan.md` (Section 3 - Planning Checklist):**
   - Item: *"Install Java 17+, Maven and an editor; confirm `mvn -v` works"* (Assigned to everyone, due 14 Nov).
3. **`docs/04-implementation-plan.md` & `docs/agents/AGENTS-P1-worku.md` (Tasks T01 & T02):**
   - **T01 (Your current task):** Set up the Maven project skeleton so everyone can run `mvn clean test`.
   - **T02 (Next task):** Add Gson and JUnit 5 to `pom.xml` and configure JAR packaging.
4. **`README.md` (Build and Run):**
   - Gives team members the exact command table to compile, test, and run the program.
