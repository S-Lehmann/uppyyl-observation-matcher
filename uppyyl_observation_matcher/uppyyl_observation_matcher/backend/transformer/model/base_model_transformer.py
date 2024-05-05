"""The abstract model transformer."""

import abc


class ModelTransformer(abc.ABC):
    """An abstract model transformer."""

    def __init__(self):
        """Initializes ModelTransformer."""
        self.output_model = None

    def transform(self, model):
        """Transforms the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        self.prepare(model=model)
        self.finalize(model=model)

    @abc.abstractmethod
    def prepare(self, model):
        """Performs preparing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """

    @abc.abstractmethod
    def finalize(self, model):
        """Performs finalizing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """