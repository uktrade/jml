from typing import List, Optional, Tuple, TypedDict

from django.urls import reverse_lazy


class StepDict(TypedDict):
    completed: bool
    active: bool
    name: str
    number: int
    link: Optional[str]


class ProgressIndicator:

    steps: List[Tuple[str, str, str]] = []

    def __init__(self, current_step: str) -> None:
        self.current_step = current_step

    def get_current_step_label(self) -> str:
        for step in self.steps:
            if step[0] == self.current_step:
                return step[1]
        return ""

    def get_step_link(self, step) -> str:
        return reverse_lazy(step[2])

    def get_progress_steps(self) -> List[StepDict]:
        """
        Build the list of progress steps
        """

        progress_steps: List[StepDict] = []
        completed: bool = True

        for index, step in enumerate(self.steps):
            # Check if the step is the current step.
            active: bool = step[0] == self.current_step
            # If we are on the active step, all future steps are not completed yet.
            if active:
                completed = False
            # Build the step and add it to the list.
            progress_step: StepDict = {
                "completed": completed,
                "active": active,
                "name": step[1],
                "number": index + 1,
                "link": self.get_step_link(step) if completed else None,
            }
            progress_steps.append(progress_step)

        return progress_steps
