import os
import json
import argparse
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import ntplib

# Function to fetch time from an NTP server
def get_ntp_time() -> datetime:
    """Fetch the current time from an NTP server and convert it to Indian Standard Time (IST)."""
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')  # You can change the server if needed
    utc_time = datetime.utcfromtimestamp(response.tx_time)
    
    # IST is UTC + 5 hours 30 minutes
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    
    return ist_time

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

def create_metadata(file_path: str, unlock_time: str) -> None:
    """Create or update the lock metadata file."""
    metadata = {
        "file_path": file_path,
        "unlock_time": unlock_time
    }
    with open("lock_metadata.json", "w") as metadata_file:
        json.dump(metadata, metadata_file)

def read_metadata() -> dict:
    """Read the lock metadata file."""
    if not os.path.exists("lock_metadata.json"):
        return {}
    
    with open("lock_metadata.json", "r") as metadata_file:
        return json.load(metadata_file)

def lock_file(file_path: str, lock_duration: int) -> None:
    """Lock a file by encrypting it."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    key = generate_key()

    # Save the key to a file for later use in unlocking
    with open("file_key.key", "wb") as key_file:
        key_file.write(key)

    # Fetch NTP time and calculate unlock time based on it
    current_time = get_ntp_time()
    unlock_time = current_time + timedelta(seconds=lock_duration)
    unlock_time_str = unlock_time.isoformat()

    # Create metadata
    create_metadata(file_path, unlock_time_str)

    # Encrypt the file
    encrypt_file(file_path, key)
    print(f"File '{file_path}' is now locked. It will unlock at {unlock_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.")

def unlock_file(file_path: str) -> None:
    """Unlock a file by decrypting it."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    metadata = read_metadata()

    if not metadata or metadata["file_path"] != file_path:
        print(f"Error: No metadata found for the file '{file_path}'.")
        return

    unlock_time = datetime.fromisoformat(metadata["unlock_time"])

    # Fetch NTP time for current time
    current_time = get_ntp_time()

    if current_time < unlock_time:
        print(f"File is still locked. It will unlock at {unlock_time} UTC. Current time: {current_time} UTC.")
        return

    if not os.path.exists("file_key.key"):
        print("Error: No key found to unlock the file.")
        return

    key = load_key()
    decrypt_file(file_path, key)
    os.remove("file_key.key")  # Remove the key after decryption
    os.remove("lock_metadata.json")  # Remove metadata after unlocking
    print(f"File '{file_path}' has been unlocked.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lock or unlock a file.")
    parser.add_argument("command", choices=["lock", "unlock"], help="Command to lock or unlock a file.")
    parser.add_argument("file_path", type=str, help="Path to the file.")
    parser.add_argument("time", type=int, nargs="?", help="Lock duration in seconds (only for 'lock' command).")

    args = parser.parse_args()

    if args.command == "lock":
        if not args.time:
            print("Error: Lock duration must be specified for 'lock' command.")
            exit(1)
        lock_file(args.file_path, args.time)
    elif args.command == "unlock":
        unlock_file(args.file_path)
