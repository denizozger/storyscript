# -*- coding: utf-8 -*-
from lark.lexer import Token

from storyscript.parser import Tree


class FakeTree:
    # unique prefix for all compiler-inserted paths
    prefix = '__p-'

    """
    Creates fake trees that are not in the original story source.
    """
    def __init__(self, block):
        self.block = block
        self.original_line = str(block.line())
        self.new_lines = {}
        self._check_existing_fake_lines(block)

    def _check_existing_fake_lines(self, block):
        for child in block.children:
            if child.path:
                tok = child.path.find_first_token().value
                if tok.startswith(self.prefix):
                    self.new_lines[tok] = False

    def line(self):
        """
        Creates fake line numbers. The strings are decreasingly sorted,
        so that the resulting tree is compiled correctly.
        """
        line = self.original_line
        parts = line.split('.')
        if len(parts) > 1:
            line = '.'.join(parts[:-1])
        # We start at .1, s.t. lines from L1 are called L1.1 and not L1.0
        # to avoid any potential confusion
        new_suffix = len(self.new_lines) + 1
        fake_line = f'{line}.{new_suffix}'
        self.new_lines[fake_line] = None
        return fake_line

    def get_line(self, tree):
        """
        Gets the tree line if it's a new one, otherwise creates it.
        """
        if tree.line() in self.new_lines:
            return tree.line()
        return self.line()

    def path(self, name=None, line=None):
        """
        Creates a fake tree path.
        """
        if line is None:
            line = self.line()
        if name is None:
            name = f'{self.prefix}{line}'
        return Tree('path', [Token('NAME', name, line=line)])

    def mark_line(self, node, line):
        """
        Updates the line for all tokens of a given `node`.
        """
        for child in node.children:
            if isinstance(child, Token):
                child.line = line
            else:
                self.mark_line(child, line)

    def assignment(self, value):
        """
        Creates a fake assignment tree, equivalent to "$fake = value"
        """
        line = self.get_line(value)
        first_token = value.find_first_token()
        first_token.line = line
        path = self.path(line=line)
        return self.assignment_path(path, value, line)

    def assignment_path(self, path, value, line):
        """
        Adds a new assignment: `path` = `value`
        """
        # updates all tokens
        self.mark_line(value, line)
        equals = Token('EQUALS', '=', line=line)
        if value.data == 'base_expression':
            expr = value
        else:
            expr = Tree('base_expression', [value])
        fragment = Tree('assignment_fragment', [equals, expr])
        return Tree('assignment', [path, fragment])

    def find_insert_pos(self, original_line):
        """
        Finds the insert position for a targeted line in the fake tree block.
        """
        for i, n in enumerate(self.block.children):
            line = n.line()
            if line == original_line:
                return i
        # use the last position as insert position by default
        # this inserts the new assignment node _before_ the last node
        return -1

    def add_assignment(self, value, original_line):
        """
        Creates an assignments and adds it to the current block
        Returns a fake path reference to this assignment
        """
        assert len(self.block.children) >= 1

        insert_pos = self.find_insert_pos(original_line)
        assignment = self.assignment(value)

        self.block.children = [
            *self.block.children[:insert_pos],
            assignment,
            *self.block.children[insert_pos:],
        ]

        # we need a new node, s.t. already inserted
        # fake nodes don't get changed
        name = Token('NAME', assignment.path.child(0), line=original_line)
        fake_path = Tree('path', [name])
        return fake_path
