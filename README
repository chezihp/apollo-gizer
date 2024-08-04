## Requirements
- Add `JIRA_API_TOKEN` and `JIRA_API_USER_EMAIL` environment variables with the corresponding values.
- Follow [this guide](https://id.atlassian.com/manage-profile/security/api-tokens) for more information on how to get the token.
- Ensure you have Python 3 installed on your machine.

## Setup
1. Create a virtual environment:
   ```sh
   virtualenv venv -p $(which python3)
   ```
2. Activate the virtual environment:
   ```sh
   . venv/bin/activate
   ```
3. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

## Description
This script monitors JIRA for new issues assigned to a specific user and plays a sound notification for any new issues detected. It continuously checks for issues that meet certain criteria, such as being open and assigned to the specified `ONCALL_ASSIGNEE`, excluding issues of type 'Duty'.

### Usage
To automate the monitoring process, run the script with the required weekday as a parameter:
```sh
python3 oncall_issue_tracker.py --weekday Wednesday
```

### Functionality
Once initiated, the script will:
- Log into JIRA using environment-stored credentials.
- Fetch issues based on a defined query.
- Log all activities and issue details in `oncall_issue_tracker.py.log` within the same directory.

Additionally, the script can add itself to the crontab to run every specified weekday, ensuring it operates on the correct days without further manual intervention.

### Features
- **Sound Notification**: The script uses Python's `sounddevice` to play a sequence of notes whenever a new issue is found, providing an auditory alert to the user.
- **Logging**: Logs of the operations help in tracking script activities and debugging if needed. These logs are managed by a `TimedRotatingFileHandler` to ensure they do not consume too much space over time.

### Author
Hezi Halpert
