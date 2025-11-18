def request_archive_path():
    print(f"Please input archive path:")
    path = input()
    return path

def notify_unknown_users(users: set[str]):
    print(f"Note! Found {len(users)} users:")
    for user in users:
        print(f"- {user}")
    print(f"Make sure you've created nicknames.txt file in you archive. Write down unknown users there, " + \
        "one for each line:\n\"handle user\"")