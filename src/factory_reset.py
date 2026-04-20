import os
import shutil

def perform_hard_reset():
    print("Removing Storage Directories")

    # Define target directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    targets = [
        # Dev mode paths (Deleting the parent dev_vault takes out both ram and storage)
        os.path.join(base_dir, "../dev_vault"),
        
        # Standard Raspberry Pi paths
        "/home/zero_monitor_storage",
        "/run/zero_monitor_decrypted"
    ]

    # Execution Loop
    for target in targets:
        if os.path.exists(target):
            try:
                shutil.rmtree(target)
                print(f"[SUCCESS] Deleted directory: {target}")
            except Exception as e:
                print(f"[ERROR] Could not delete {target}. Reason: {e}")
        else:
            print(f"[SKIPPED] Directory not found: {target}")

    print("Reset Complete.")

if __name__ == "__main__":
    perform_hard_reset()