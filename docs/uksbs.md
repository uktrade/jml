# UK SBS Integration

[READ ME FIRST](/docs/index.md#uk-sbs-person-id)

The DIT Leaving Service integrates with UK SBS to inform Payroll of someone leaving the department. Below are the tasks that integrate with UK SBS...

## The Leaver selects their Line Manager

During the Leaver's journey, we make a request to the UK SBS Hierarchy API, if we get a result that returns a Line Manager, and the Line Manager is in the Staff Index, we will prepopulate this field in the Leaver's journey.

### Scenarios:

- The Leaver is not in UK SBS
    - The leaver is asked to manually select their Line Manager.
- The Line Manager is in UK SBS and the Staff Index
    - The Line Manager will be prepopulated, and the leaver asked to confirm or manually select their Line Manager.
- The Line Manager is not in UK SBS
    - The leaver is asked to manually select their Line Manager.
- The Line Manager in UK SBS doesn't exist in the Staff Index
    - The leaver is asked to manually select their Line Manager. This will intentionally cause a mismatch between the selected Line Manager and the Line Manager in UK SBS.

## The Line Manager decides what to do with the Leaver's Line reports

During the Line Manager's journey, we make a request to the UK SBS Hierarchy API, if we get a result that tells us the Leaver has Line reports, we will present the Line Manager with a page that asks them to inform us of the new Managers for each report.

### Scenarios:

- The Leaver is not in UK SBS
    - This will result in the Line Manager skipping this step.
- The leaver has no Line reports
    - This will result in the Line Manager skipping this step.

## The system informs UK SBS of the Leaver

Once the Line Manager has completed their journey, we make a request to the UK SBS API to inform UK SBS of the Leaver.

### Scenarios:

- The Leaver is not in UK SBS
    - **??? What should we do here ???**
- The Line Manager selected matches the Line Manager in UK SBS
    - The system will inform UK SBS of the Leaver.
- The Line Manager selected doesn't match the Line Manager in UK SBS
    - The Leaver doesn't have a manager in UK SBS
        - An email is sent to HR and the Line Manager that the Leaver selected informing them that UK SBS needs to be updated.
    - The service will ask the Line Manager in UK SBS to update on UK SBS Connect so that the Leaver's Line Manager is corrected to the one selected by the Leaver.
        - The Line Manager in UK SBS doesn't have an email_address
            - **??? What should we do here ???**
        - The Line Manager in UK SBS isn't in the Staff Index
            - **??? What should we do here ???**
        - Once the manager in UK SBS is updated and correct, the system will inform UK SBS of the Leaver.

## Un-handled edge cases

### The Leaver is not in UK SBS

Should we skip over the Automation and just send an email to the Line Manager asking them to fill out the UK SBS form?

### The Line Manager in UK SBS isn't contactable

They don't have an email in UK SBS OR they aren't in the Staff index.
Who should we ask to update UK SBS to correct the Leaver's Line Manager? HR and the Line Manager that the Leaver selected?
