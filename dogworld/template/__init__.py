"""template — Isaac's template system, vendored as the FOUNDATION of dogworld.

This is the actual code dogworld exists to test:
  - `pydantic_stack.RenderablePiece` / `MetaStack`  — stackable, renderable pydantic models
  - `template_mixins.TemplateAttributeMixin` / `TemplateMethodMixin` — dynamic `add_attribute` /
    `add_method` / `execute_template_sequence` (class-level templating from data)
  - `templated_class.TemplatedClass` — a BaseModel+mixins class configurable from a dict
  - `owl22python.owl22python` — OWL2/XML -> a generated `RenderablePiece` class (one field per
    DataProperty), instantiate, render back to an ontology-typed result

Vendored verbatim (imports re-pathed to this package) from the heaven progenitor template_mixins +
pydantic_stack_core. Requires `pydantic` + `jinja2`.
"""
from .pydantic_stack import RenderablePiece, MetaStack, generate_output_from_metastack
from .template_mixins import TemplateAttributeMixin, TemplateMethodMixin
from .templated_class import TemplatedClass
from .owl22python import owl22python, EXAMPLE_OWL2_XML

__all__ = [
    "RenderablePiece", "MetaStack", "generate_output_from_metastack",
    "TemplateAttributeMixin", "TemplateMethodMixin", "TemplatedClass",
    "owl22python", "EXAMPLE_OWL2_XML",
]
