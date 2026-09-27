package example;

/** Consumer fixture for the gradle-build self-test. */
public final class Greeter {
    private Greeter() {}

    public static String greet(String name) {
        return "Hello, " + name;
    }
}
