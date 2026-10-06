"""Deterministic fake educational LLM adapter for tests and local development.

This is NOT N-ATLaS. It performs no inference. It exists so the application
architecture can be exercised end-to-end without loading a real LLM, without
a GPU, and without network access.

Use it only when LLM_PROVIDER=fake is set. Do not represent its output as
N-ATLaS in any user-facing context.
"""

from app.llm.base import EducationalLLM


class FakeEducationalLLM(EducationalLLM):
    """Returns a fixed answer regardless of the question.

    The default answer corresponds to the default fake ASR transcript, so
    the fake end-to-end path returns a coherent-looking result. This is a
    placeholder for the real N-ATLaS implementation, nothing more.
    """

    def __init__(
        self,
        fixed_answer: str = (
            "Photosynthesis is the process by which plants use sunlight, "
            "water, and carbon dioxide to produce glucose and release oxygen."
        ),
    ) -> None:
        self._fixed_answer = fixed_answer
        self.calls: list[str] = []

    def answer(self, question: str) -> str:
        self.calls.append(question)
        return self._fixed_answer
