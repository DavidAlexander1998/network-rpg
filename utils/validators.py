"""
Validation utilities for Network+ RPG.

Provides input validation helpers to ensure clean, safe user input.
"""

from typing import Optional, List


def validate_non_empty_string(value: str, field_name: str = "Value") -> str:
    """
    Validate that a string is non-empty after stripping whitespace.
    
    Args:
        value: The string to validate
        field_name: Name of the field for error messages
    
    Returns:
        The stripped string
    
    Raises:
        ValueError: If the string is empty or contains only whitespace
    """
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} cannot be empty")
    return stripped


def validate_int_in_range(
    value: str,
    min_val: int,
    max_val: int,
    field_name: str = "Value"
) -> int:
    """
    Validate and convert a string to an integer within a range.
    
    Args:
        value: The string to convert
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages
    
    Returns:
        The parsed integer
    
    Raises:
        ValueError: If value is not a valid integer or out of range
    """
    try:
        num = int(value.strip())
    except ValueError:
        raise ValueError(f"{field_name} must be a valid number")
    
    if not (min_val <= num <= max_val):
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
    
    return num


def validate_menu_choice(
    value: str,
    options: List[str],
    allow_quit: bool = True
) -> Optional[str]:
    """
    Validate a menu choice against available options.
    
    Args:
        value: The user's input
        options: List of valid options
        allow_quit: Whether 'q' or 'quit' is a valid choice
    
    Returns:
        The validated choice, or None if quitting
    
    Raises:
        ValueError: If choice is invalid
    """
    choice = value.strip().lower()
    
    if allow_quit and choice in ("q", "quit", "exit"):
        return None
    
    if choice in [opt.lower() for opt in options]:
        return choice
    
    raise ValueError(f"Invalid choice. Valid options: {', '.join(options)}")


def validate_yes_no(value: str, default: Optional[bool] = None) -> bool:
    """
    Validate a yes/no response.
    
    Args:
        value: The user's input
        default: Default value if input is empty (None means no default)
    
    Returns:
        True for yes, False for no
    
    Raises:
        ValueError: If input is invalid and no default provided
    """
    choice = value.strip().lower()
    
    if not choice and default is not None:
        return default
    
    if choice in ("y", "yes", "true", "1"):
        return True
    if choice in ("n", "no", "false", "0"):
        return False
    
    raise ValueError("Please enter 'y' or 'n'")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Removes or replaces characters that are unsafe for filenames.
    
    Args:
        filename: The string to sanitize
    
    Returns:
        A sanitized filename string
    """
    # Characters not allowed in Windows/Unix filenames
    unsafe_chars = '<>:"/\\|?*'
    
    result = filename.strip()
    for char in unsafe_chars:
        result = result.replace(char, '_')
    
    # Limit length
    if len(result) > 50:
        result = result[:50]
    
    # Ensure not empty
    if not result:
        result = "unnamed"
    
    return result


def validate_slot_number(value: str) -> int:
    """
    Validate a save slot number (1-10).
    
    Args:
        value: The user's input
    
    Returns:
        The validated slot number
    
    Raises:
        ValueError: If slot is invalid
    """
    return validate_int_in_range(value, 1, 10, "Slot")


def get_valid_input(
    prompt: str,
    validator,
    error_msg: str = "Invalid input. Please try again."
) -> any:
    """
    Get validated input from the user with retry loop.
    
    Args:
        prompt: The prompt to display
        validator: Function to validate the input
        error_msg: Message to show on validation failure
    
    Returns:
        The validated value
    """
    while True:
        try:
            user_input = input(prompt)
            return validator(user_input)
        except ValueError as e:
            print(f"{error_msg} ({e})")
