import sys
import time
import random
import os
import requests
import json
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone

# CLI things
CYAN    = '\033[36m'
BLACK   = '\033[30m'
RED     = '\033[31m'
GREEN   = '\033[32m'
YELLOW  = '\033[33m'
BLUE    = '\033[34m'
MAGENTA = '\033[35m'
WHITE   = '\033[37m'
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"
DIGITS = "0123456789"
SPECIALS = "_-."

load_dotenv(find_dotenv())

class Webhook:
    @staticmethod
    def _composition(username: str) -> str:
        has_digit = any(c in DIGITS for c in username)
        has_special = any(c in SPECIALS for c in username)
        if has_digit and has_special:
            return "Letters + numbers + specials"
        if has_digit:
            return "Letters + numbers"
        if has_special:
            return "Letters + specials"
        return "Letters only"

    @staticmethod
    def send_message(webhook_url: str, username: str, platform: str) -> None:
        if not webhook_url:
            return

        content = f"`{username}` is available on **{platform}**"

        payload = {
            "content": content,
            "embeds": [{
                "title": "New Available Handle Found",
                "color": 3066993,
                "fields": [
                    {"name": "Length", "value": f"{len(username)} chars", "inline": True},
                    {"name": "Composition", "value": Webhook._composition(username), "inline": True},
                ],
                "footer": {"text": "@hunter"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        }

        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except requests.exceptions.RequestException:
            pass

class PlatformChecker:
    def __init__(self):
        self.discord_token = os.getenv("DISCORD_TOKEN")
    
    def github(self, username: str) -> str:
        url = f"https://api.github.com/users/{username}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        try:
            res = requests.get(url, headers=headers, timeout=0.5)
            if res.status_code == 404:
                return "Available"
            elif res.status_code == 200:
                return "Taken"
            elif res.status_code == 403:
                return "Rate Limited"
            return f"Error {res.status_code}"
        except requests.exceptions.RequestException:
            return "Failed Connection"

    def roblox(self, username: str) -> str:
        url = "https://auth.roblox.com/v1/usernames/validate"
        payload = {
            "birthday": "2000-01-01",
            "context": "Signup",
            "username": username
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        
        try:
            # First request will fail with 403 and return the required CSRF token
            res = requests.post(url, json=payload, headers=headers, timeout=0.5)
            
            if res.status_code == 403 and "x-csrf-token" in res.headers:
                # Extract the token, update headers, and execute the actual check
                headers["x-csrf-token"] = res.headers["x-csrf-token"]
                res = requests.post(url, json=payload, headers=headers, timeout=0.5)

            if res.status_code == 200:
                data = res.json()
                if data.get("code") == 0:
                    return "Available"
                return f"Unavailable: {data.get('message', 'Unknown reason')}"
                
            elif res.status_code == 429:
                return "Rate Limited"
                
            return f"Error {res.status_code}"
            
        except requests.exceptions.RequestException:
            return "Failed Connection"

    def discord(self, username: str) -> str:
        url = "https://discord.com/api/v9/users/@me/pomelo-attempt"
        headers = {
            "Authorization": self.discord_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            res = requests.post(url, json={"username": username.lower().strip()}, headers=headers, timeout=5)
            if res.status_code == 200:
                return "Taken" if res.json().get("taken") else "Available"
            elif res.status_code == 429:
                return "Rate Limited"
            return f"Error {res.status_code}"
        except requests.exceptions.RequestException:
            return "Failed Connection"
    
    def youtube(self, username: str, max_retries: int = 3) -> str:
        username = username.lower().replace("@", "").strip()

        if not (3 <= len(username) <= 30):
            return "Invalid"
        if not all(c.isalnum() or c in "._-" for c in username):
            return "Invalid"
        if username.replace(".", "").replace("_", "").replace("-", "").isdigit():
            return "Invalid"

        url = "https://www.youtube.com/youtubei/v1/navigation/resolve_url"
        params = {"key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"}  # public web client key
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json",
        }
        payload = {
            "context": {"client": {"clientName": "WEB", "clientVersion": "2.20240101.00.00"}},
            "url": f"https://www.youtube.com/@{username}",
        }

        backoff = 2.0
        for attempt in range(max_retries):
            try:
                res = requests.post(url, params=params, headers=headers, json=payload, timeout=5)
            except requests.exceptions.RequestException:
                return "Failed Connection"

            if res.status_code == 429:
                if attempt == max_retries - 1:
                    return "Rate Limited"
                time.sleep(backoff + random.uniform(0, 1))
                backoff = min(backoff * 2, 60)
                continue

            if res.status_code != 200:
                return f"Error {res.status_code}"

            try:
                data = res.json()
            except ValueError:
                return "Unknown"

            browse_id = data.get("endpoint", {}).get("browseEndpoint", {}).get("browseId", "")
            if browse_id.startswith("UC"):
                return "Taken"

            if "error" in data:
                return "Available"

            return "Unknown"

        return "Rate Limited"
    
    def steam(self, username: str) -> str:
        url = f"https://steamcommunity.com/id/{username}/?xml=1"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json",
        }

        try:
            res = requests.get(url, headers=headers, timeout=5)
            
            if "The specified profile could not be found." in res.text:
                return "Available"
            return "Taken"
        except requests.exceptions.RequestException:
            return "Failed Connection"

    def minecraft(self, username: str) -> str:
        url = f"https://api.minecraftservices.com/minecraft/profile/lookup/name/{username}"

        try:
            res = requests.get(url, timeout=5)

            if res.status_code == 200:
                return "Taken"

            if res.status_code == 404:
                return "Available"

            return f"Error ({res.status_code})"

        except requests.exceptions.RequestException:
            return "Failed Connection"

class UsernameHunter:
    platforms = {
        "1": "Discord",
        "2": "WhatsApp",
        "3": "Telegram",
        "4": "GitHub",
        "5": "Instagram",
        "6": "Twitter",
        "7": "TikTok",
        "8": "Steam",
        "9": "Roblox",
        "10": "Spotify",
        "11": "YouTube",
        "12": "Minecraft",
    }

    @staticmethod
    def search_username(username: str, platform: str) -> None:
        c = PlatformChecker()
        webhook_url = os.getenv("WEBHOOK_URL")

        if platform == "Discord":
            status = c.discord(username)
            
            if status == "Available":
                print(f"{BOLD}{GREEN}[+]{RESET} {platform} - {BOLD}{GREEN}{username}{RESET}")
                Webhook.send_message(webhook_url, username, platform)
                
            elif status == "Taken":
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET}")
            else:
                print(f"{BOLD}{YELLOW}[!]{RESET} {platform} - {username} ({status})")
        elif platform == "YouTube":
            status = c.youtube(username)
            
            if status == "Available":
                print(f"{BOLD}{GREEN}[+]{RESET} {platform} - {BOLD}{GREEN}{username}{RESET}")
                Webhook.send_message(webhook_url, username, platform)
                
            elif status == "Taken":
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET}")
            else:
                print(f"{BOLD}{YELLOW}[!]{RESET} {platform} - {username} ({status})")
        elif platform == "Roblox":
            status = c.roblox(username)

            if status == "Available":
                print(f"{BOLD}{GREEN}[+]{RESET} {platform} - {BOLD}{GREEN}{username}{RESET}")
                Webhook.send_message(webhook_url, username, platform)
            elif status == "Unavailable":
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET}")
            else:
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET} ({status})")
        elif platform == "GitHub":
            status = c.github(username)

            if status == "Available":
                print(f"{BOLD}{GREEN}[+]{RESET} {platform} - {BOLD}{GREEN}{username}{RESET}")
                Webhook.send_message(webhook_url, username, platform)
            elif status == "Taken":
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET}")
            else:
                print(f"{BOLD}{YELLOW}[!]{RESET} {platform} - {username} ({status})")
        elif platform == "Steam":
            status = c.steam(username)

            if status == "Available":
                print(f"{BOLD}{GREEN}[+]{RESET} {platform} - {BOLD}{GREEN}{username}{RESET}")
                Webhook.send_message(webhook_url, username, platform)
            elif status == "Taken":
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET}")
            else:
                print(f"{BOLD}{YELLOW}[!]{RESET} {platform} - {username} ({status})")
        elif platform == "Minecraft":
            status = c.minecraft(username)

            if status == "Available":
                print(f"{BOLD}{GREEN}[+]{RESET} {platform} - {BOLD}{GREEN}{username}{RESET}")
                Webhook.send_message(webhook_url, username, platform)
            elif status == "Taken":
                print(f"{BOLD}{RED}[-]{RESET} {platform} - {BOLD}{WHITE}{username}{RESET}")
            else:
                print(f"{BOLD}{YELLOW}[!]{RESET} {platform} - {username} ({status})")
        else:
            print(f"{BOLD}{CYAN}?{RESET} {platform} - {BOLD}{WHITE}{username}{RESET} (No checker implemented)")

    @staticmethod
    def search_rare_usernames(platform: str, timeout: float) -> None:
        if not os.path.exists("./includes/rare.txt"):
            print(f"{BOLD}{RED}!{RESET} Error: ./includes/rare.txt not found.")
            return

        with open("./includes/rare.txt", "r") as file:
            name_list = list(file)
        
        random.shuffle(name_list)

        for i in name_list:
            username = i.strip()
            if username:
                UsernameHunter.search_username(username, platform)
                time.sleep(timeout)

    @staticmethod
    def _build_charsets(length: int, use_numbers: bool, use_specials: bool) -> list:
        charsets = [CONSONANTS if i % 2 == 0 else VOWELS for i in range(length)]
        if use_numbers:
            charsets.append(DIGITS)
        if use_specials:
            charsets.append(SPECIALS)
        return charsets

    @staticmethod
    def _increment(indices: list, charsets: list) -> bool:
        for pos in range(len(indices) - 1, -1, -1):
            indices[pos] += 1
            if indices[pos] < len(charsets[pos]):
                return True
            indices[pos] = 0
        return False

    @staticmethod
    def search_rare_string_usernames(platform: str, length: int, use_numbers: bool, use_specials: bool, timeout: float, count: int) -> None:
        charsets = UsernameHunter._build_charsets(length, use_numbers, use_specials)
        indices = [random.randrange(len(cs)) for cs in charsets]

        checked = 0
        while checked < count:
            username = "".join(cs[i] for cs, i in zip(charsets, indices))
            UsernameHunter.search_username(username, platform)
            checked += 1
            if not UsernameHunter._increment(indices, charsets):
                break 

            time.sleep(timeout)
        
    @staticmethod
    def search_random_string_usernames(platform: str, length: int, use_numbers: bool, use_specials: bool, timeout: float, count: int) -> None:
        charsets = CONSONANTS + VOWELS
        if use_numbers:
            charsets += DIGITS
        if use_specials:
            charsets += SPECIALS

        for _ in range(count):
            username = "".join(random.choice(charsets) for _ in range(length))
            UsernameHunter.search_username(username, platform)
            time.sleep(timeout)
    
    @staticmethod
    def search_short_dictionary_usernames(platform: str, length: int, timeout: float) -> None:
        json_path = "./includes/short_words.json"

        if not os.path.exists(json_path):
            print(f"{BOLD}{RED}!{RESET} Error: {json_path} not found.")
            return

        with open(json_path, "r", encoding="utf-8") as file:
            name_list = json.load(file)

        length_key = str(length)

        # Check if the requested length group exists in the JSON dictionary
        if length_key not in name_list:
            print(f"{BOLD}{RED}!{RESET} Error: Length group '{length_key}' does not exist in dictionary database.")
            print(f"Available length groups: {list(name_list.keys())}")
            return

        # Extract the specific word list for that length
        words = name_list[length_key]

        # Shuffle the target word list (not the dict itself)
        random.shuffle(words)

        # Iterate and check
        for username in words:
            username = username.strip()
            if username:
                UsernameHunter.search_username(username, platform)
                time.sleep(timeout)

class gui:
    @staticmethod
    def display_start() -> None:
        print(f"\n{BOLD}{RED}?{RESET} Select your operational mode:\n")
        print(f"  {BOLD}{RED}1{RESET} - Search for a specific username")
        print(f"  {BOLD}{RED}2{RESET} - Search for over 600+ rare usernames from (./includes/rare.txt)")
        print(f"  {BOLD}{RED}3{RESET} - Search for rare string usernames")
        print(f"  {BOLD}{RED}4{RESET} - Search for random string usernames")
        print(f"  {BOLD}{RED}5{RESET} - Search for short dictionary usernames")
        print(f"  {BOLD}{RED}q{RESET} - Quit app")
        print(" ")

    @staticmethod
    def display_menu() -> None:
        print(f"\n{BOLD}{RED}?{RESET} Select your platform of choice:\n")
        for i in UsernameHunter.platforms:
            print(f"  {BOLD}{RED}{i}{RESET} - {UsernameHunter.platforms[i]}")
        print(f"  {BOLD}{RED}q{RESET} - Quit app")
        print(" ")

    @staticmethod
    def display_string_options() -> tuple:
        print(f"\n{BOLD}{RED}?{RESET} Configure rare string search:\n")

        length = input(f"{BOLD}{RED}>{RESET} String length (e.g. 3): ").strip()
        length = int(length) if length.isdigit() and int(length) > 0 else 3

        numbers = input(f"{BOLD}{RED}>{RESET} Include numbers? (y/n): ").strip().lower()
        use_numbers = numbers == "y"

        specials = input(f"{BOLD}{RED}>{RESET} Include special characters? (y/n): ").strip().lower()
        use_specials = specials == "y"

        timeout = input(f"{BOLD}{RED}>{RESET} Timeout between checks in seconds (e.g. 0.5): ").strip()
        timeout = float(timeout) if timeout.replace(".", "", 1).isdigit() and float(timeout) >= 0 else 0.5

        count = input(f"{BOLD}{RED}>{RESET} How many to check (e.g. 50): ").strip()
        count = int(count) if count.isdigit() and int(count) > 0 else 50

        return length, use_numbers, use_specials, timeout, count

    @staticmethod
    def pause() -> None:
        input(f"{BOLD}{RED}?{RESET} Press {BOLD}{RED}ENTER{RESET} to continue")

if __name__ == "__main__":
    while True:
        gui.display_start()
        mode = input(f"{BOLD}{RED}>{RESET} ").strip()
        if mode == "q":
            break
        if mode not in ("1", "2", "3", "4", "5"):
            print(f"{BOLD}{RED}!{RESET} Not a right command. Please choose 1, 2, 3, 4, 5, or q.")
            print("")
            gui.pause()
            continue

        gui.display_menu()
        platform = input(f"{BOLD}{RED}>{RESET} ").strip()
        if platform == "q":
            break

        if platform not in UsernameHunter.platforms:
            print(f"{BOLD}{RED}!{RESET} Not a right command. Please choose a valid platform.")
            gui.pause()
            continue

        selected_platform = UsernameHunter.platforms[platform]

        if mode == "1":
            username = input(f"{BOLD}{RED}>{RESET} Enter username: ").strip()
            UsernameHunter.search_username(username, selected_platform)
        elif mode == "2":
            timeout = input(f"{BOLD}{RED}>{RESET} Timeout between checks in seconds (e.g. 0.5): ").strip()
            timeout = float(timeout) if timeout.replace(".", "", 1).isdigit() and float(timeout) >= 0 else 0.5
            UsernameHunter.search_rare_usernames(selected_platform, timeout)
        elif mode == "3":
            length, use_numbers, use_specials, timeout, count = gui.display_string_options()
            UsernameHunter.search_rare_string_usernames(
                selected_platform, length, use_numbers, use_specials, timeout, count
            )
        elif mode == "4":
            length, use_numbers, use_specials, timeout, count = gui.display_string_options()
            UsernameHunter.search_random_string_usernames(
                selected_platform, length, use_numbers, use_specials, timeout, count
            )
        elif mode == "5":
            timeout = input(f"{BOLD}{RED}>{RESET} Timeout between checks in seconds (e.g. 0.5): ").strip()
            timeout = float(timeout) if timeout.replace(".", "", 1).isdigit() and float(timeout) >= 0 else 0.5

            lenght = input(f"{BOLD}{RED}>{RESET} Enter the length of usernames to search (e.g. 3): ").strip()
            length = int(lenght) if lenght.isdigit() and int(lenght) > 0 else 3

            UsernameHunter.search_short_dictionary_usernames(selected_platform, length, timeout)

        print("")
        gui.pause()

    print(f"\n{BOLD}{RED}!{RESET} Exiting...")
    sys.exit(0)