"""Brython templating engine.

Templates in HTML pages can include:

- Python code blocks:

    <tr b-code="for item in items">
        ...
    </tr>


- Python expressions:

    {message}

- tag attributes:

    <option value="{name}", selected="{name===expected}">

Usage in Brython scripts:

    from browser.template import Template

    Template(element).render(message="ok")

replaces an element with template code by its rendering using the
key/values in kw.

Elements rendered by the template engine have an attribute "data" set to a
object with attributes set to the keyword arguments of render().

Callback functions
------------------

    <button b-on="click:increment">Increment</button>

The tag attribute "b-on" is converted so that a click on the button is
handled by the function "increment". This function takes two arguments:

    def increment(event, element):
       element.data.counter += 1

where "event" is the event object.

To make the function available in the element, pass the list of callback
functions as the second argument of Template():

    Template(element, [increment]).render(counter=0)

After a handler function is run, the element is rendered again, with the
current value of element.data.

"""
import traceback
import json
from browser import document, html

def copy(obj):
    if isinstance(obj, dict):
        res = {}
        for key, value in obj.items():
            res[key] = copy(value)
        return res
    elif isinstance(obj, (list, tuple)):
        return obj[:]
    elif isinstance(obj, set):
        return {x for x in obj}
    else:
        return obj

class ElementData:

    def __init__(self, **kw):
        self.__keys__ = set()
        for key, value in kw.items():
            object.__setattr__(self, key, value)
            self.__keys__.add(key)

    def __setattr__(self, attr, value):
        object.__setattr__(self, attr, value)
        if attr != '__keys__':
            self.__keys__.add(attr)

    def to_dict(self):
        return {k:getattr(self, k) for k in self.__keys__}

    def clone(self):
        return copy(self.to_dict())


class TemplateError(Exception):
    pass


class Template:

    def __init__(self, element, callbacks=[]):
        self.element = element
        self.line_mapping = {}
        self.line_num = 1
        self.indent = 0
        self.python = ""
        self.source = element.outerHTML
        self.parse(element)
        self.callbacks = callbacks
        self.data_cache = None

    def add(self, content, elt):
        self.python += content
        self.line_mapping[self.line_num] = elt
        if content.endswith('\n'):
            self.line_num += 1

    def add_indent(self, content, elt):
        self.add("    " * self.indent + content, elt)

    def write(self, content):
        self.html += str(content)+"\n"

    def parse(self, elt):
        is_block = False
        if elt.nodeType == 3:
            if elt.text.strip():
                lines = [line for line in elt.text.split('\n')
                    if line.split()]
                text = ' '.join(lines).replace('"', '&quot;')
                text = '"""' + text + '"""'
                if "{" in text:
                    text = "f" + text
                self.add_indent ('__write__(' + text + ')\n', elt)

        elif hasattr(elt, 'tagName'):
            start_tag = "__write__('<" + elt.tagName +"')\n"
            block = None
            attrs = []
            for item in elt.attributes:
                if item.name == "b-code":
                    block = item.value.rstrip(':') + ':'
                else:
                    value = item.value.replace('\n', '')
                    if "{" in value:
                        attr = ("__render_attr__('" + item.name + "', f'" +
                            value + "')\n")
                    else:
                        attr = "__write__(' " + item.name + '= "' + value +'"\')\n'
                    attrs.append(attr)
            end_tag = "__write__('>')\n"

            if block:
                self.add_indent(block + '\n', elt)
                self.indent += 1
                is_block = True

            self.add_indent(start_tag, elt)
            for attr in attrs:
                self.add_indent(attr, elt)

            self.add_indent(end_tag, elt)

        for child in elt.childNodes:
            self.parse(child)

        if hasattr(elt, 'tagName'):
            self.add_indent("__write__('</" + elt.tagName + ">')\n", elt)

        if is_block:
            self.indent -= 1

    def on(self, element, event, callback):
        def func(evt):
            cache = self.data.clone()
            callback(evt, self)
            new_data = self.data.to_dict()
            if new_data != cache:
                self.render(**new_data)
        element.bind(event, func)

    def render_attr(self, name, value):
        if isinstance(value, bool):
            self.html += '' if not value else ' ' + name
        else:
            self.html += ' ' + name + '="' + str(value) + '"'

    def render(self, **ns):
        """Returns the HTML code for the template, with key / values in ns.
        """
        # Add name "__write__" to namespace, alias for self.write, used in the
        # generated Python code
        self.data = ElementData(**ns)

        ns.update({'__write__': self.write,
            '__render_attr__': self.render_attr})

        self.html = ""

        # Executing the Python code will store HTML code in self.html
        try:
            exec(self.python, ns)
        except Exception as exc:
            if isinstance(exc, SyntaxError):
                line_no = exc.args[2]
            else:
                line_no = exc.traceback.tb_lineno
            elt = self.line_mapping[line_no]
            for item in elt.attributes:
                if item.name == "b-code":
                    print(self.source)
            print(exc.__class__.__name__, exc)
            return

        # replace element content by generated html
        self.element.html = self.html

        # bindings
        self.element.unbind()
        callbacks = {}
        for callback in self.callbacks:
            callbacks[callback.__name__] = callback

        for element in self.element.select("*[b-on]"):
            bindings = element.getAttribute("b-on")
            bindings = bindings.split(';')
            for binding in bindings:
                parts = binding.split(':')
                if not len(parts) == 2:
                    raise TemplateError(f"wrong binding: {binding}")
                event, func_name = [x.strip() for x in parts]
                self.on(element, event, callbacks[func_name])
