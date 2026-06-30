"""
Core components of the Pydantic Stack library.

This module contains the minimal foundation for creating stackable, renderable
Pydantic models that can be composed into structured string outputs.
"""

from pydantic import BaseModel, Field
from typing import List, Any
from abc import abstractmethod


class RenderablePiece(BaseModel):
    """
    Base class for any Pydantic model that can render itself to a string.
    
    This is the fundamental building block of the Pydantic Stack system.
    All models that want to be part of a MetaStack must inherit from this class
    and implement the render() method.
    
    The render() method is where the magic happens - it converts the structured
    Pydantic data into the final string representation. This could be:
    - HTML markup
    - Markdown text  
    - Plain text
    - JSON strings
    - Code snippets
    - Any other string format
    
    Agents learn how to use RenderablePiece subclasses by calling help() on them
    and understanding their fields, validation rules, and render() behavior.
    
    Example:
        ```python
        class Title(RenderablePiece):
            '''A title with configurable heading level.'''
            text: str = Field(..., description="The title text")
            level: int = Field(1, ge=1, le=6, description="Heading level (1-6)")
            
            def render(self) -> str:
                '''Render as markdown heading.'''
                return f"{'#' * self.level} {self.text}"
        
        # Agent learns: Title needs 'text' and optional 'level'
        # Agent learns: render() produces markdown heading format
        title = Title(text="Hello", level=2)
        print(title.render())  # ## Hello
        ```
    
    Fields:
        No required fields by default. Subclasses define their own fields
        based on what data they need to render properly.
    """
    
    @abstractmethod
    def render(self) -> str:
        """
        Convert this piece to its string representation.
        
        This is the ONLY method that subclasses MUST implement.
        The render() method should:
        
        1. Take all the Pydantic fields of the model
        2. Transform them into the desired string format
        3. Return the final string representation
        
        The agent learns rendering patterns by:
        - Calling help(YourClass.render) to read this docstring
        - Examining successful render() outputs
        - Understanding the transformation from fields -> string
        
        Returns:
            str: The string representation of this piece
            
        Raises:
            NotImplementedError: If subclass doesn't implement render()
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement render() method"
        )


class MetaStack(BaseModel):
    """
    Universal container for stacking any RenderablePiece models into structured output.
    
    MetaStack is model-agnostic - it doesn't care what specific RenderablePiece
    subclasses you put in it. It just calls render() on each piece and combines
    them according to the specified separator.
    
    This is the composition engine that allows agents to:
    - Experiment with different piece combinations
    - Learn which combinations work well together  
    - Generate structured outputs for any domain
    - Discover new patterns by trying different orderings
    
    The agent learns MetaStack patterns by:
    - Understanding that pieces is a List[RenderablePiece]
    - Experimenting with different piece orders
    - Learning effective separator strategies
    - Discovering which piece types compose well
    
    Example:
        ```python
        # Agent learns: MetaStack accepts any RenderablePiece subclasses
        stack = MetaStack(
            pieces=[
                Title(text="My Blog Post", level=1),
                Paragraph(content="Introduction paragraph..."),
                Title(text="Section 1", level=2), 
                Paragraph(content="Section content..."),
            ],
            separator="\\n\\n"  # Double newlines between pieces
        )
        
        # Agent learns: render() combines all pieces with separator
        output = stack.render()
        ```
    
    Fields:
        pieces: List of RenderablePiece instances to render in order
        separator: String used to join rendered pieces (default: "\\n")
    """
    
    pieces: List[RenderablePiece] = Field(
        default_factory=list,
        description="List of RenderablePiece instances to render in order"
    )
    
    separator: str = Field(
        default="\\n",
        description="String used to join rendered pieces together"
    )
    
    def render(self) -> str:
        """
        Render all pieces to final string output.
        
        This method orchestrates the rendering process:
        1. Calls render() on each piece in the pieces list
        2. Joins all rendered strings with the separator
        3. Returns the final combined output
        
        The agent learns the rendering flow:
        - MetaStack.render() -> calls each piece.render() -> joins with separator
        
        Returns:
            str: Final combined output of all rendered pieces
            
        Example:
            ```python
            stack = MetaStack(
                pieces=[Title(text="Hello"), Paragraph(content="World")],
                separator=" | "
            )
            result = stack.render()  # "# Hello | World"
            ```
        """
        if not self.pieces:
            return ""
        
        rendered_pieces = [piece.render() for piece in self.pieces]
        return self.separator.join(rendered_pieces)
    
    def add_piece(self, piece: RenderablePiece) -> None:
        """
        Add a new piece to the end of the stack.
        
        Convenience method for building stacks incrementally.
        The agent can learn to use this for dynamic stack construction.
        
        Args:
            piece: RenderablePiece instance to add to the stack
        """
        self.pieces.append(piece)
    
    def insert_piece(self, index: int, piece: RenderablePiece) -> None:
        """
        Insert a piece at a specific position in the stack.
        
        Allows the agent to learn precise positioning strategies
        for different types of content organization.
        
        Args:
            index: Position to insert the piece (0-based)
            piece: RenderablePiece instance to insert
        """
        self.pieces.insert(index, piece)


def generate_output_from_metastack(meta_stack: MetaStack) -> str:
    """
    Generate final string output from a MetaStack.
    
    This is the top-level function that agents use to convert a composed
    MetaStack into its final string representation. It's essentially a
    wrapper around MetaStack.render() that provides a clear functional
    interface for the generation process.
    
    The agent learns this as the standard pipeline:
    1. Build a MetaStack with appropriate pieces
    2. Call generate_output_from_metastack() to get final result
    3. Use the result as the structured string output
    
    This function exists to:
    - Provide a clear, discoverable entry point for agents
    - Allow for future enhancements (validation, post-processing, etc.)  
    - Make the generation process explicit and learnable
    
    Args:
        meta_stack: MetaStack instance containing the pieces to render
        
    Returns:
        str: Final rendered output combining all pieces in the stack
        
    Example:
        ```python
        # Agent learns this standard pattern:
        stack = MetaStack(pieces=[...])
        final_output = generate_output_from_metastack(stack)
        ```
    """
    return meta_stack.render()