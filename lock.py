import os
from cryptography.fernet import Fernet

def generate_key() -> bytes:
    """Generate and return an encryption key."""
    return Fernet.generate_key()

def load_key() -> bytes:
    """Load the encryption key from a file."""
    with open("file_key.key", "rb") as key_file:
        return key_file.read()

def encrypt_file(file_path: str, key: bytes) -> None:
    """Encrypt a file using the provided key."""
    with open(file_path, "rb") as file:
        data = file.read()
    encrypted_data = Fernet(key).encrypt(data)
    with open(file_path, "wb") as file:
        file.write(encrypted_data)

def decrypt_file(file_path: str, key: bytes) -> None:
    """Decrypt a file using the provided key."""
    with open(file_path, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = Fernet(key).decrypt(encrypted_data)
    with open(file_path, "wb") as file:
        file.write(decrypted_data)

def lock_file(file_path: str) -> None:
    """Lock a file by encrypting it."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    key = generate_key()

    # Save the key to a file for later use in unlocking
    with open("file_key.key", "wb") as key_file:
        key_file.write(key)

    encrypt_file(file_path, key)
    print(f"File '{file_path}' is now locked.")

def unlock_file(file_path: str) -> None:
    """Unlock a file by decrypting it."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    if not os.path.exists("file_key.key"):
        print("Error: No key found to unlock the file.")
        return

    key = load_key()
    decrypt_file(file_path, key)
    os.remove("file_key.key")  # Remove the key after decryption
    print(f"File '{file_path}' has been unlocked.")

if __name__ == "__main__":
    command: str = input("Enter command (lock/unlock): ").strip().lower()
    file_path: str = input("Enter file path: ").strip()

    if command == "lock":
        lock_file(file_path)
    elif command == "unlock":
        unlock_file(file_path)
    else:
        print("Invalid command. Please enter 'lock' or 'unlock'.")
