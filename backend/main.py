from src.auth.repository import AuthRepository

def main():
    auth = AuthRepository()
    auth._write({"name":"monish"})
    print("Hello from landlord!")


if __name__ == "__main__":
    main()
