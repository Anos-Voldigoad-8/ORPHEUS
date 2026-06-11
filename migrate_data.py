import os
import json
import shutil
from pathlib import Path

# Create data dir
os.makedirs("data", exist_ok=True)

# Migrate users.json
if os.path.exists("users.json"):
    print("Migrating users.json...")
    shutil.move("users.json", "data/users.json")

# Migrate profiles.json
if os.path.exists("profiles.json"):
    print("Migrating profiles.json...")
    shutil.move("profiles.json", "data/profiles.json")

# Migrate workspace to admin if exists
admin_email = "lakshyasrivastava811@gmail.com"
admin_ws = Path(f"data/{admin_email}/workspace")

if os.path.exists("workspace") and os.path.isdir("workspace"):
    print(f"Migrating global workspace to {admin_ws}...")
    os.makedirs(admin_ws, exist_ok=True)
    for item in os.listdir("workspace"):
        src = os.path.join("workspace", item)
        dst = os.path.join(admin_ws, item)
        if not os.path.exists(dst):
            shutil.move(src, dst)
    # Don't delete workspace yet just in case, but it's migrated
    
print("Migration complete!")
