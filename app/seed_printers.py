from app.services.printer_service import printer_service


def main() -> None:
    result = printer_service.seed_from_yaml(only_if_empty=False)
    print(result)


if __name__ == "__main__":
    main()

