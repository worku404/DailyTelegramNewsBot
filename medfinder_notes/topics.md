Chapter 1: Introduction to OOP & Programming Paradigms
1.1 Program Development & Problem Solving
Problem-solving phases and algorithm formulation
Program development lifecycle: Problem analysis, program design, coding/implementation, testing & debugging, and maintenance
Evolution of programming languages: Machine language, Assembly language, High-level languages
1.2 Programming Paradigms
Imperative / Procedural Paradigm (state mutation, sequential execution, routines/functions, Fortran, C, Pascal)
Functional Paradigm (pure functions, mathematical evaluation, immutability, Lisp, Haskell)
Declarative / Logic Paradigm (rule-based evaluation, predicate logic, Prolog, SQL)
Object-Oriented Paradigm (objects, message passing, encapsulation, Simula, Smalltalk, C++, Java)
Architectural comparison: Procedural decomposition vs. Object-Oriented decomposition
1.3 Software Architecture & The Software Crisis
The Software Crisis and limitations of procedural code
Software architectural metrics: High cohesion vs. tight coupling
1.4 Core Pillars of Object-Oriented Programming
Fundamental concepts: Objects (state, behavior, identity) and Classes (templates/blueprints)
Abstraction: Data abstraction, information hiding, and separating interface from implementation
Encapsulation: Bundling attributes and behaviors, state hiding, and invariant enforcement
Inheritance: Taxonomic generalization, base/derived classes, and code reuse
Polymorphism: Unified interfaces with distinct behaviors, dynamic binding, and late binding
Chapter 2: Basics of Java, JVM Architecture & Control Statements
2.1 Java Overview & Platform Architecture
Definition, origin, and history of Java (James Gosling, Sun Microsystems)
Java program types: Standalone Applications vs. Applets
Core Java architectural features: Simple, Object-Oriented, Distributed, Interpreted, Robust, Secure, Architecture-Neutral, Portable, High-Performance, Multithreaded, Dynamic
2.2 The Java Execution Environment & JVM Internals
Java execution pipeline: Source code (.java) 
→
→ Compiler (javac) 
→
→ Bytecode (.class) 
→
→ JVM execution
ClassLoader Subsystem: Delegation model, Bootstrap, Extension/Platform, and Application class loaders
Bytecode Verifier and Security Manager
Execution Engine: Interpreter and Just-In-Time (JIT) Compiler
JVM Runtime Memory Model: Metaspace / Method Area, Stack frames (local variables, operand stack), Heap memory, and Garbage Collection (GC)
2.3 Java Syntax & Program Structure
Program anatomy: package declaration, import statements, class definition, and the entry point (public static void main(String[] args))
Identifiers, naming conventions, and Java keywords / reserved words
Comments: Single-line (//), Multi-line (/* */), and Javadoc documentation comments (/** */)
Variables, memory representation, and constants (final modifier)
Primitive Data Types: Integral types (byte, short, int, long), Floating-point types (float, double, IEEE-754 precision), Character type (char), and Boolean type (boolean)
Reference types vs. Primitive types
Type Conversion & Type Casting: Widening conversion (implicit) vs. Narrowing conversion (explicit)
Standard output & formatting: System.out.print(), System.out.println(), and escape sequences (\n, \t, \", \\, etc.)
2.4 Operators & Expressions
Arithmetic operators (+, -, *, /, %) and unary increment/decrement operators (++, --)
Relational / comparison operators (==, !=, <, >, <=, >=)
Logical operators (&&, ||, !) and short-circuit evaluation
Assignment and compound assignment operators (=, +=, -=, *=, /=, %=)
Bitwise and bit-shift operators
2.5 Control Flow & Branching
Conditional branching: if, if...else, nested if, and if...else if...else ladder
Multi-way selection: switch statement, case, break, default, and bytecode branching mechanics (tableswitch vs. lookupswitch)
Iteration statements / Loops: while loop, do...while loop, standard counter-controlled for loop, and nested loops
Jump statements: break and continue (labeled and unlabeled)
2.6 Core Library Classes & Standard Utilities
User console input: java.util.Scanner
Mathematical utilities: java.lang.Math (sqrt, pow, abs, random, max, min, PI, E)
System utilities: System.arraycopy, System.currentTimeMillis()
2.7 Strings & Character Data
The String class and String immutability
The String Constant Pool (SCP) and memory deduplication
Common String operations: length(), charAt(), substring(), equals(), equalsIgnoreCase(), compareTo(), indexOf(), toLowerCase(), toUpperCase()
String concatenation (+) vs. mutable buffers (StringBuilder / StringBuffer)
2.8 Arrays & Memory Layout
Array declaration, instantiation, and initialization
Array indexing, length attribute (array.length), and contiguous heap memory layout
Bounds checking and ArrayIndexOutOfBoundsException
Array traversal: Traditional indexed for loop and enhanced for-each loop
Multidimensional arrays: 2D arrays, matrix representation, and jagged / ragged arrays
Array manipulation utilities: java.util.Arrays (sorting, searching, filling, string representation)
Chapter 3: Classes, Objects, Methods & Constructors
3.1 Class Anatomy & Object Lifecycle
Object-Oriented modeling: State (fields), Behavior (methods), and Identity
Class declaration syntax and structure
Object instantiation: new operator, heap memory allocation, and reference variables
Low-level object creation mechanics (new, dup, invokespecial)
Member access via the dot (.) operator
Object references vs. object instances, reference assignment, and null references
3.2 Variable Types & Scopes
Local variables (stack allocation, method scope, mandatory initialization)
Instance variables (heap allocation, object lifecycle, default initialization)
Class / Static variables (static keyword, Metaspace allocation, shared state)
3.3 Parameter Passing Architecture
Strict Pass-by-Value mechanism in Java (primitives by value vs. object references by value)
3.4 Encapsulation & Access Control
Class abstraction, information hiding, and invariant protection
The four access modifiers: private, default (package-private), protected, and public
Accessor methods (Getters) and Mutator methods (Setters)
Defensive copying: Protecting internal mutable state against external manipulation
3.5 Constructors & Initialization Pipelines
Constructor definition, characteristics, and syntax rules
Default / no-argument constructor vs. user-defined constructors
Parameterized constructors
Constructor overloading
The this keyword:
Resolving variable shadowing / name collisions (this.field = field)
Explicit constructor invocation and constructor chaining (this(...))
Passing and returning the current object instance
The 4-phase JVM object initialization pipeline (class loading, static initializers, instance initializers, constructor execution)
3.6 Methods & Static Architecture
Method declaration, parameter lists, return types, and method signatures
Instance methods vs. Static methods (class methods)
Dynamic method dispatch (invokevirtual) vs. static method dispatch (invokestatic)
Method Overloading (Compile-Time / Static Polymorphism):
Overloading rules, signature resolution priority, and type promotion
3.7 Packages, Namespaces & Modularity
Package concepts, namespace organization, and directory hierarchies
Standard built-in packages (java.lang, java.util, java.io, etc.)
User-defined packages and subpackages
Package imports (import) and Static imports (import static)
Chapter 4: Inheritance, Polymorphism & Abstract Classes / Interfaces
4.1 Inheritance Mechanics
Generalization and specialization concepts
Superclass / Base class / Parent class vs. Subclass / Derived class / Child class
Class derivation syntax using the extends keyword
The IS-A relationship and inheritance hierarchies
Subclass heap memory layout and inherited member accessibility
Single inheritance in Java and the Deadly Diamond Problem (multiple inheritance ambiguity)
4.2 The super Keyword & Constructor Chaining
Invoking superclass constructors (super(), super(args))
Top-down initialization order across class hierarchies
The implicit super() call trap
Accessing superclass members and shadowed fields (super.field)
Invoking overridden superclass methods (super.method())
4.3 Method Overriding & Runtime Polymorphism
Method Overriding definition: Dynamic redefinition of superclass methods
Overloading vs. Overriding distinction
The 5 compiler rules for overriding:
Identical method signatures
Covariant return types
Access visibility cannot be narrowed
Checked exception confinement (cannot throw broader or new checked exceptions)
Private, static, and final methods cannot be overridden
The @Override annotation
Field shadowing vs. method overriding
The Liskov Substitution Principle (LSP)
JVM Virtual Method Tables (vtables) and dynamic dispatch
Composition over Inheritance and the Fragile Base Class problem
4.4 The final Modifier
final variables (constants)
final methods (preventing method overriding; JIT compiler inlining)
final classes (preventing class extension / inheritance; immutability)
4.5 Abstract Classes & Abstract Methods
The abstract keyword
Abstract class characteristics (cannot be instantiated, can contain concrete state, methods, and constructors)
Abstract methods (method signatures without implementation; mandatory subclass implementation)
The Template Method design pattern
4.6 Interfaces & Contract Architecture
Interface definition and the interface keyword
Interface implementation via implements (single and multiple interface inheritance)
Traditional interface members (public abstract methods and public static final constants)
Modern interface extensions: default methods, static methods, and private helper methods
Interface default method diamond conflicts and the 3 resolution rules
Architectural comparison: Abstract Classes vs. Interfaces
Chapter 5: Polymorphism, Dynamic Binding & Type Systems
5.1 Foundations of Polymorphism
Definition and core philosophy ("many forms", programming in the general)
Early Binding (Static Binding / Compile-Time) vs. Late Binding (Dynamic Binding / Runtime)
Polymorphic method invocation: Superclass reference variables referencing subclass instances
Polymorphic behavior and dynamic method dispatch
5.2 Heterogeneous Collections & Software Architecture
Storing diverse subclass objects in common superclass collections / arrays
Uniform polymorphic processing of heterogeneous collections
The Open-Closed Principle (OCP): Extending functionality without altering client code
Polymorphism vs. Inheritance relationship
5.3 Reference Type Casting & Type Safety
Reference types vs. runtime object types
Upcasting (Widening reference conversion): Implicit, safe generalization
Downcasting (Narrowing reference conversion): Explicit specialization
Type safety hazards, JVM bytecode verification (checkcast), and ClassCastException
5.4 Type Introspection & Pattern Matching
The instanceof comparison operator for runtime type verification
Pattern matching for instanceof (type checking with automatic conditional binding)
Array Covariance vs. Generic Invariance (ArrayStoreException pitfalls)
Code smells and anti-patterns associated with excessive manual downcasting
Chapter 6: Exception Handling & Fault-Tolerant Systems
6.1 Principles of Exception Handling
Philosophy of exceptions: Separating error detection and handling from core business logic
Limitations of traditional error return codes vs. structured exception propagation
6.2 The Java Throwable Hierarchy
java.lang.Throwable root class and its two major branches:
java.lang.Error: Catastrophic system/JVM failures (OutOfMemoryError, StackOverflowError, VirtualMachineError)
java.lang.Exception: Programmatic, recoverable failure conditions
java.lang.RuntimeException: Programming bugs and logic errors
6.3 Checked vs. Unchecked Exceptions
Checked Exceptions (compile-time checked, mandatory catch-or-declare contract, e.g., IOException, SQLException)
Unchecked Exceptions (RuntimeException subclasses, optional catch, logic defects, e.g., NullPointerException, ArithmeticException, ArrayIndexOutOfBoundsException, IllegalArgumentException)
6.4 Exception Control Flow Mechanics
The try block: Isolating failure-prone operations
The catch block: Catching exceptions, parameter binding, and multi-catch hierarchy rules (subclasses before superclasses)
Multi-catch syntax (catch (TypeA | TypeB e)) and disjoint type constraints
The finally block: Guaranteed cleanup execution across normal, exceptional, and returning paths
Stack unwinding: JVM call stack frame destruction during exception propagation
The throw keyword: Explicitly instantiating and raising exception objects
The throws clause: Declaring checked exceptions in method signatures
6.5 Resource Management
The Try-with-Resources statement
The java.lang.AutoCloseable and java.io.Closeable interfaces
Automatic deterministic resource closure and suppressed exception handling
6.6 Custom Domain Exceptions & Enterprise Architecture
Defining custom checked and unchecked domain-specific exceptions
The four canonical constructors of Throwable
Exception Chaining: Preserving root cause diagnostics via initCause() and cause constructors (getCause())
Exception translation / wrapping across architectural layer boundaries
Anti-patterns: Swallowing exceptions (empty catch blocks), catching generic Throwable, log-and-rethrow cascades, and flow-control via exceptions