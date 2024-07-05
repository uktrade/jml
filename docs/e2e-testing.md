---
hide:
  - navigation
---

# End-to-end tests

These E2E tests are intended to cover the most important parts of the application.
The scenarios are written with the assumption that you are testing locally or on dev/staging.

**Setup some test data:**

- Create a new user to be a leaver
    - Go to "Dev tools" and fill out the "Create user" form
- Create a new user to be the leaver's manager
    - Go to "Dev tools" and fill out the "Create user" form
- Create a new user to be a HR admin
    - Go to "Dev tools" and fill out the "Create user" form
    - Make sure to set the "Group" to "HR"
- Create a new user to be an SRE admin
    - Go to "Dev tools" and fill out the "Create user" form
    - Make sure to set the "Group" to "SRE"
- Create a new user to be an Security admin
    - Go to "Dev tools" and fill out the "Create user" form
    - Make sure to set the "Group" to "Security Team"

## Leaver Journey

Using dev tools, in the "Change user" form, select the leaver user you created and click "Select user".

- Navigate to `/leavers/start/`
- Press "Start"
- Select "I am leaving the department"
- Fill out the forms using realistic data (don't use real names, emails, etc)
- **Who is your line manager?**
    - Select the manager user you created
- At the end, you should see a confirmation page, submit this request and the leaver's part of the process is complete

## Manager Journey

Using dev tools, in the "Change user" form, select the manager user you created and click "Select user".

- In the navigation menu, a new item should be visible: "Start Line Manager process"
    - Clicking this should take you to the manager section of the offboarding process for the leaver you just created
- Press "Start"
- Confirm all of the details are correct and fill out the new fields as required
- At the end, you should see a confirmation page, submit this request and the manager's part of the process is complete

## HR Admin Journey (Viewing Submitted Requests)

Using dev tools, in the "Change user" form, select the HR admin user you created and click "Select user".

- You should now see a new item in the navigation menu: "Leaving Requests" `/leavers/leaving-requests/`
    - Clicking this should take you to a list of all leaving requests
- In the list of "Incomplete" requests, click on the leaver you created
- You should now see a summary of the leaver's request and it's actions

## HR Admin Journey (Create a new leaver)

Using dev tools, in the "Change user" form, select the HR admin user you created and click "Select user".

- You should now see a new item in the navigation menu: "Leaving Requests" `/leavers/leaving-requests/`
    - Clicking this should take you to the page where you can "Create a new leaver".
- Click on the "Start" button to manually off-board someone.
    - Select the person you want to off-board by typing their name in the search bar.
        - Click on the "Select" button displayed next to the leaver's name.
    - Click on the "Continue" button to fill in the forms on behalf of the leaver.
    - At the end, you should see a confirmation page, submit this request and the leaver's details part of the process is complete.
- To complete the offboarding click on "Start" button to confirm all the details and to add further information as needed.
- After confirming all the information you can complete the process via "Accept and send" button.

## SRE Journey

Using dev tools, in the "Change user" form, select the SRE admin user you created and click "Select user".
 team

- You should now see a new item in the navigation menu: "Leaving Requests" `/leavers/leaving-requests/sre/incomplete-leaving-request/`
    - Clicking this should take you to a list of submitted leaving requests that are ready for the SRE team to action
- Select the request for the leaver you created
    - You should see the information from the request that is helpful to the SRE team
    - You should be able to do the following tasks:
        - For each tool listed:
            - Mark it as:
                - Not started
                - Not applicable
                - Removed
            - Add notes to the tool
        - Mark the record as complete
            - This is only possible if all of the tools have been marked as "Removed" or "Not applicable"

## Security Journey

Using dev tools, in the "Change user" form, select the Security admin user you created and click "Select user".

- You should now see a new item in the navigation menu: "Leaving Requests" `/leavers/leaving-requests/security-team/incomplete-leaving-request/`
    - Clicking this should take you to a list of submitted leaving requests that are ready for the Security team to action
- There are 2 tabs on this page "Security requests" and "ROSA Kit requests"
    - On the "Security requests" tab, click on the leaver you created
        - You should see the information from the request that is helpful to the security team
        - You should be able to do the following tasks:
            - Mark the building pass as:
                - Deactivated
                - Returned
                - Destroyed
            - Mark the security clearance as:
                - Active
                - Lapsed
                - Paused
                - Other (with a text field to explain)
            - Add comments to the request
            - Mark the record as complete
                - This is only possible if all of the above fields are filled out
    - On the "ROSA Kit requests" tab, click on the leaver you created (the leaver will only show here if in the request it was flagged that they have ROSA equipment)
        - You should see the information from the request that is helpful to the Security team
        - You should be able to do the following tasks:
            - Set each equipment as:
                - Not started
                - Not applicable
                - Returned
            - Add notes to each piece of equipment
            - Mark the record as complete
                - This is only possible if all of the equipment has been marked as "Returned" or "Not applicable"
