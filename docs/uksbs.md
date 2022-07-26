# UK SBS Integration

[READ ME FIRST](docs/index.md#UK-SBS-Person-ID)

The DIT Leaving Service integrates with UK SBS to inform Payroll of someone leaving the department. Below are the tasks that integrate with UK SBS...

## The Leaver selects their Line manager

During the Leaver's journey, we make a request to the UK SBS Hierarchy API, if we get a result that returns a Line manager, and the Line manager is in the Staff Index, we will prepopulate this field in the Leaver's journey.

### Scenarios:

- The Leaver is not in UK SBS
    - The leaver is asked to manually select their line manager.
- The Line manager is in UK SBS and the Staff Index
    - The line manager will be prepopulated, and the leaver asked to confirm or manually select their line manager.
- The Line manager is not in UK SBS
    - The leaver is asked to manually select their line manager.
- The Line manager in UK SBS doesn't exist in the Staff Index
    - The leaver is asked to manually select their line manager. This will intentionally cause a mismatch between the selected Line Manager and the Line Manager in UK SBS.

## The Line manager decides what to do with the Leaver's Line reports

During the Line manager's journey, we make a request to the UK SBS Hierarchy API, if we get a result that tells us the Leaver has Line reports, we will present the Line manager with a page that asks them to inform us of the new Managers for each report.

### Scenarios:

- The Leaver is not in UK SBS
    - This will result in the Line manager skipping this step.
- The leaver has no Line reports
    - This will result in the Line manager skipping this step.

## The system informs UK SBS of the Leaver

Once the Line manager has completed their journey, we make a request to the UK SBS API to inform UK SBS of the Leaver.

### Scenarios:

- The Leaver is not in UK SBS
    - **??? What should we do here ???**
- The Line manager selected matches the Line manager in UK SBS
    - The system will inform UK SBS of the Leaver.
- The Line manager selected doesn't match the Line manager in UK SBS
    - The Leaver doesn't have a manager in UK SBS
        - **??? What should we do here ???**
    - The service will ask the Line manager in UK SBS to update on UK SBS Connect so that the Leaver's Line manager is corrected to the one selected by the Leaver.
        - The Line Manager in UK SBS doesn't have an email_address
            - **??? What should we do here ???**
        - The Line Manager in UK SBS isn't in the Staff Index
            - **??? What should we do here ???**
        - Once the manager in UK SBS is updated and correct, the system will inform UK SBS of the Leaver.

## Edge cases

### The Leaver is not in UK SBS

Should we skip over the Automation and just send an email to the Line manager asking them to fill out the UK SBS form?

### The Leaver doesn't have a Line manager in UK SBS

Should we send an email to UK SBS to inform them that we know of a Leaver that their system doesn't know about?
Should we not tell UK SBS at all?

### The Line manager in UK SBS isn't contactable
They don't have an email in UK SBS OR they aren't in the Staff index.

Who should we ask to update UK SBS to correct the Leaver's Line manager?
