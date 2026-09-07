SEED_TOPICS = [
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