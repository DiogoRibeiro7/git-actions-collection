import os


def get_message() -> str:
    return os.getenv("APP_MESSAGE", "Hello from Docker")


def main() -> None:
    print(get_message())


if __name__ == "__main__":
    main()
