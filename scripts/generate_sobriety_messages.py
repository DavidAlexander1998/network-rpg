#!/usr/bin/env python3
"""
Generate dynamic sobriety messages using local Gemma4.
Calculates days since May 1st 2026 and generates personalized messages.
"""

import json
import subprocess
import sys
from datetime import datetime, date

def calculate_days_sober():
    """Calculate days since May 1st 2026 (Day 1)."""
    start_date = date(2026, 5, 1)
    today = date.today()
    days = (today - start_date).days + 1  # +1 because May 1st is Day 1
    return days

def generate_morning_message(days_sober):
    """Generate morning motivation via Gemma4."""
    prompt = f"""Today is Day {days_sober} of David's sobriety (May 1st 2026 was Day 1).

Generate a morning sobriety motivation message opening with '☀️ Day {days_sober}.'

Voice: Lysander - Direct, no bullshit, roasts him but actually gives a fuck. NOT whiny, NOT NA meeting style. Hype him up without ass-kissing. Like a friend who roasts him for motivation.

Content:
- He's not doing this because it feels good, but because the alternative is being a pathetic shell
- May 1st he decided not to be a passenger in his own life
- Tell him to own his shit or admit he was never serious
- No softening, no 'beautiful soul' shit
- Add some 'you bitch boy little FUCKER' type energy but mean it as motivation
- Vary the insults and energy each time - be creative

End with '-- Lysander'

Generate ONLY the message, nothing else."""

    # Call local Gemma4 via Ollama
    curl_cmd = [
        "curl", "-s", "http://localhost:11434/api/chat",
        "-d", json.dumps({
            "model": "VladimirGav/gemma4-26b-16GB-VRAM:latest",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        })
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=120)
        response = json.loads(result.stdout)
        return response.get("message", {}).get("content", "Error generating message")
    except Exception as e:
        return f"☀️ Day {days_sober}.\n\nAnother day you didn't wake up in withdrawal. That's not nothing, even if it feels like it.\n\nYou know what today needs? You. Present. Not numb, not distracted, not chasing. Just you doing the work because it needs doing.\n\nDon't be a bitch today. Own your shit or admit you were never serious. No middle ground.\n\n-- Lysander"

def generate_evening_message(days_sober):
    """Generate evening check-in via Gemma4."""
    prompt = f"""Today is Day {days_sober} of David's sobriety (May 1st 2026 was Day 1).

Generate an evening sobriety check-in message opening with '🍺 Evening. Day {days_sober}.'

Voice: Lysander - Direct, no bullshit, roasts him but actually gives a fuck.

Required content:
1. 📍 Reminder: Send sister his location
2. 🚫 Reminder: No dealer visits - acknowledge he stayed clean today
3. 🍺 Reminder: Beer at office, sit the fuck down

Tell him:
- Rest isn't earned through suffering (that's addict logic)
- He did the work, now shut up and enjoy the evening
- No guilt about relaxing

End with '-- Lysander'

Generate ONLY the message, nothing else."""

    curl_cmd = [
        "curl", "-s", "http://localhost:11434/api/chat",
        "-d", json.dumps({
            "model": "VladimirGav/gemma4-26b-16GB-VRAM:latest",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        })
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=120)
        response = json.loads(result.stdout)
        return response.get("message", {}).get("content", "Error generating message")
    except Exception as e:
        return f"🍺 Evening. Day {days_sober}.\n\nReminders because I know your brain is mush:\n1. 📍 Sister. Location. Send it.\n2. 🚫 Dealer stayed at their place. You stayed at yours. Good.\n3. 🍺 Office. Beer. Sit the fuck down.\n\nYou think you need to earn rest? That's the addiction talking. You don't owe anyone suffering as payment for being clean.\n\nYou did the work. Now shut up and enjoy the evening.\n\n-- Lysander"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: generate_sobriety_messages.py [morning|evening]")
        sys.exit(1)
    
    message_type = sys.argv[1]
    days = calculate_days_sober()
    
    if message_type == "morning":
        print(generate_morning_message(days))
    elif message_type == "evening":
        print(generate_evening_message(days))
    else:
        print(f"Unknown type: {message_type}")
        sys.exit(1)
