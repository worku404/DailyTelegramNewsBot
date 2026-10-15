SEED_TOPICS = [
    # --- Requirement Analysis: Understanding client and user needs ---
    "Functional vs. non-functional requirements, and why NFRs are the ones that sink projects",
    "Elicitation techniques (interviews, workshops, observation) and the bias each one introduces",
    "The ambiguity problem: 'the system should be fast' is not a requirement until it's measurable",
    "Requirements traceability: linking every requirement back to a stakeholder and forward to a test",
    "Prioritization with MoSCoW, and the political fight hiding inside 'Must vs. Should'",

# --- System Design: Translating requirements into architecture and module interactions ---
    "High-level vs. low-level design, and the trap of jumping to code before boundaries exist",
    "Coupling and cohesion: the subtle one is why low coupling sometimes costs you high cohesion",
    "Architectural styles (layered, microservices, event-driven) and the trade-off each forces",
    "Separation of concerns and the Single Responsibility Principle at the module level",
    "Designing the interfaces/contracts between modules before their internals",

# --- Implementation: Writing clean, efficient, and maintainable code ---
    "Readability over cleverness: code is read far more often than it is written",
    "Naming, consistency, and coding standards (why a style guide beats individual taste)",
    "DRY vs. premature abstraction, and the cost of the wrong abstraction",
    "Error handling and defensive programming: failing loudly vs. failing silently",
    "Version control discipline: small commits, meaningful messages, and reviewable diffs",

# --- Testing: Unit, integration, and system testing to ensure correctness ---
    "The test pyramid: many unit, fewer integration, fewest end-to-end, and why inverting it hurts",
    "Unit test isolation with mocks and stubs (the subtle one: mocking too much tests nothing)",
    "Integration testing and the class of bugs that only appear when modules actually talk",
    "Black-box vs. white-box testing, and boundary/edge-case selection",
    "Regression testing and code coverage as a signal, not a goal",

# --- Deployment and Maintenance: Launching software and managing updates ---
    "CI/CD pipelines: automating build, test, and release to shrink the blast radius",
    "Deployment strategies (blue-green, canary, rolling) and how each trades risk for speed",
    "Monitoring, logging, and observability: you can't maintain what you can't see",
    "The four types of maintenance: corrective, adaptive, perfective, preventive",
    "Rollback and versioning: a safe way back is part of going forward",
    # --- Data Structures & Algorithms (general, Python-illustrated) ---
    "Hash tables: collision resolution (chaining vs. open addressing)",
    "Big-O vs. Big-Theta vs. Big-Omega: what each actually asserts",
    "Amortized analysis: why list.append is O(1) on average",
    "Binary search invariants and the off-by-one traps",
    "When a hash map beats sorting, and when it doesn't",
    
    # --- Concurrency & Async ---
    "Concurrency vs. parallelism: the distinction that matters",
    "Race conditions and why they're nondeterministic",
    "Deadlock: the four Coffman conditions",
    "asyncio: cooperative scheduling and the event loop",

    # --- Databases ---
    "ACID properties, one at a time (isolation is the subtle one)",
    "Database indexing: why a B-tree, and the read/write trade-off",
    "The N+1 query problem and how ORMs cause it",
    "Optimistic vs. pessimistic locking",

    # --- Systems / OS / Networking ---
    "How a TCP handshake actually establishes a connection",
    "Blocking vs. non-blocking I/O",
    "How you leak memory in a garbage-collected language",
    "Caching strategies and cache invalidation (the two hard problems)",

    # --- Software Engineering practice / Design ---
    "Idempotency and why it matters for retries",
    "The difference between coupling and cohesion",
    "Dependency inversion: depend on abstractions, not concretions",
    "Fail-fast vs. fail-safe error handling philosophies",
    "Exponential backoff and jitter",

    # --- Testing ---
    "The test pyramid, and why UI-heavy testing is a trap",

        # --- Python language internals (Python-specific, advanced) ---
    "The GIL: what it actually locks and what it doesn't",
    "Generators and lazy evaluation: memory-bounded iteration",
    "Decorators: functions that return functions, and functools.wraps",
    "Context managers and the with protocol (__enter__/__exit__)",
    "Mutable default arguments: the classic footgun and why it happens",
    "__slots__ and the memory cost of dynamic attributes",
    "Duck typing vs. structural typing (Protocol)",
    "Shallow vs. deep copy and reference semantics",
]