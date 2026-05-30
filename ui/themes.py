"""
UI Themes and color constants for Network+ RPG.

Defines color schemes and visual styles used throughout the application.
"""

from rich.style import Style
from rich.color import Color


class GameTheme:
    """
    Color theme constants for the game UI.
    
    Provides consistent color schemes for different game elements.
    """
    
    # Primary colors
    PRIMARY = "bright_cyan"
    SECONDARY = "bright_blue"
    ACCENT = "bright_magenta"
    
    # Status colors
    SUCCESS = "bright_green"
    WARNING = "yellow"
    ERROR = "bright_red"
    INFO = "bright_white"
    
    # Player stats colors
    HP = "bright_red"
    HP_LOW = "red"           # HP below 30%
    HP_MEDIUM = "yellow"       # HP below 60%
    XP = "bright_cyan"
    LEVEL = "bright_yellow"
    BITS = "bright_green"
    
    # Zone/Level colors
    ZONE_LOCKED = "dim"
    ZONE_UNLOCKED = "bright_white"
    ZONE_COMPLETED = "green"
    ZONE_CURRENT = "bright_cyan"
    
    # Node colors
    NODE_LOCKED = "dim"
    NODE_AVAILABLE = "bright_white"
    NODE_COMPLETED = "green"
    NODE_GUARDIAN = "bright_red"
    
    # Combat colors
    COMBAT_CORRECT = "green"
    COMBAT_WRONG = "red"
    QUESTION_TEXT = "bright_white"
    OPTION_LETTER = "bright_cyan"
    OPTION_TEXT = "white"
    EXPLANATION = "bright_blue"
    
    # Menu colors
    MENU_TITLE = "bright_cyan"
    MENU_OPTION = "white"
    MENU_HIGHLIGHT = "bright_cyan"
    MENU_SELECTED = "green"
    
    # Progress bars
    PROGRESS_BG = "grey37"
    PROGRESS_FILL = "bright_cyan"
    HP_BAR_FULL = "bright_green"
    HP_BAR_MEDIUM = "yellow"
    HP_BAR_LOW = "red"
    XP_BAR = "bright_cyan"
    
    # Border styles
    BORDER_NORMAL = "bright_blue"
    BORDER_HIGHLIGHT = "bright_cyan"
    BORDER_SUCCESS = "green"
    BORDER_WARNING = "yellow"
    BORDER_ERROR = "red"


class Symbols:
    """
    Text symbols and characters used in the UI.
    """
    
    # Status indicators
    CHECK = "✓"
    X = "✗"
    LOCK = "🔒"
    UNLOCK = "🔓"
    STAR = "★"
    EMPTY_STAR = "☆"
    HEART = "❤"
    DIAMOND = "◆"
    
    # Arrows
    ARROW_RIGHT = "→"
    ARROW_LEFT = "←"
    ARROW_UP = "↑"
    ARROW_DOWN = "↓"
    
    # Progress
    FILLED = "█"
    HALF = "▌"
    EMPTY = "░"
    
    # Combat
    SWORD = "⚔"
    SHIELD = "🛡"
    SKULL = "💀"
    
    # Menu
    BULLET = "•"
    POINTER = "▶"
    
    # Nodes
    NODE_START = "⚑"
    NODE_BOSS = "👹"
    NODE_NORMAL = "○"
    NODE_COMPLETE = "●"


class Styles:
    """
    Rich Style objects for common UI elements.
    """
    
    # Headers
    TITLE = Style(color="bright_cyan", bold=True)
    SUBTITLE = Style(color="bright_blue")
    HEADER = Style(color="white", bold=True)
    
    # Text
    EMPHASIS = Style(italic=True)
    STRONG = Style(bold=True)
    DIM = Style(dim=True)
    
    # Status
    SUCCESS = Style(color="bright_green", bold=True)
    ERROR = Style(color="bright_red", bold=True)
    WARNING = Style(color="yellow", bold=True)
    INFO = Style(color="bright_cyan")
    
    # Combat specific
    CORRECT_ANSWER = Style(color="green", bold=True)
    WRONG_ANSWER = Style(color="red", bold=True)
    XP_GAIN = Style(color="cyan", bold=True)
    BITS_GAIN = Style(color="green")
    DAMAGE = Style(color="red", bold=True)
    LEVEL_UP = Style(color="bright_yellow", bold=True)
    
    # Menu
    MENU_SELECTED = Style(color="bright_cyan", bold=True)
    MENU_OPTION = Style(color="white")
    MENU_DISABLED = Style(color="grey39")


def get_hp_color(hp: int, max_hp: int) -> str:
    """
    Get the appropriate color for HP based on current percentage.
    
    Args:
        hp: Current HP
        max_hp: Maximum HP
        
    Returns:
        Color name string
    """
    if max_hp <= 0:
        return GameTheme.HP_LOW
    
    percentage = hp / max_hp
    
    if percentage < 0.3:
        return GameTheme.HP_LOW
    elif percentage < 0.6:
        return GameTheme.HP_MEDIUM
    else:
        return GameTheme.HP
