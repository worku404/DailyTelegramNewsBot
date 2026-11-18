# What are JUnit 5 and Gson 2.10.1, and Why Do We Need Them?

> **Personal Study Notes** — Kept in `notes/` (git-ignored, private learning documentation).

In our project's `pom.xml`, there are **only two external libraries** allowed in the entire system:
```xml
<!-- Only two libraries are allowed in this project: Gson and JUnit 5. -->
<dependencies>
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>2.10.1</version>
    </dependency>

    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

Here is everything you need to know about what they are, why they are there, and what happens without them.

---

# Part 1: JUnit 5 (Version 5.10.2)

## 1. What is JUnit 5 in Plain English?

**JUnit 5** is the industry-standard **automated unit testing framework** for Java.

In programming:
- A **unit test** is a small piece of code written by developers to verify that an individual method or class works exactly as intended under different conditions (normal cases, edge cases, and error cases).
- **JUnit 5** provides the annotations (like `@Test`) and assertions (like `assertEquals`) that allow Maven to automatically run all tests whenever you type `mvn test` or `mvn clean test`.

## 2. Why Do We Need JUnit 5 in MedFinder?

MedFinder has complex business logic:
- Calculating Levenshtein string distance in `TextSimilarity`.
- Classifying stock freshness into `FRESH`, `AGING`, and `STALE` based on hours in `FreshnessClassifier`.
- Validating immutable `Location` equality.
- Parsing AI JSON responses in `AiResponseParser`.

Without JUnit 5, every time you make a change to the code, you would have to manually run the program, type console inputs by hand, and verify outputs with your eyes. **JUnit tests run in 0.2 seconds and verify hundreds of scenarios automatically.**

## 3. Where is JUnit 5 Used in Our Project?

Notice the `<scope>test</scope>` tag in `pom.xml`. This means JUnit 5 code is **strictly forbidden inside `src/main`** (production code). It is only used inside `src/test/java/medfinder/`:

| Test Class | Owner | What it tests |
|---|---|---|
| `logic/TextSimilarityTest.java` | P1 (Worku) | Levenshtein distance formula, normalisation, typo handling (e.g. "amoxcillin" matching "Amoxicillin") |
| `logic/FreshnessClassifierTest.java` | P4 (Tesnim) | Exact boundary tests at 12 hours and 48 hours |
| `model/LocationTest.java` | P4 (Tesnim) | Sub-city case-insensitivity, equality, and hash code |
| `model/PharmacyTest.java` | P4 (Tesnim) | State transition validation (Pending -> Verified -> Rejected) |
| `ai/AiResponseParserTest.java` | P2 (Tensaye) | Parsing valid JSON, fenced JSON, unsupported intent, fallback |
| `ai/AiAssistantServiceTest.java` | P2 (Tensaye) | Resilience and fallback behavior using `FakeLlmClient` |

## 4. Key JUnit 5 Features You Will See in the Code

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FreshnessClassifierTest {

    @Test
    void testUnder12HoursIsFresh() {
        // Assert that 5 hours age results in Freshness.FRESH
        assertEquals(Freshness.FRESH, FreshnessClassifier.classify(5));
    }

    @Test
    void testInvalidNegativeHoursThrowsException() {
        // Assert that passing -1 throws a ValidationException
        assertThrows(ValidationException.class, () -> {
            FreshnessClassifier.classify(-1);
        });
    }
}
```

- `@Test`: Marks a method as an automated test case for Maven Surefire to run.
- `assertEquals(expected, actual)`: Fails the build if the values don't match.
- `assertTrue(...)` / `assertFalse(...)`: Verifies boolean flags.
- `assertThrows(Exception.class, ...)`: Verifies that an operation properly refuses bad input.

## 5. What Happens Without JUnit 5?
- You cannot automate testing.
- You have to test everything manually by typing into the terminal.
- A bug introduced by one member could break someone else's code unnoticed until presentation day!

---

# Part 2: Gson 2.10.1 (by Google)

## 1. What is Gson in Plain English?

**Gson** is an open-source Java library developed by Google that converts **Java Objects into JSON**, and **JSON text into Java Objects**.
- **Serialization:** Java Object ➔ JSON string (e.g. `{ "name": "Amoxicillin", "price": 120.0 }`)
- **Deserialization:** JSON string ➔ Java Object

## 2. Why Do We Need Gson in MedFinder?

MedFinder integrates with a real Large Language Model (LLM / AI API) in task T22–T27. 
When a user asks:
> *"I have a fever and need paracetamol in Bole sub-city"*

The AI returns a structured JSON response:
```json
{
  "kind": "SEARCH",
  "keywords": ["paracetamol"],
  "subCity": "Bole",
  "notice": null
}
```

Java does not natively understand JSON strings without string parsing. **Gson converts that raw JSON response into our Java class `AiOutcome` in a single line of code:**

```java
Gson gson = new Gson();
AiOutcome outcome = gson.fromJson(jsonResponseText, AiOutcome.class);
```

## 3. Where is Gson Used in Our Project?

Per document `03-architecture-and-folder-structure.md` (Section 2 & Section 4), **Gson is strictly isolated**:
- It is **ONLY allowed in the `medfinder.ai` package** (primarily `AiResponseParser.java`).
- No other package (model, repository, service, console) is allowed to import or touch Gson! This prevents the rest of the application from being tightly coupled to an external JSON library.

## 4. What Happens Without Gson?
- Without Gson, you would have to write raw string parsing logic with `indexOf("keywords")`, `substring()`, and string splitting to parse JSON responses from the AI.
- Doing manual JSON string manipulation is notoriously fragile: if the AI adds a space or changes quotation marks, manual string parsing crashes instantly. Gson handles whitespace, formatting variations, character escaping, and type mapping cleanly and safely.

---

# Summary Comparison Table

| Aspect | JUnit 5 (`junit-jupiter`) | Gson (`gson`) |
|---|---|---|
| **What is it?** | Automated unit testing framework | JSON serialization / deserialization library |
| **Creator** | JUnit team | Google |
| **Project Scope** | `<scope>test</scope>` (Testing only) | Production runtime (Compile / Package) |
| **Where allowed?** | `src/test/java/medfinder/` only | `medfinder.ai` package only |
| **Why MedFinder needs it?** | Proves our 57 classes, algorithms, and business rules work automatically on `mvn test`. | Converts AI API JSON responses into strongly-typed Java `AiOutcome` objects. |
| **What if missing?** | Must test 57 classes by hand; regression bugs go unnoticed. | Must write manual, brittle string parsers for AI responses. |
