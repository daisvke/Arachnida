# ANSI escape codes for text formatting

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# Logs levels
INFO = f"{YELLOW}[INFO]{RESET}"
WARNING = f"{MAGENTA}[WARNING]{RESET}"
ERROR = f"{RED}[ERROR]{RESET}"
DONE = f"{GREEN}[DONE]{RESET}"
FOUND = f"{GREEN}[FOUND]{RESET}"

def color_search_string_in_context(
        search_string: str,
        context: str,
        case_insensitive: bool,
        color: str = RED
        ) -> str:
    """"
    Color the search string contained in the context and return it.
    """
    colored_text = ""

    # Replace newlines from within the text by spaces
    stripped_text = context.replace('\n', ' ')

    # Color the search string in the given color
    colored_search_string = color + search_string + RESET

    # Handle case-insensitive mode
    if case_insensitive:
        stripped_text = stripped_text.lower()
        search_string = search_string.lower()
        colored_search_string = colored_search_string.lower()

    # Replace the uncolored string occurences by the colored one
    colored_text = stripped_text.replace(
        search_string,
        colored_search_string
        )

    return colored_text