from typing import Dict, List, Any, Optional, Union, Callable, Type, get_type_hints
from pydantic import BaseModel, Field
import inspect
import json
import os
import jinja2

# Import the mixins from your existing code
from .template_mixins import TemplateAttributeMixin, TemplateMethodMixin

class TemplatedClass(BaseModel, TemplateAttributeMixin, TemplateMethodMixin):
    """
    A general-purpose class that uses template mixins and can be 
    dynamically reconfigured via dict. It can generate a Jinja template
    of itself and a Maker class that creates more instances.
    """
    class_name: str
    class_description: Optional[str] = "A dynamically templated class"
    base_classes: List[str] = ["BaseModel", "TemplateAttributeMixin", "TemplateMethodMixin"]

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize the mixin state if not already present
        if not hasattr(self, '_attributes'):
            self._attributes = {}
        if not hasattr(self, '_attribute_dependencies'):
            self._attribute_dependencies = {}
        if not hasattr(self, '_methods'):
            self._methods = {}
        if not hasattr(self, '_template_sequence'):
            self._template_sequence = []
        if not hasattr(self, '_format_logic'):
            self._format_logic = {}

        # Initialize from constructor data if provided
        if 'attributes' in data:
            for attr_name, attr_spec in data['attributes'].items():
                if isinstance(attr_spec, dict) and 'value' in attr_spec:
                    self.add_attribute_from_dict({
                        'name': attr_name,
                        **attr_spec
                    })
                else:
                    self.add_attribute(attr_name, attr_spec)

        if 'methods' in data:
            for method_spec in data['methods']:
                self.add_method_from_dict(method_spec)

        if 'template_sequence' in data:
            self.set_template_sequence(data['template_sequence'])

    def configure_from_dict(self, config: Dict[str, Any]):
        """
        Configure this class from a dictionary specification.

        Args:
            config: Configuration dict with attributes, methods, and sequence
        """
        # Update class info
        if 'class_name' in config:
            self.class_name = config['class_name']
        if 'class_description' in config:
            self.class_description = config['class_description']
        if 'base_classes' in config:
            self.base_classes = config['base_classes']

        # Add attributes
        if 'attributes' in config:
            for attr_name, attr_spec in config['attributes'].items():
                if isinstance(attr_spec, dict) and 'value' in attr_spec:
                    self.add_attribute_from_dict({
                        'name': attr_name,
                        **attr_spec
                    })
                else:
                    self.add_attribute(attr_name, attr_spec)

        # Add methods
        if 'methods' in config:
            for method_spec in config['methods']:
                self.add_method_from_dict(method_spec)

        # Set template sequence
        if 'template_sequence' in config:
            self.set_template_sequence(config['template_sequence'])

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the class configuration to a dictionary.

        Returns:
            Dictionary with complete class specification
        """
        # Start with basic class info
        result = {
            'class_name': self.class_name,
            'class_description': self.class_description,
            'base_classes': self.base_classes,
            'attributes': {},
            'methods': [],
            'template_sequence': self.get_template_sequence()
        }

        # Add all attributes
        for attr_name, attr_info in self._attributes.items():
            result['attributes'][attr_name] = {
                'value': self._serialize_attribute_value(attr_info['value']),
                'type': self._type_to_string(attr_info['type']),
                'description': attr_info['description'],
                'computed': attr_info['computed']
            }

            # Add dependencies if present
            if attr_info['computed'] and attr_name in self._attribute_dependencies:
                result['attributes'][attr_name]['dependencies'] = self._attribute_dependencies[attr_name]

        # Add all methods
        for method_name, method_info in self._methods.items():
            method_dict = {
                'name': method_name,
                'description': method_info['description'],
                'parameters': method_info['parameters'],
                'return_type': self._type_to_string(method_info['return_type']),
                'func': self._method_to_string(method_info['func'])
            }
            result['methods'].append(method_dict)

        return result

    def _serialize_attribute_value(self, value):
        """Convert attribute value to a serializable form."""
        if callable(value) and not isinstance(value, type):
            # For callables, convert to string representation
            return inspect.getsource(value)
        return value

    def _type_to_string(self, type_annotation):
        """Convert a type annotation to a string representation."""
        if type_annotation is None:
            return 'None'
        if isinstance(type_annotation, type):
            return type_annotation.__name__
        # Handle typing annotations
        return str(type_annotation).replace('typing.', '')

    def _method_to_string(self, func):
        """Convert a method function to a string representation."""
        if not callable(func):
            return str(func)

        # For bound methods, get the underlying function
        if hasattr(func, '__self__'):
            func = func.__func__

        # Get the source code
        try:
            source = inspect.getsource(func)
            # Extract just the function body
            lines = source.split('\n')
            # Find the first line with a colon (function definition)
            for i, line in enumerate(lines):
                if ':' in line:
                    # Get the body, properly indented
                    body_lines = lines[i+1:]
                    # Remove common indentation
                    if body_lines:
                        indent = len(body_lines[0]) - len(body_lines[0].lstrip())
                        body = '\n'.join(line[indent:] for line in body_lines)
                        return body
            return source
        except Exception:
            return "# Source code not available"

    def generate_class_template(self) -> str:
        """
        Generate a Jinja template for this class.

        Returns:
            Jinja template string that can recreate this class
        """
        template = '''# {{ class_name }}.py
# Generated class
from typing import Dict, List, Any, Optional, Union, Callable, Type
from pydantic import BaseModel, Field
from .template_mixins import TemplateAttributeMixin, TemplateMethodMixin

class {{ class_name }}({{ base_classes|join(', ') }}):
    """{{ class_description }}"""

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize mixin state
        if not hasattr(self, '_attributes'):
            self._attributes = {}
        if not hasattr(self, '_attribute_dependencies'):
            self._attribute_dependencies = {}
        if not hasattr(self, '_methods'):
            self._methods = {}
        if not hasattr(self, '_template_sequence'):
            self._template_sequence = []
        if not hasattr(self, '_format_logic'):
            self._format_logic = {}

        # Add standard attributes
        {% for attr_name, attr in attributes.items() %}
        self.add_attribute(
            "{{ attr_name }}", 
            {{ attr.value }}, 
            type_annotation={{ attr.type }}, 
            description="{{ attr.description }}", 
            computed={{ attr.computed }}
            {% if attr.dependencies %}
            , dependencies={{ attr.dependencies }}
            {% endif %}
        )
        {% endfor %}

        # Add standard methods
        {% for method in methods %}
        self.add_method(
            "{{ method.name }}",
            lambda self: {{ method.func }},
            description="{{ method.description }}",
            parameters={{ method.parameters }},
            return_type={{ method.return_type }}
        )
        {% endfor %}

        # Set template sequence
        self.set_template_sequence([
            {% for method_name in template_sequence %}
            "{{ method_name }}",
            {% endfor %}
        ])
'''
        # Create Jinja environment and compile template
        env = jinja2.Environment()
        template = env.from_string(template)

        # Render template with class specification
        class_spec = self.to_dict()
        return template.render(**class_spec)

    def generate_maker_template(self) -> str:
        """
        Generate a Jinja template for a Maker class that can create 
        instances of this class.

        Returns:
            Jinja template string for the Maker class
        """
        template = '''# {{ class_name }}Maker.py
# Generated Maker class for {{ class_name }}
from typing import Dict, List, Any, Optional, Union, Callable, Type
import jinja2
import os

class {{ class_name }}Maker:
    """
    Maker class for {{ class_name }}.
    Creates and configures instances of {{ class_name }}.
    """

    def __init__(self, template_dir: str = "./templates"):
        """
        Initialize the maker with a template directory.

        Args:
            template_dir: Directory to store templates
        """
        self.template_dir = template_dir
        os.makedirs(template_dir, exist_ok=True)

        # Create Jinja environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def create_instance(self, config: Dict[str, Any]) -> "{{ class_name }}":
        """
        Create an instance of {{ class_name }} with the given configuration.

        Args:
            config: Dictionary with class configuration

        Returns:
            Configured instance of {{ class_name }}
        """
        # Import the class
        from {{ class_name.lower() }} import {{ class_name }}

        # Create and configure instance
        instance = {{ class_name }}()
        instance.configure_from_dict(config)

        return instance

    def generate_class_file(self, output_dir: str = "./generated") -> str:
        """
        Generate a Python file for the class.

        Args:
            output_dir: Directory to write the generated file

        Returns:
            Path to the generated file
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Load class template
        template = self.env.get_template("{{ class_name.lower() }}.j2")

        # Get default configuration
        config = {
            'class_name': "{{ class_name }}",
            'class_description': "{{ class_description }}",
            'base_classes': {{ base_classes }},
            'attributes': {{ attributes }},
            'methods': {{ methods }},
            'template_sequence': {{ template_sequence }}
        }

        # Render template
        output = template.render(**config)

        # Write to file
        output_path = os.path.join(output_dir, "{{ class_name.lower() }}.py")
        with open(output_path, 'w') as f:
            f.write(output)

        return output_path

    def save_templates(self) -> Dict[str, str]:
        """
        Save the Jinja templates for this class.

        Returns:
            Dictionary mapping template names to file paths
        """
        # Create default instance for template generation
        from {{ class_name.lower() }} import {{ class_name }}
        instance = {{ class_name }}()

        # Generate class template
        class_template = instance.generate_class_template()
        class_template_path = os.path.join(self.template_dir, "{{ class_name.lower() }}.j2")
        with open(class_template_path, 'w') as f:
            f.write(class_template)

        # Also save the maker template (self template)
        maker_template_path = os.path.join(self.template_dir, "{{ class_name.lower() }}maker.j2")
        with open(maker_template_path, 'w') as f:
            f.write(open(__file__).read())

        return {
            'class_template': class_template_path,
            'maker_template': maker_template_path
        }
'''
        # Create Jinja environment and compile template
        env = jinja2.Environment()
        template = env.from_string(template)

        # Render template with class specification
        class_spec = self.to_dict()
        return template.render(**class_spec)

    def save_templates(self, output_dir: str = "./templates") -> Dict[str, str]:
        """
        Save the Jinja templates for this class and its maker.

        Args:
            output_dir: Directory to save templates

        Returns:
            Dictionary mapping template names to file paths
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate templates
        class_template = self.generate_class_template()
        maker_template = self.generate_maker_template()

        # Save templates
        class_template_path = os.path.join(output_dir, f"{self.class_name.lower()}.j2")
        with open(class_template_path, 'w') as f:
            f.write(class_template)

        maker_template_path = os.path.join(output_dir, f"{self.class_name.lower()}maker.j2")
        with open(maker_template_path, 'w') as f:
            f.write(maker_template)

        return {
            'class_template': class_template_path,
            'maker_template': maker_template_path
        }

    def generate_code_files(self, output_dir: str = "./generated") -> Dict[str, str]:
        """
        Generate actual Python code files for this class and its maker.

        Args:
            output_dir: Directory to save Python files

        Returns:
            Dictionary mapping file types to file paths
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Create Jinja environment for direct rendering
        env = jinja2.Environment()

        # Generate and save class file
        class_template = env.from_string(self.generate_class_template())
        class_content = class_template.render(**self.to_dict())

        class_file_path = os.path.join(output_dir, f"{self.class_name.lower()}.py")
        with open(class_file_path, 'w') as f:
            f.write(class_content)

        # Generate and save maker file
        maker_template = env.from_string(self.generate_maker_template())
        maker_content = maker_template.render(**self.to_dict())

        maker_file_path = os.path.join(output_dir, f"{self.class_name.lower()}maker.py")
        with open(maker_file_path, 'w') as f:
            f.write(maker_content)

        return {
            'class_file': class_file_path,
            'maker_file': maker_file_path
        }

# Example usage
def create_example_templated_class():
    """Create an example templated class and generate its code."""
    # Create a templated class
    example = TemplatedClass(
        class_name="CustomerProfile",
        class_description="A dynamically configurable customer profile"
    )

    # Add attributes
    example.add_attribute("name", "", type_annotation=str, description="Customer's full name")
    example.add_attribute("email", "", type_annotation=str, description="Customer's email address")
    example.add_attribute("age", 0, type_annotation=int, description="Customer's age")
    example.add_attribute("loyalty_points", 0, type_annotation=int, description="Customer's loyalty points")

    # Add a computed attribute
    example.add_attribute(
        "loyalty_tier", 
        lambda self: "Gold" if self.loyalty_points > 1000 else "Silver" if self.loyalty_points > 500 else "Bronze",
        computed=True,
        dependencies=["loyalty_points"],
        description="Customer's loyalty tier based on points"
    )

    # Add methods
    example.add_method(
        "format_customer_info",
        lambda self: f"Customer: {self.name}, Email: {self.email}, Age: {self.age}\nLoyalty: {self.loyalty_tier} ({self.loyalty_points} points)",
        description="Format customer information as a string",
        add_to_sequence=True
    )

    example.add_method(
        "add_points",
        lambda self, points: self.__dict__.update(loyalty_points=self.loyalty_points + points),
        description="Add loyalty points to the customer's account",
        parameters=["self", "points: int"],
        return_type=None
    )

    # Set template sequence
    example.set_template_sequence(["format_customer_info"])

    # Generate code files
    files = example.generate_code_files("./example_output")

    # Also save the templates
    templates = example.save_templates("./example_templates")

    print(f"Generated files: {files}")
    print(f"Generated templates: {templates}")

    return example

if __name__ == "__main__":
    example = create_example_templated_class()

    # Show the template that would generate this class
    print("\nCLASS TEMPLATE:")
    print(example.generate_class_template())

    print("\nMAKER TEMPLATE:")
    print(example.generate_maker_template())