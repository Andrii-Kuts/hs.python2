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