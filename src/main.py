from src.views import main_response


def main() -> str:
    x = main_response("2025-04-30 23:59:59")
    return x


if __name__ == "__main__":
    print(main())
