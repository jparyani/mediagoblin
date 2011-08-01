from docutils import nodes

from sphinx.util.compat import Directive, make_admonition

class youcanhelp_node(nodes.Admonition, nodes.Element):
    pass

class YouCanHelp(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        ad = make_admonition(
            youcanhelp_node,
            self.name,
            ["You Can Help!"],
            self.options,
            self.content,
            self.lineno,
            self.content_offset,
            self.block_text,
            self.state,
            self.state_machine)
        ad[0].line = self.lineno
        return ad

def visit_youcanhelp_node(self, node):
    self.visit_admonition(node)

def depart_youcanhelp_node(self, node):
    self.depart_admonition(node)

def setup(app):
    app.add_node(
        youcanhelp_node,
        html=(visit_youcanhelp_node, depart_youcanhelp_node),
        latex=(visit_youcanhelp_node, depart_youcanhelp_node),
        text=(visit_youcanhelp_node, depart_youcanhelp_node)
        )
    
    app.add_directive('youcanhelp', YouCanHelp)
