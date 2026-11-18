# HTTP Client and Network Requests (Chapter 2)

> **Chapter:** 2.6 Core Library Classes & Standard Utilities | **In MedFinder:** `GeminiConnectionTest.java` | **PR:** #4 by @Tensaye-Daniel

## What is it?
An **HTTP Client** is a tool provided by the Java standard library that allows your program to communicate with web services over the internet. It acts as a messenger, sending requests to a server and receiving responses back. Think of it like a postal service where you package a letter (the request), send it to a specific address (the URI), and wait for the recipient to send a reply back (the response).

## Why do we need it?
In MedFinder, we need to connect to external AI services like Gemini to process medical data. Without an HTTP client, our application would be isolated on the user's machine, unable to fetch data or send information to the outside world. If we tried to build this manually using low-level network sockets, we would face complex issues like managing connection timeouts, handling security headers, and parsing raw data streams, which would lead to unstable and unmaintainable code.

## How it works
1. You create an `HttpClient` instance, which acts as the engine for your network operations.
2. You build an `HttpRequest` object, specifying the destination address (URI), the request method (like POST), and any necessary headers (like content type).
3. You use the client to send the request, which returns an `HttpResponse` object containing the server's status code and the data returned.
4. The process is typically synchronous, meaning your program waits for the server to reply before continuing.

## How MedFinder uses it
### Sending Requests to Gemini
**Situation:** We need to send a JSON payload to the Gemini API to verify our connection.
**Code:**
```java
HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(20))
        .build();

HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(url))
        .timeout(Duration.ofSeconds(60))
        .header("Content-Type", "application/json")
        .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
        .build();

HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
```
**Walkthrough:** We configure the `HttpClient` with a 20-second connection timeout. We then build an `HttpRequest` that targets the Gemini API URL and sets the `Content-Type` header to `application/json`. Finally, we use `client.send()` to perform the network call. If we did not use these standard classes, we would have to manually implement the HTTP protocol, which is error-prone and inefficient.

## Common mistakes
One common mistake is forgetting to set a timeout. If the server is slow or the network is down, your program might hang indefinitely, waiting for a response that never arrives. Always use `.timeout()` to ensure your application remains responsive.

## Summary
The `HttpClient` class provides a robust way for Java applications to interact with web services. By using standard request and response objects, we can easily send data to APIs like Gemini and handle the results. This enables MedFinder to integrate with external intelligence while keeping our network logic clean and reliable.
