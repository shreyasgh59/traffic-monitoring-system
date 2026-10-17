# Traffic Monitoring System

Traffic Monitoring System is an academic project for IT303. It gives traffic administrators a single place to review road-video uploads, monitor traffic conditions, prepare fine reports, and share current traffic status with registered users.

## What the system offers

- Separate administrator and registered-user accounts.
- A traffic-operations dashboard showing the latest traffic level, visible vehicles, congestion score, recent activity, and sign-in history.
- A Live Monitoring page where an administrator can upload road clips, choose a queued clip, connect an IP camera URL, or select a browser camera.
- Per-video traffic reports with vehicle categories and a clear Low, Medium, or Heavy traffic status.
- A traffic-density gauge and congestion-history chart for easy status review.
- A fine-evidence screen for creating helmet-violation fine reports with a supporting snapshot.
- A protected Pending Fines page where a registered user can view records for only their own vehicle.
- Account registration, sign-in with username or email, password reset, and Terms and Conditions pages.

## Who uses it

### Traffic administrator

Administrators can access the control-room dashboard, add and select video sources, review traffic reports, and create fine reports. Administrator password recovery requires the registered email address and administrator unique number.

### Registered user

Registered users can create an account with their vehicle number, check the latest published traffic status, and view fines issued to their own vehicle. User password recovery requires the registered email address and vehicle number.

## Getting started

1. Open PowerShell in the project folder.
2. Activate the included environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Start the application:

   ```powershell
   python manage.py runserver
   ```

4. In a browser, open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

To stop the application, return to PowerShell and press `Ctrl+C`.

## Demo administrator access

- Username: `Shreyas`
- Password: `Shashank123`
- Email for password recovery: `shreyas@test.com`
- Administrator unique number: `011`

## Typical workflow

1. Sign in as an administrator.
2. Open **Live Monitoring** and add one or more local road-video clips.
3. Select a clip to view it, then run its analysis.
4. Review the saved results on **Traffic reports** and the dashboard.
5. If required, open **Fine evidence**, attach a supporting snapshot, and create a fine report for a registered vehicle.
6. A registered user can sign in and check **Traffic status** or **Pending fines**.

## Important note

This is a coursework project. Traffic information and fine evidence should be reviewed by an administrator before any real-world action is taken.
