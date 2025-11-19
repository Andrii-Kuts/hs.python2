class colors:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'

def __frame_text(lines: list[str], padding_x: int = 2, padding_y: int = 1, frame_char: str = "#", prefix: str = colors.RESET, suffix: str = colors.RESET) -> list[str]:
    max_len = max(map(len, lines))
    result = []
    result.append(prefix + frame_char * (max_len + padding_x*2 + 2) + suffix)
    for i in range(padding_y):
        result.append(prefix + frame_char + " " * (max_len + padding_x*2) + frame_char + suffix)
    for line in lines:
        result.append(prefix + frame_char + " " * padding_x + line + " " * (padding_x + max_len - len(line)) + frame_char + suffix)
    for i in range(padding_y):
        result.append(prefix + frame_char + " " * (max_len + padding_x*2) + frame_char + suffix)
    result.append(prefix + frame_char * (max_len + padding_x*2 + 2) + suffix)
    return result

def notify_app_started():
    lines = [
        "Pesun Analysis App is ready!",
        "",
        "Author: Andrii Kuts"
    ]
    framed_lines = __frame_text(lines, prefix=colors.GREEN)
    print("\n".join(framed_lines))

def request_archive_path():
    print(f"ℹ️  Please input the path of the archive:")
    path = input()
    return path

def archive_parsing():
    print(f"{colors.BLUE}⏱️  Parsing the archive, this might take a minute...{colors.RESET}")

def notify_unknown_users(users: set[str]):
    print(f"{colors.YELLOW}⚠️. Note! Found {len(users)} unknown users:")
    for user in users:
        print(f"- {user}")
    print(f"Make sure you've created nicknames.txt file in your archive. Write down unknown users there, " + \
        f"one for each line:\n\"handle user\"{colors.RESET}")

def archive_parsed():
    print(f"{colors.GREEN}✅  Archive has been parsed!{colors.RESET}")