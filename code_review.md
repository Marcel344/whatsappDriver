# Code Review
This markdown document will hold multiple sections, each relatively different from the others. Each section is aimed at one specific way to make your code better, my "pythonic", or more easily understood. Each section will come with examples in your code, as well as a different suggested solution (No one gets better from just hearing "this part could be better". You'd want to see what the alternatives are, and why they're better.)

I'm going to be reading through the `unix` portion, but going to assume Windows is mostly the same.

## Package Structure

### GitIgnore
Currently, your project has both `.DS_Store` files (which macs add to your file system) and `__pycache__` files, which contain the Python bytecode. It is typically bad practice to include unnecessary files, which the `.DS_Store` will fall under, or potentially build breaking files (`__pycache__` as things break when the platform doesn't match the bytecode.)

A good starting place for a Python gitignore is (here)[https://github.com/github/gitignore/blob/master/Python.gitignore]. You can add / remove as needed.

### Setup.py
Currently, your `setup.py` file does not contain the `python_requires` keyword nor any description (typically a short description is provided in text, and a long description is provided via a `.md` or `.rst` file). If you provide the content via `.md` file, you also need to specify a keyword argument `long_description_content_type="text/markdown"`.

You'd also likely want to list yourself as the author and an email, but these are optional.

### Requirements.txt
Currently, there are packages in the `requirements.txt` files that aren't pinned to specific versions. This means that if one of those packages has a backwards incompatable change, your code that previously was working can break.

#### Use standard packages for standard things
It looks like, in general, you've done a good job at this (BeautifulSoup, etc.), but `httplib` is a very low level library (when you need 100% control over everything you're doing). In the `connectionThread.py` file, this library is used directly and shouldn't be. If you want to continue to use standard library modules, I'd look into `urllib`, and if you're okay with 3rd party packages (even though it's kind of the standard), look at `requests`.

## General Code Structure
Python's conventions are to use `ProperCase` for class names, and `snake_case` for variable and method names. For example, in the `forwader.py` file, in the `WhatsappForwader.__init__` method, `self.contactDict` can be `self.contact_dict`.

In the `main.py` file, on line 91 (as an example, not exhaustive list), comparisons to `None` should be done like so per convention:

```python
self.loadedCsvFile is not None
self.importedNamesCsvFile is None
```

### My Personal Preference
In the `globalVariables` file, there are 2 options; `NEW_NAMES` and `IMPORTED_NAMES`. This looks an awful lot like an enum, which Python has a standard library packge for. While this is more of my personal preference than standard convention, any related constants belonging to the same group should use enums.



### Comments
Commenting code is typically a good thing, and the amount of comments everywhere has definitely helped me, a completely random 3rd party, understand your code better without knowing much of anything about Selenium nor QT. However, there are some comments that are redundant.

For example, on line 41 of `forwader.py`, there's a sleep for 1 second with a comment saying it's sleeping for 1 second. This comment is redundant, and should either be removed or updated to say why it's sleeping. A good rule of thumb is that if your comment explains _why_ something is happening, it's a good idea to leave in.

In addition, it's typically not recommended to have inline comments. There are some situations where this is okay, but typically you'd have the comment on the line above.

### Methods

#### Getters and Setters
Python does have the option to implement getters and setters, however the way you'd want to do that is different than implemented in `forwader.py`. Python believes that accessing public attributes is fair game on classes, so you can just reference them as `instance.ImagePath`, as an example. When setting them, the same is true; you can set them directly as `instance.ImagePath = "whatever"`. If you want to protect a variable from being publicly set or read, convention is to implement it with a single leading underscore, such as `instance._ImagePath`.

#### File Handling Methods
Python has a concept of `context managers`, which allow you to do syntax such as:

```python
with open("my_file.txt", "a") as f:
    f.write("new data")
```

What this does is automatically closes the file when you're done with it, and always closes the file, even when errors occur. It's typically best practice to use these, and I've never actually found a good reason not to.


#### Method Length
The `run` method in `forwader.py` is > 300 lines long, which is far too long. A good rule of thumb is keeping methods <= 20 lines of code. Where I'd personally break the `run` method are creating new methods, one for each `self.MODE` option. Then, whatever data you're pulling out of the `BeautifulSoup` extraction (line ~64 as an example) should also be a method, explaining what it does. For example, `parse_contact_from_document` or `get_contact_from_document`. 

Another good method would be to replace the lines on 105 and 111. Without your comments (which, again, very good use of comments), I'd have no idea what that does. So, one solution would be to put that code into a method with a human readible name and remove the comment. So the new code could look like:

```python
def get_contact_elements(self):
    # override the elements to fetch updated names
    elements = self.driver.find_elements_by_xpath(
        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]'
    )
```

Another random note here is to not change things while you're iterating over them. So the method referenced above where it's refreshing the `elements` list, should be refactored in a way that that doesn't happen.

As a goal, specifically for the `run` method, you want to keep any logic of what's actually happening outside of this method, while keeping all things related to QT here. For example, lines 90-93 definitely belong in the `run` method.

Another example of this is the `runThread` method in the `main.py` file. It seems that each combination of data already existing and not existing is handled here, where each specific scenario can be handled in its own method (or if you can parameterize it, you can re-use the methods).


## Concluding Notes
All things considered, given how messy all code is for creating UIs, your code looks good! Its clear that Python likely wasn't your first programming language (from the `camelCasing`), but you're well on your way to getting better at Python! Let me know if you have any questions!