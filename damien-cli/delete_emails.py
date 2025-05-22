#!/usr/bin/env python3
import os
import sys
import subprocess
import time

# IDs of emails to delete
email_ids = [
    "196e9cd3c6c5b537", "196e9cb07d8925e8", "196e9b7b04a986c2", "196e9b75372d689b",
    "196e9b62a16cd020", "196e9b51c91384af", "196e9b21b4bf5c09", "196e9ae6f59c83c5",
    "196e9a99849ca738", "196e9a72b77bbead", "196e99e3b0c064d8", "196e9992dca4cae7",
    "196e9930b002b4a3", "196e98fd64e76a51", "196e98d24698dd33", "196e98c9bac5336c",
    "196e986878eb1c0c", "196e983668bbb047", "196e9821b5dcd8fb", "196e980a788f1593"
]

# Path to Poetry
poetry_path = "/Users/ivanrivera/.local/bin/poetry"

# Function to permanently delete emails
def permanent_delete(ids):
    ids_str = ",".join(ids)
    cmd = f"{poetry_path} run damien emails delete --ids \"{ids_str}\""
    
    # Use pexpect-like approach with subprocess
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for first confirmation prompt
    time.sleep(1)
    process.stdin.write("y\n")
    process.stdin.flush()
    
    # Wait for YESIDO prompt
    time.sleep(1)
    process.stdin.write("YESIDO\n")
    process.stdin.flush()
    
    # Wait for final confirmation
    time.sleep(1)
    process.stdin.write("y\n")
    process.stdin.flush()
    
    # Get output
    stdout, stderr = process.communicate()
    
    # Return result
    return stdout, stderr, process.returncode

if __name__ == "__main__":
    # Change to project directory
    os.chdir("/Users/ivanrivera/Downloads/AWS/DamienPlatform/damien_cli_project/")
    
    # Permanently delete emails
    stdout, stderr, return_code = permanent_delete(email_ids)
    
    # Print result
    print("Return code:", return_code)
    print("Output:", stdout)
    if stderr:
        print("Errors:", stderr)
