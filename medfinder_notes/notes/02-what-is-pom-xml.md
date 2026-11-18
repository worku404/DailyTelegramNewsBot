# What is `pom.xml` and Why Do We Need It?

> **Personal Study Notes** — Kept in `notes/` (git-ignored, private learning documentation).

---

## 1. What is `pom.xml` in Plain English?

`pom.xml` is the **single most important file** in an Apache Maven project. 

- **POM** stands for **Project Object Model**.
- It is written in XML (Extensible Markup Language).
- Think of `pom.xml` as the **blueprint, recipe, and identity card** of the entire application. It tells Maven:
  - *Who is this project?* (Name, group, version)
  - *What Java version does it need?* (Java 17)
  - *What external libraries does it depend on?* (Gson, JUnit 5)
  - *How should it be built, tested, and packaged into a `.jar` file?*

---

## 2. Is `pom.xml` Necessary?

**YES, it is 100% mandatory.**

If you run `mvn clean test` or `mvn clean package` in a folder that does not contain a `pom.xml` file, Maven will immediately abort with this fatal error:

```text
[ERROR] The goal you specified requires a project to execute but there is no POM in this directory.
```

Maven is literally blind without `pom.xml`. Every action Maven takes is driven by the declarations inside this file.

---

## 3. What Happens WITHOUT `pom.xml`? (The Nightmare of Manual Java)

To truly appreciate `pom.xml`, imagine building **MedFinder (57 classes across 9 packages)** using only raw Java terminal commands (`javac` and `java`):

### ❌ Problem 1: Manual Dependency Hunting & Clutter
- Without Maven, where do you get **Gson** (for AI JSON) and **JUnit 5** (for testing)?
- You would have to open a web browser, search for `gson-2.10.1.jar`, `junit-jupiter-api-5.10.2.jar`, `junit-platform-commons.jar`, `opentest4j.jar`, etc.
- You would have to download all 8+ separate `.jar` files manually, create a `lib/` folder in your project, and commit heavy binary files into your Git repository.
- If one teammate downloads Gson 2.8 and another downloads 2.10, code that works on one computer will crash on another!

### ❌ Problem 2: Monstrous Compilation Commands
To compile 57 classes across 9 subdirectories and link them to Gson without Maven, you would have to type this in terminal every single time you edit code:
```bash
javac -d target/classes -cp "lib/gson-2.10.1.jar" src/main/java/medfinder/*.java src/main/java/medfinder/model/*.java src/main/java/medfinder/service/*.java src/main/java/medfinder/repository/*.java src/main/java/medfinder/repository/file/*.java src/main/java/medfinder/logic/*.java src/main/java/medfinder/config/*.java src/main/java/medfinder/exception/*.java src/main/java/medfinder/console/*.java src/main/java/medfinder/ai/*.java
```
On Windows, path separators are `;`, on Linux/Mac they are `:`. Scripts written on Windows break immediately on Mac or Linux.

### ❌ Problem 3: Impossible Test Automation
Without Maven, to run your JUnit test suite, you would have to download the standalone JUnit Console Launcher and manually pass every test class and dependency path.

### ❌ Problem 4: Painful Executable JAR Creation
When presenting the project to the instructor, you need a runnable `target/medfinder.jar` that can be run with:
```bash
java -jar target/medfinder.jar
```
Without `pom.xml`:
1. You would have to manually unzip `gson-2.10.1.jar` to extract its raw `.class` files.
2. Merge those classes with your own compiled classes.
3. Manually write a text file called `MANIFEST.MF` containing:
   ```text
   Main-Class: medfinder.Main
   ```
4. Run the tricky packaging command:
   ```bash
   jar cvfm target/medfinder.jar MANIFEST.MF -C target/classes .
   ```
If you make one typo in `MANIFEST.MF`, the JAR fails to run.

---

## 4. How `pom.xml` Solves All of This

With `pom.xml`, **all of the chaos above disappears**. 

You just run:
```bash
mvn clean test        # Wipes old files, downloads libraries, compiles, runs all tests
mvn clean package     # Does all above + builds target/medfinder.jar automatically
```

---

## 5. Tour of Our Actual MedFinder `pom.xml`

Here is an exact walkthrough of how each part of our project's `pom.xml` works:

### 1. Project Coordinates (Identity)
```xml
<groupId>medfinder</groupId>
<artifactId>medfinder</artifactId>
<version>1.0-SNAPSHOT</version>
<packaging>jar</packaging>
```
- Tells Maven this project produces a **JAR** file named `medfinder`.

### 2. Properties (Rules & Versions)
```xml
<properties>
    <maven.compiler.release>17</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <gson.version>2.10.1</gson.version>
    <junit.version>5.10.2</junit.version>
</properties>
```
- `<maven.compiler.release>17</maven.compiler.release>`: Enforces **Java 17**. If anyone tries to compile with incompatible newer language features, the compiler rejects it immediately.
- Centralizes library version numbers so updating a library requires changing only one line.

### 3. Dependencies (Automated Download)
```xml
<dependencies>
    <!-- JSON parsing for AI response -->
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>${gson.version}</version>
    </dependency>

    <!-- Unit testing -->
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>${junit.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```
- When Maven reads this, it automatically connects to the internet, downloads Gson and JUnit 5, and adds them to your compilation classpath.
- `<scope>test</scope>`: Guarantees that JUnit 5 is only available when testing, preventing production code in `src/main` from accidentally depending on test helpers.

### 4. Build Plugins (Automation Engines)
```xml
<build>
    <plugins>
        <!-- 1. Compiler Plugin: compiles Java 17 code -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.11.0</version>
        </plugin>

        <!-- 2. Surefire Plugin: discovers and executes all JUnit 5 tests -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.2.5</version>
        </plugin>

        <!-- 3. Shade Plugin: bundles Gson directly inside target/medfinder.jar -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-shade-plugin</artifactId>
            <version>3.5.2</version>
            <configuration>
                <transformers>
                    <transformer implementation="...ManifestResourceTransformer">
                        <mainClass>medfinder.Main</mainClass>
                    </transformer>
                </transformers>
            </configuration>
        </plugin>
    </plugins>
</build>
```
- `maven-compiler-plugin`: Replaces hundreds of manual `javac` commands.
- `maven-surefire-plugin`: Automatically runs every test file ending in `*Test.java` (like `TextSimilarityTest`, `PharmacyTest`).
- `maven-shade-plugin`: Solves the runnable JAR problem. It bundles the Gson library directly into `target/medfinder.jar` and configures `medfinder.Main` as the entrypoint. Anyone can run the app with `java -jar target/medfinder.jar` without installing any external libraries!

---

## 6. Summary: Quick Reference

| Question | Answer |
|---|---|
| **What does POM stand for?** | Project Object Model. |
| **Where does it live?** | In the root folder of the project (`pom.xml`). |
| **Is it mandatory?** | Yes. Maven cannot build, compile, test, or package without it. |
| **What are its 4 main jobs?** | 1. Define project identity & Java 17 rules.<br>2. Automatically download dependencies (Gson, JUnit).<br>3. Compile and execute unit tests.<br>4. Package the runnable `target/medfinder.jar`. |
| **What happens without it?** | You would have to download JARs manually, type massive `javac` commands, and write custom scripts to bundle executable JARs. |
