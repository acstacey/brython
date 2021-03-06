module **javascript**
---------------------

The module **javascript** allows interaction with the objects defined in 
Javascript programs and libraries present in the same page as the Brython 
program.

**javascript**.`JSConstructor(`_constructor_`)`

> Class whose instances represent Javascript constructors, ie functions 
> used with the Javascript keyword `new`.

> <code>JSConstructor(_constructor_)</code> returns a Brython object. This object 
> is callable ; it returns the object built by the constructor *constructor*, 
> tranformed into a Python object according to the conversion table in
> <a href="jsobjects.html">Javascript objects and libraries</a>.

> _WARNING : this function is deprecated since version 3.1.1. Instead of `py_class = JSConstructor(js_class)` use `py_class = js_class.new`_


**javascript**.`JSObject(`_js\_object_`)`

> Class for Javascript objects that can't be converted "naturally" into Python
> objects when they are referenced as attributes of `browser.window`. This
> class is used internally by Brython and should not be used in scripts.

> See <a href="jsobjects.html">Javascript objects and libraries</a>.

> _WARNING : this function is deprecated since version 3.1.1. The attributes of object `window` are already instances of the class `JSObject`_

**javascript**.`py2js(`_src_`)`
> Returns the Javascript code generated by Brython from the Python source code _src_.

**javascript**.`this()`
> Returns the Brython object matching the value of the Javascript object `this`. It
> may be useful when using Javascript frameworks, eg when a callback function uses
> the value of `this`.
