"""The preprocessed model transformer."""

from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_model.backend.models.nta.modifiers.nta_modifier import SystemModifier
from uppyyl_observation_matcher.backend.transformer.model.base_model_transformer import ModelTransformer


class PreprocessedModelTransformer(ModelTransformer):
    """A model transformer for model preprocessing."""

    def __init__(self):
        """Initializes PreprocessedModelTransformer."""
        super().__init__()

        self.uppaal_c_parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())
        self.instance_data = None

    def prepare(self, model):
        """Performs preparing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        pass

    def finalize(self, model):
        """Performs finalizing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        SystemModifier.move_sys_vars_to_global_decl(system=model)

        SystemModifier.convert_instances_to_templates(
            system=model, instance_data=self.instance_data, keep_original_templates=False)

        for inst_name, inst_data in self.instance_data.items():
            tmpl = model.get_template_by_name(name=f'{inst_name}_Tmpl')
            SystemModifier.resolve_parameters(system=model, tmpl=tmpl)
            SystemModifier.convert_local_decl_to_global_decl(system=model, tmpl=tmpl)

    def set_instance_data(self, instance_data):
        """Sets the instance data.

        Returns:
            None
        """
        self.instance_data = instance_data
