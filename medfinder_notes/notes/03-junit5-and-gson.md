# JUnit 5 and Gson — The Two External Libraries (Chapters 1 & 3)

> **Chapter:** 1.1 Program Development & Problem Solving (Testing), 1.3 Low Coupling, 3.7 Packages | **In MedFinder:** `pom.xml`, `medfinder.ai.AiResponseParser` (Gson), `src/test/java/medfinder/` (JUnit 5) | **Source:** MedFinder core foundation

## What is it?

MedFinder is allowed exactly two external libraries. Every other utility we need, we write ourselves.

**Gson** is a library from Google that converts between Java objects and JSON text. The two directions have names: turning a Java object into a JSON string is **serialization**; turning a JSON string back into a Java object is **deserialization**. We use Gson only for deserialization — the AI returns a JSON string, and Gson parses it into a Java object we can work with.

**JUnit 5** is a testing framework. It gives us `@Test` annotations, assertion methods like `assertEquals`, and the machinery to run those tests automatically. It has nothing to do with the app itself; it only exists to verify that the app behaves correctly.

## Why do we need it?

Without Gson, parsing JSON by hand means splitting strings, hunting for curly braces, and writing brittle code that breaks the moment the AI tweaks its formatting. Gson handles all of that reliably, in one method call, in a well-tested library.

Without JUnit 5, verifying that `medfinder.logic.TextSimilarity.levenshtein` or `medfinder.ai.AiResponseParser.parse` works correctly means running the whole app, triggering an AI call, and reading the output with your eyes. That's slow, unrepeatable, and catches nothing automatically. JUnit lets us write a small focused test for each method and run all of them in seconds with `mvn test`.

The reason we're limited to these two is coupling. Every external library is a dependency that can change, break, or introduce a vulnerability. The fewer we take, the less surface area we're responsible for.

## How it works

JUnit 5's model is simple: you annotate a method with `@Test`, call the code you want to verify, and use an assertion to state what the result should be. If the assertion is wrong, the test fails and Maven reports it. The key detail is that JUnit is `<scope>test</scope>` in `pom.xml`, which means Maven puts it on the classpath only during the test phase and never includes it in `target/medfinder.jar`.

Gson's model is also simple: you create a `Gson` instance and call `fromJson(jsonString, TargetClass.class)`. Gson uses Java reflection to read the field names of `TargetClass` and fill them from the matching keys in the JSON. It is `compile` scope in `pom.xml` because the production code calls it at runtime.

## How MedFinder uses it

**Situation:** the AI returns a JSON string and we need to turn it into a usable Java object without writing a manual parser.

```java
// medfinder/ai/AiResponseParser.java
public class AiResponseParser {
    private static final Gson GSON = new Gson();

    public AiResponse parse(String rawJson) {
        AiResponse response = GSON.fromJson(rawJson, AiResponse.class);
        if (response == null || response.medications() == null) {
            throw new IllegalArgumentException("AI returned unparseable JSON");
        }
        return response;
    }
}
```

**Walkthrough:** `GSON.fromJson(rawJson, AiResponse.class)` hands the raw JSON string and a class blueprint to Gson. Gson uses reflection to map each JSON key to a matching field in `AiResponse` and returns a filled-in instance. The null-check immediately after is not optional — LLMs can return malformed JSON, truncated output, or plain English instead of JSON. Trusting the raw response without validation would let garbage propagate into the rest of the system. Gson is imported here, in `medfinder.ai`, and nowhere else in the codebase.

**Situation:** we need to verify that `AiResponseParser.parse` correctly rejects a response where the medications list is missing.

```java
// src/test/java/medfinder/ai/AiResponseParserTest.java
class AiResponseParserTest {
    private final AiResponseParser parser = new AiResponseParser();

    @Test
    void parse_throwsOnMissingMedications() {
        String badJson = "{\"summary\": \"ok\"}"; // medications key absent
        assertThrows(
            IllegalArgumentException.class,
            () -> parser.parse(badJson)
        );
    }
}
```

**Walkthrough:** `@Test` tells JUnit 5 this method is a test case. `assertThrows` runs the lambda and expects an `IllegalArgumentException` to be thrown. If `parse` returns normally instead, the assertion fails and Maven marks the test red. This test lives in `src/test/java/medfinder/ai/`, which mirrors the production package. JUnit never appears in production source — it stays entirely inside `src/test/`.

## Common mistakes

- **Importing Gson in a model or service class.** Gson belongs exclusively in `medfinder.ai.AiResponseParser`. Letting it spread to `medfinder.model` or `medfinder.service` violates the low-coupling principle — now multiple packages depend on an external library, making it harder to swap out later.
- **Trusting the raw LLM JSON without validation.** `fromJson` returns `null` if the input is completely unparseable, and it happily returns an object with null fields if the JSON is missing keys. Always validate the result before using it.
- **Forgetting `<scope>test</scope>` on JUnit.** Without it, JUnit is bundled into the production jar and available in production code — neither of which is intended. It also signals to anyone reading `pom.xml` that JUnit is a runtime dependency, which is wrong.
- **Writing tests in `src/main/java/`.** Maven treats that folder as production code. Tests must live in `src/test/java/` so the surefire plugin finds them and so they're excluded from the production jar.

## Summary

Gson and JUnit 5 are the only two external libraries in MedFinder, and their scopes reflect their roles. Gson is `compile` scope because `medfinder.ai.AiResponseParser` calls it in production to deserialize AI responses; it is deliberately confined to the `medfinder.ai` package to keep coupling low. JUnit 5 is `test` scope because it exists only to verify behaviour during `mvn test`; it never enters the production jar. Using them correctly — right scope, right package — keeps the codebase small, predictable, and easy to audit.
