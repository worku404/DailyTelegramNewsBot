# System Environment and File I/O (Chapter 2)

> **Chapter:** 2.6 Core Library Classes & Standard Utilities | **In MedFinder:** `GeminiConnectionTest.java` | **PR:** #4 by @Tensaye-Daniel

## What is it?
**System environment variables** are key-value pairs stored by the operating system that provide configuration data to applications. **File I/O** (Input/Output) refers to the ability of a program to read from or write to files on the computer's storage. Together, these allow a program to adapt its behavior based on its surroundings without changing the source code.

## Why do we need it?
MedFinder requires an API key to talk to Gemini. We should not hardcode this sensitive key directly into our Java source code, as it would be insecure and difficult to update. We need a way to read this configuration from the environment or a local file (like `.env`) so that each developer can use their own credentials securely.

## How it works
1. `System.getenv(key)` allows you to retrieve a value set in the operating system's environment.
2. `java.nio.file.Files` and `java.nio.file.Path` provide a modern way to interact with the file system.
3. By checking for the existence of a file (like `.env`) and reading its lines, we can parse custom configuration settings at runtime.

## How MedFinder uses it
### Resolving Configuration
**Situation:** We need to find the API key from either an environment variable, a command-line argument, or a local `.env` file.
**Code:**
```java
private static String resolveApiKey(String[] args) {
    String fromEnv = System.getenv(ENV_VAR);
    if (fromEnv != null && !fromEnv.isBlank()) {
        return fromEnv.trim();
    }
    // ...
    return readDotEnv(ENV_VAR);
}
```
**Walkthrough:** The `resolveApiKey` method checks the system environment first. If the key is missing, it falls back to reading from a local file. This hierarchy ensures that the application is flexible. If we didn't use `System.getenv()`, we would be forced to hardcode the key, making it impossible to share the code safely.

## Common mistakes
Students often forget to handle the case where a file does not exist. Using `Files.isRegularFile(envFile)` before attempting to read is crucial to prevent the program from crashing with an exception when the configuration file is missing.

## Summary
Using environment variables and file reading allows MedFinder to be configurable and secure. By checking multiple sources for settings, we ensure the application is easy to set up for different users. This approach separates sensitive configuration from the application logic.
