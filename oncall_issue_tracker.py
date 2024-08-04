#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler

import numpy as np
import sounddevice as sd
from dateutil.parser import parse
from jira import JIRA

SCRIPT_PATH = os.path.abspath(__file__)

JIRA_URL = 'https://vastdata.atlassian.net'
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_API_USER_EMAIL = os.getenv('JIRA_API_USER_EMAIL')
ONCALL_ASSIGNEE = os.getenv('ONCALL_ASSIGNEE')
QUERY = f'assignee in ({ONCALL_ASSIGNEE}) AND status in (open, Triage) AND issuetype != Duty ORDER BY priority DESC'
SLEEP_BETWEEN_CHECKS_SECONDS = 10
MAX_ISSUE_SUMMERY_CHARS = 40

LOG_PATH = f'{__file__}.log'
handler = TimedRotatingFileHandler(LOG_PATH, when='W0', interval=1, backupCount=2)
handler.setFormatter(logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s'))
logger = logging.getLogger('logger')
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def play_sound():
    fs = 44100  # Sample rate
    duration_note = 0.2  # Duration of each note in seconds

    # Define a sequence of notes (frequencies in Hz)
    notes = [523, 659, 784, 1047]  # C5, E5, G5, C6

    samples = np.array([])
    for note in notes:
        t_note = np.linspace(0, duration_note, int(fs * duration_note), endpoint=False)
        # Create a simple sine wave for each note
        samples = np.append(samples, np.sin(2 * np.pi * note * t_note))

    # Apply a fade-out effect to the whole melody
    decay = np.linspace(1, 0, samples.size)
    samples *= decay

    # Normalize the audio volume
    samples *= 0.5

    # Play the melody
    sd.play(samples, fs)
    sd.wait()


def is_script_running():
    # Command to check if this script is already running
    process_name = os.path.basename(__file__)
    try:
        output = subprocess.check_output(["pgrep", "-f", process_name])
        # If more than one line of output, another instance is running
        if len(output.splitlines()) > 1:
            return True
    except subprocess.CalledProcessError:
        # pgrep exits with non-zero status if no matching processes are found
        return False
    return False


def add_to_crontab(target_day_param):
    # The cron job to be added
    new_job = (f"*/10 * * * {target_day_param + 1} JIRA_API_TOKEN={JIRA_API_TOKEN}; JIRA_API_USER_EMAIL={JIRA_API_USER_EMAIL} "
               f"{sys.executable} {SCRIPT_PATH} --weekday {get_weekday_name(target_day_param)} >> {LOG_PATH} 2>&1")

    # Get the current crontab
    try:
        current_crontab = subprocess.check_output("crontab -l", shell=True).decode()
    except subprocess.CalledProcessError:
        # If the crontab is empty or doesn't exist, initialize it
        current_crontab = ""

    # Check if the cron job already exists
    old_job = next(iter(job for job in current_crontab.split('\n') if SCRIPT_PATH in job), None)
    if old_job and old_job == new_job:
        logger.info("Same cron job already exists. Skipping add to crontab...")
    else:
        if old_job:
            new_crontab = current_crontab.replace(old_job, '')
            logger.info("Old cron job removed...")
        else:
            new_crontab = current_crontab
            logger.info("No old cron job found...")
        new_crontab = f"{new_crontab.strip()}\n{new_job}"
        with open("temp_crontab", "w") as f:
            f.write(new_crontab)
        subprocess.run("crontab temp_crontab", shell=True)
        os.remove("temp_crontab")
        logger.info(f"Cron job added: {new_job}")


def format_issue(issue):
    summary = issue.get_field("summary")
    summary = f'{summary[:MAX_ISSUE_SUMMERY_CHARS-3]}...' if len(summary) > MAX_ISSUE_SUMMERY_CHARS else summary
    return f'{issue.get_field("priority").name} - {JIRA_URL}/browse/{issue.key} - {summary}'


def search_issues():
    if not JIRA_API_TOKEN:
        logger.error('No token found in JIRA_API_TOKEN env var. Check the README for instructions.')
        return []
    if not JIRA_API_USER_EMAIL:
        logger.error('No user found in JIRA_API_USER_EMAIL env var. Check the README for instructions.')
        return []
    jira = JIRA(JIRA_URL, basic_auth=(JIRA_API_USER_EMAIL, JIRA_API_TOKEN))
    last_known_issues = []
    while True:
        logger.info('Searching for new issues...')
        current_issues = jira.search_issues(QUERY)
        formated_current_issues = "\n\t".join(format_issue(issue) for issue in current_issues)
        logger.info(f'Current issues are:\n\t {formated_current_issues}')
        for issue in current_issues:
            if issue not in last_known_issues:
                logger.info(f'New issue found: {format_issue(issue)}')
                play_sound()
        last_known_issues = current_issues
        logger.info('Going to sleep...')
        time.sleep(SLEEP_BETWEEN_CHECKS_SECONDS)


def get_weekday_name(weekday):
    base_date = datetime(2020, 1, 6)  # January 6, 2020, is a Monday
    target_date = base_date + timedelta(days=weekday)
    return target_date.strftime('%A')  # %A returns the full weekday name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a script that checks new issues on a specified weekday.')
    parser.add_argument('--weekday', type=str,
                        help='The weekday to run the script (e.g., Monday, mon, etc.)', required=True)
    args = parser.parse_args()

    try:
        target_day = parse(args.weekday, fuzzy=True).weekday()
    except ValueError:
        logger.error('Invalid weekday provided.')
        sys.exit(1)

    add_to_crontab(target_day)

    if datetime.now().weekday() != target_day:
        logger.info(f'Today it\'s not {get_weekday_name(target_day)}. Exiting...')
        sys.exit(0)

    if is_script_running():
        logger.warning('Another instance of this script is already running. Exiting...')
        sys.exit(0)

    search_issues()
