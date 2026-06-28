#!/usr/bin/env python3
"""
Daily Schedule + Weather Notifier
- Sends daily course schedule and weather via Feishu/Lark webhook
- Weather data from wttr.in (free, no API key required)
- Zero dependencies — Python 3 stdlib only

GitHub: https://github.com/Sver0411/daily-push
"""

import json
import urllib.request
import os
import re
from datetime import datetime, date

# ============ Configuration ============
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
CITY = os.environ.get("CITY", "Beijing")
SEMESTER_START = date(2026, 3, 9)  # First Monday of semester


# ============ Utility Functions ============

def get_current_week() -> int:
    """Calculate current week number based on semester start date."""
    today = date.today()
    delta = (today - SEMESTER_START).days
    return max(1, delta // 7 + 1)


def parse_week_desc(desc: str) -> list:
    """
    Parse week description string into list of week numbers.

    Supported formats:
      "1-16"      → [1, 2, ..., 16]
      "1,3-16"    → [1, 3, 4, ..., 16]
      "4-16e"     → [4, 6, 8, ..., 16]  (even weeks only, use "e" suffix)
      "3"         → [3]
      "5-9,11-16" → [5, 6, 7, 8, 9, 11, ..., 16]
    """
    desc = desc.strip()
    even_only = False
    if desc.endswith("e"):
        even_only = True
        desc = desc[:-1]

    weeks = set()
    parts = desc.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            for w in range(int(a), int(b) + 1):
                weeks.add(w)
        else:
            weeks.add(int(part))

    if even_only:
        weeks = {w for w in weeks if w % 2 == 0}

    return sorted(weeks)


def week_matches(desc: str, current_week: int) -> bool:
    """Check if current week is included in the week description."""
    return current_week in parse_week_desc(desc)


def get_period_time(period: tuple) -> str:
    """Convert period tuple to time string."""
    period_times = {
        (1, 2): "08:40-10:10",
        (3, 4): "10:30-12:00",
        (5, 6): "14:00-15:30",
        (7, 8): "15:40-17:10",
    }
    return period_times.get(period, f"Period {period[0]}-{period[1]}")


def get_weather(city: str = CITY) -> str:
    """Fetch weather from wttr.in with English→Chinese translation."""
    WEATHER_ZH = {
        "sunny": "晴", "clear": "晴",
        "partly cloudy": "多云",
        "cloudy": "阴", "overcast": "阴",
        "mist": "薄雾", "fog": "雾",
        "light rain": "小雨", "patchy rain possible": "阵雨",
        "moderate rain": "中雨", "heavy rain": "大雨",
        "light snow": "小雪", "moderate snow": "中雪",
        "thunder": "雷阵雨",
    }

    def to_zh(desc):
        desc_lower = desc.strip().lower()
        for en, zh in WEATHER_ZH.items():
            if desc_lower == en:
                return zh
        for en, zh in WEATHER_ZH.items():
            if en in desc_lower or desc_lower in en:
                return zh
        return desc.strip()

    try:
        url = f"https://wttr.in/{urllib.request.quote(city)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data["current_condition"][0]
        weather_desc = to_zh(current["weatherDesc"][0]["value"])
        temp = current["temp_C"]
        humidity = current["humidity"]

        today_weather = data["weather"][0]
        temp_low = today_weather["mintempC"]
        temp_high = today_weather["maxtempC"]

        return f"{weather_desc}  {temp_low}°C~{temp_high}°C  now {temp}°C  humidity {humidity}%"
    except Exception as e:
        return f"Weather unavailable: {e}"


def send_feishu(text: str):
    """Send message via Feishu/Lark webhook."""
    if not FEISHU_WEBHOOK:
        print("[No webhook configured — print only]")
        print(text)
        return

    payload = {
        "msg_type": "text",
        "content": {"text": text}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"Feishu response: {resp.read().decode('utf-8')}")
    except Exception as e:
        print(f"Feishu send failed: {e}")


# ============ Course Data ============
# Each course: { day, name, teacher, weeks_desc, period, classroom }
# day: 0=Monday ... 4=Friday
# period: (start, end) tuple

COURSES = [
    # ── Replace these with your own courses ──
    {"day": 0, "name": "Mobile Development", "teacher": "",
     "weeks_desc": "1-16", "period": (1, 2), "classroom": "Building B 101"},
    {"day": 2, "name": "Mobile Development", "teacher": "",
     "weeks_desc": "1-16", "period": (1, 2), "classroom": "Lab B201"},
    {"day": 2, "name": "Policy Studies", "teacher": "",
     "weeks_desc": "1-16", "period": (3, 4), "classroom": "East A312"},
    {"day": 2, "name": "Agricultural IT", "teacher": "",
     "weeks_desc": "1-16", "period": (5, 6), "classroom": "Building B 101"},
    {"day": 3, "name": "Big Data in Agriculture", "teacher": "",
     "weeks_desc": "1-16", "period": (1, 2), "classroom": "Building B 110"},
    {"day": 3, "name": "HarmonyOS Development", "teacher": "",
     "weeks_desc": "1-16", "period": (3, 4), "classroom": "East A314"},
    {"day": 3, "name": "Big Data in Agriculture", "teacher": "",
     "weeks_desc": "1-16", "period": (5, 6), "classroom": "Lab B203"},
    {"day": 4, "name": "Machine Learning", "teacher": "",
     "weeks_desc": "1-16", "period": (1, 2), "classroom": "East A312"},
    {"day": 4, "name": "Machine Learning", "teacher": "",
     "weeks_desc": "1-16", "period": (5, 6), "classroom": "East A506"},
]


# ============ Main Logic ============

def get_today_courses():
    """Get courses for today."""
    today = datetime.now()
    weekday = today.weekday()  # 0=Monday ... 6=Sunday
    current_week = get_current_week()
    date_str = today.strftime("%Y-%m-%d")

    if weekday >= 5:
        return None, current_week, date_str

    today_courses = []
    for c in COURSES:
        if c["day"] == weekday and week_matches(c["weeks_desc"], current_week):
            today_courses.append(c)

    return today_courses, current_week, date_str


def format_message(courses, current_week, date_str):
    """Format the push notification message."""
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today = datetime.now()
    day_name = day_names[today.weekday()]

    lines = [
        f"📅 {date_str} {day_name}  ·  Week {current_week}",
        "",
    ]

    weather = get_weather()
    lines.append(f"🌤 Weather: {weather}")
    lines.append("")

    if not courses:
        lines.append("📭 No classes today ✨")
    else:
        courses_sorted = sorted(courses, key=lambda c: c["period"])
        lines.append("📚 Today's Courses:")
        for c in courses_sorted:
            time_str = get_period_time(c["period"])
            lines.append(
                f"  {time_str}  {c['name']} ({c['teacher']})"
            )
            lines.append(f"            📍 {c['classroom']}")
        lines.append("")
        lines.append(f"{len(courses_sorted)} course(s) today — good luck! 💪")

    lines.append("")
    lines.append("── Daily Schedule Bot ──")

    return "\n".join(lines)


def main():
    courses, current_week, date_str = get_today_courses()
    today = datetime.now()

    if today.weekday() >= 5:
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weather = get_weather()
        msg = (
            f"📅 {date_str} {day_names[today.weekday()]}  ·  Week {current_week}\n"
            f"\n"
            f"🌤 Weather: {weather}\n"
            f"\n"
            f"🎉 Weekend! No classes today～\n"
            f"\n"
            f"── Daily Schedule Bot ──"
        )
    else:
        msg = format_message(courses, current_week, date_str)

    print("=" * 50)
    print(msg)
    print("=" * 50)

    send_feishu(msg)


# ============ Simulation & Full Schedule ============

def simulate(weekday: int = None, week: int = None):
    """
    Simulate a day's output without actually sending.

    Args:
        weekday: 0=Monday ... 4=Friday
        week: simulated week number
    """
    today = datetime.now()
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    if weekday is None:
        weekday = today.weekday()
    if week is None:
        week = get_current_week()

    if weekday >= 5:
        print(f"Sim: {day_names[weekday]} Week {week} → Weekend, no classes")
        return

    sim_courses = []
    for c in COURSES:
        if c["day"] == weekday and week_matches(c["weeks_desc"], week):
            sim_courses.append(c)

    print(f"\n📋 Sim: {day_names[weekday]} Week {week}")
    print(f"   Matched {len(sim_courses)} course(s):")
    for c in sorted(sim_courses, key=lambda c: c["period"]):
        time_str = get_period_time(c["period"])
        print(f"   {time_str}  {c['name']} ({c['teacher']}) → {c['classroom']}")

    if not sim_courses:
        print("   (No classes)")

    return sim_courses


def full_schedule():
    """Print the complete Mon–Fri schedule."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    print("\n" + "=" * 60)
    print("  📋 Full Course Schedule")
    print("=" * 60)
    for day_idx, day_name in enumerate(day_names):
        day_courses = [c for c in COURSES if c["day"] == day_idx]
        print(f"\n  【{day_name}】")
        for c in sorted(day_courses, key=lambda c: c["period"]):
            time_str = get_period_time(c["period"])
            print(f"    {time_str}  {c['name']} ({c['teacher']})")
            print(f"              Weeks: {c['weeks_desc']}  |  📍 {c['classroom']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sim":
        weekday = int(sys.argv[2]) if len(sys.argv) > 2 else None
        week = int(sys.argv[3]) if len(sys.argv) > 3 else None
        simulate(weekday, week)
    elif len(sys.argv) > 1 and sys.argv[1] == "full":
        full_schedule()
    else:
        main()
