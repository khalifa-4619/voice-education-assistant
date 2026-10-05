"""Abstract interface for the N-ATLaS educational LLM.

The rest of the application depends only on this interface, never on a
concrete implementation. This lets us swap the eventual hosted N-ATLaS API
for a local N-ATLaS inference path (or vice versa) without touching callers.

Educational scope note: this interface is deliberately general. The specific
subjects, difficulty levels, and refusal behavior for the assistant are
defined in Milestone 8, not here. Adding those now would be premature.
"""

from abc import ABC, abstractmethod


class EducationalLLM(ABC):
    """N-ATLaS educational question-answering interface.

    Implementations accept an educational question (in a supported language)
    and return an answer in the same language where N-ATLaS supports it.

    The interface is intentionally minimal: one method, one string in, one
    string out. No streaming, no conversation history, no tool calls yet.
    We add those only when a real requirement demands them.
    """

    @abstractmethod
    def answer(self, question: str) -> str:
        """Answer an educational question.

        Args:
            question: The student's question, in Hausa, Nigerian-accented
                English, or another N-ATLaS-supported language.

        Returns:
            The educational answer as a single string.

        Raises:
            ValueError: If the question is empty or otherwise invalid.
            RuntimeError: If the underlying LLM backend fails.
            NotImplementedError: If this implementation is a documented
                stub awaiting credentials or compute.
        """
        raise NotImplementedError
