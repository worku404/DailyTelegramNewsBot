# What is pom.xml? (Chapters 1 & 2)

> **Chapter:** 1.1 Program Development & Problem Solving, 2.1 Compiling & Running Java Programs, 2.2 The Java Execution Environment & JVM Internals | **In MedFinder:** `pom.xml` (project root) | **Source:** MedFinder core foundation

## What is it?

`pom.xml` stands for **Project Object Model**. It is a single XML file that sits at the root of the project and tells Maven everything it needs to know: who the project is, what Java version it targets, which external libraries it depends on, and which build plugins to run.

Think of it as a contract. Every teammate, every CI server, and every deployment pipeline reads the same file and produces an identical build. Nothing about the build lives in anyone's head or on anyone's machine alone.

## Why do we need it?

Imagine the five of us building MedFinder without `pom.xml`. One person downloads Gson 2.10.1, another downloads 2.8.9. The JSON parsing code works for the first person and silently produces wrong output for the second because the APIs changed between versions. Meanwhile, we're passing around fat `.jar` files over Slack and committing them to Git, which bloats the repository. When we try to run the tests, half the team can't because JUnit isn't on the classpath. `pom.xml` fixes all of this in one place: declare a library once, pin its version, and every machine gets exactly that version.

## How it works

1. Maven reads `pom.xml` at the start of every build.
2. The **coordinates** (`<groupId>`, `<artifactId>`, `<version>`) uniquely identify our project — like an address in the Maven world. Other projects could depend on us using these three values.
3. The **properties** section sets global variables. We set `<java.version>17</java.version>` and `<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>` here so that every plugin reads the same value from one place.
4. The **dependencies** section lists external libraries. Each has its own coordinates plus an optional `<scope>`. Scope controls when the library is available: `compile` (the default) means it's on the classpath at compile time and bundled into the jar; `test` means it's only available during `mvn test` and is never bundled into the production jar.
5. The **build plugins** section configures the tools Maven calls during the build lifecycle. We use three: `maven-compiler-plugin` (tells `javac` to use Java 17), `maven-surefire-plugin` (runs JUnit 5 tests), and `maven-shade-plugin` (bundles our classes and Gson into one fat jar).

## How MedFinder uses it

**Situation:** we need Gson at runtime (the app parses AI responses in production) but JUnit only during testing (we never ship test code to users).

```xml
<dependencies>
  <dependency>
    <groupId>com.google.code.gson</groupId>
    <artifactId>gson</artifactId>
    <version>2.10.1</version>
    <!-- no <scope> tag = compile scope = bundled into the jar -->
  </dependency>

  <dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.10.2</version>
    <scope>test</scope>
  </dependency>
</dependencies>
```

**Walkthrough:** Gson has no `<scope>` tag, so Maven uses the default: `compile`. That means Gson is on the classpath when `javac` compiles our production code and it gets bundled into `target/medfinder.jar` by the shade plugin — which is what we want, because `medfinder.ai.AiResponseParser` calls Gson at runtime. JUnit has `<scope>test</scope>`, so Maven puts it on the classpath only when running `mvn test`. It is never included in the production jar. Shipping JUnit to users would add dead weight and expose test infrastructure that has no business being in a production binary.

**Situation:** we need to produce a single runnable jar that includes Gson, with `medfinder.Main` as the entry point.

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-shade-plugin</artifactId>
  <version>3.5.2</version>
  <configuration>
    <transformers>
      <transformer implementation=
        "org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
        <mainClass>medfinder.Main</mainClass>
      </transformer>
    </transformers>
  </configuration>
</plugin>
```

**Walkthrough:** When you run `mvn package`, the shade plugin merges our compiled `.class` files and all compile-scope dependencies (Gson) into one jar. The `ManifestResourceTransformer` writes a `MANIFEST.MF` file inside the jar that declares `Main-Class: medfinder.Main`. That's what lets you run `java -jar target/medfinder.jar` — without the manifest entry, the JVM wouldn't know where to start.

## Common mistakes

- **Giving JUnit compile scope (or no scope).** JUnit ends up bundled into the production jar and available to production code — neither of which is intentional. Always add `<scope>test</scope>`.
- **Omitting the UTF-8 encoding property.** Without `<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>`, `javac` falls back to the platform default, which differs across operating systems. String literals with accented characters compile correctly on one machine and corrupt on another.
- **Adding a dependency that isn't in the assignment spec.** The project has an approved dependency list. Adding anything else — even a seemingly harmless utility library — is a rules violation. If you need a utility, write it yourself in a class like `medfinder.logic.TextSimilarity`.
- **Not pinning plugin versions.** If you omit `<version>` on a plugin, Maven picks the latest available. The build that passes today may break tomorrow when a new plugin version changes behaviour. Always pin.

## Summary

`pom.xml` is the single source of truth for the MedFinder build. Its four sections — coordinates (who we are), properties (Java 17, UTF-8), dependencies (Gson at compile scope, JUnit 5 at test scope), and plugins (compiler, surefire, shade) — give every teammate and every machine an identical, reproducible build. The shade plugin is what turns our compiled classes and Gson into the runnable `target/medfinder.jar`, and the scope system is what keeps test infrastructure out of that jar.
