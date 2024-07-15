import string
import ast
from nnf import Var, And, Or

class MyTransformer(ast.NodeTransformer):
    """Traverses tree using DFS and modifies nodes"""

    def __init__(self):
        self.list = []
        self.dict = {}
        self.alpha = list(string.ascii_uppercase)+ list(string.ascii_lowercase) + \
        list([chr(x) for x in range(945,1012)])
        self.count = -1

    def find_parents(self, node, parent):
        node.parent = parent
        for n in ast.iter_child_nodes(node):
            self.find_parents(n, node)

    # Logical operators
    def visit_And(self, node):  
        super().generic_visit(node)
        node.formula = And()
        return node

    def visit_Or(self, node):
        super().generic_visit(node)
        node.formula = Or()
        return node

    def visit_Not(self, node):
        super().generic_visit(node)
        node.formula = False
        return node

    def visit_BoolOp(self, node):
        """ Assigns relevant logical operators to children of And and Or nodes"""
        super().generic_visit(node)
        try:
            items = []
            for i in node.values:
                items.append(i.formula)
            if isinstance(node.op.formula, Or):
                node.formula = node.values[0].formula | node.values[1].formula
            if isinstance(node.op.formula, And):
                node.formula = node.values[0].formula & node.values[1].formula
        except AttributeError:
            pass
        return node

    def visit_Name(self, node):
        """ Assigns prop. variables to bare python variables (e.g. if a: )"""
        super().generic_visit(node)
        if isinstance(node.parent, (ast.If, ast.IfExp, ast.While)):
            if ast.dump(node) in self.dict:  # familiar proposition
                node.formula = Var(self.dict.get(ast.dump(node)))
            else: # novel proposition
                self.count += 1
                self.dict.update({ast.dump(node):(self.alpha[self.count])})
                node.formula = Var(self.alpha[self.count])
        return node

    def visit_UnaryOp(self, node):
        """ Assigns negation of prop. logic to an unary node, if unary operator is Not"""
        super().generic_visit(node)
        if isinstance(node.op, ast.Not):
            if ast.dump(node.operand) in self.dict:  # familiar proposition
                node.formula = Var(self.dict.get(ast.dump(node.operand)), False)
            else: # novel proposition
                self.count += 1
                self.dict.update({ast.dump(node.operand):self.alpha[self.count]})
                node.formula = Var(self.alpha[self.count], False)
        return node
    
    def visit_If(self, node):
        """ Assigns logic to body of if, elif, else and nested if statements (as conjunctions) """
        try:
            if hasattr(node, 'ancestor'): # Has condition in ancestry line
                for n in node.body:
                    n.ancestor = super().visit(node.test).formula & node.ancestor
                # Else
                if node.orelse != [] and node.orelse is not None and not isinstance(node.orelse[0], ast.If):
                    for i in node.orelse:
                        i.formula = node.ancestor & super().visit(node.test).formula.negate()
                # Elif
                if node.orelse != [] and node.orelse is not None and isinstance(node.orelse[0], ast.If):
                    node.orelse[0].ancestor = node.ancestor & node.test.formula.negate()
                    for i in node.orelse:
                        for j in i.body:
                            j.formula = super().visit(i.test).formula & i.ancestor
                # Body
                for i in node.body: 
                    if not isinstance(i, (ast.If, ast.While)):
                        i.formula = super().visit(node.test).formula & node.ancestor
            
            else: # No previous ancestor conditions
                for n in node.body:
                    n.ancestor = super().visit(node.test).formula
                # Else
                if node.orelse != [] and node.orelse is not None and not isinstance(node.orelse[0], ast.If):
                    for i in node.orelse:
                        i.formula = super().visit(node.test).formula.negate()
                # Elif
                if node.orelse != [] and node.orelse is not None and isinstance(node.orelse[0], ast.If):
                    node.orelse[0].ancestor = super().visit(node.test).formula.negate()
                    for i in node.orelse:
                        for j in i.body:
                            j.formula = super().visit(i.test).formula
                # Body
                for i in node.body:
                    if not isinstance(i, (ast.If, ast.While)):
                        i.formula = super().visit(node.test).formula
        except AttributeError:
            pass
        super().generic_visit(node)
        return node
    
    def visit_IfExp(self, node): 
        """ Assigns logic to same-line if else statments """
        super().generic_visit(node)
        try:
            node.body.formula = node.test.formula
            node.orelse.formula = node.test.formula.negate()
        except AttributeError:
            pass
        return node
    
    def visit_Compare(self, node):
        """ Assigns logic to a comparison (e.g. a < 5) """
        super().generic_visit(node)
        if ast.dump(node) in self.dict:  # familiar proposition
            node.formula = self.dict.get(ast.dump(node))
        else: # novel proposition
            self.count += 1
            self.dict.update({ast.dump(node): Var(self.alpha[self.count])})
            node.formula = Var(self.alpha[self.count])
        return node
    
    def visit_Call(self, node):
        """ Assigns logic to a function call """
        super().generic_visit(node)
        if isinstance(node.parent, (ast.If, ast.BoolOp, ast.UnaryOp)):
            if ast.dump(node) in self.dict:  # familiar proposition
                node.formula = self.dict.get(ast.dump(node))
            else: # novel proposition
                self.count += 1
                self.dict.update({ast.dump(node): Var(self.alpha[self.count])})
                node.formula = Var(self.alpha[self.count])
        return node
    
    def visit_ListComp(self, node):
        super().generic_visit(node)
        if hasattr(node.generators[0], 'formula'):
            node.formula = node.generators[0].formula
        return node
    
    def visit_comprehension(self, node):
        super().generic_visit(node)
        if node.ifs == []:
            return node
        node.formula = node.ifs[0].formula
        return node
    
    def visit_While(self, node):
        """ Assigns logic to body of while loops and nested while (as conjunctions) """
        try:
            if hasattr(node, 'ancestor'): # Has condition in ancestry line
                for n in ast.iter_child_nodes(node):
                    n.ancestor = super().visit(node.test).formula & node.ancestor
                for i in node.body:
                    if not isinstance(i, (ast.While, ast.If)):
                        i.formula = super().visit(node.test).formula & node.ancestor
            else:
                for n in ast.iter_child_nodes(node):
                    n.ancestor = super().visit(node.test).formula
                for i in node.body:
                    if not isinstance(i, (ast.While, ast.If)):
                        i.formula = super().visit(node.test).formula
        except AttributeError:
            pass
        super().generic_visit(node)
        return node
    
    def visit_For(self, node):
        if hasattr(node, 'ancestor'):
            for i in node.body:
                i.ancestor = node.ancestor
        super().generic_visit(node)
        return node

class MyVisitor(ast.NodeVisitor):
    """ Visits nodes in our modified tree """

    def __init__(self):
        self.list = []

    # Override visit methods so we don't append children nodes to our list
    def visit_And(self, node):
        super().generic_visit(node)

    def visit_Or(self, node):
        super().generic_visit(node)

    def visit_Not(self, node):
        super().generic_visit(node)

    def visit_Compare(self, node):
        super().generic_visit(node)
    
    def visit_Call(self, node):
        super().generic_visit(node)

    def visit_UnaryOp(self, node):
        super().generic_visit(node)

    def visit_BoolOp(self, node):
        super().generic_visit(node)
    
    def visit_Name(self, node):
        super().generic_visit(node)
    
    def visit_While(self, node):
        super().generic_visit(node)
    
    def visit_For(self, node):
        super().generic_visit(node)

    def generic_visit(self, node):
        """ Visits all nodes except those of type explicitly defined above """
        super().generic_visit(node)
        try:
            self.list.append((node.formula, node.lineno))
        except AttributeError:
            pass