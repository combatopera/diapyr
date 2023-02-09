# diapyr
Constructor injection for Python

## Overview
* Automatic wiring between application objects
* Declare what collaborator types you want in your constructor using an @types decorator, they correspond with params
    * You can decorate a (factory) function in the same way, in which case the return type must also be declared using 'this' kwarg
    * Surround a type in square brackets if you want a list of all matching objects, normally diapyr provides a unique match
* Add such classes/factories to a DI instance
    * You can also add objects, for example an application config object
* Request a type from the DI instance and diapyr will attempt to make it for you, along with the rest of the object graph
* Instances are cached in the DI object
    * On exit from 'with' clause, dispose is called on any created instances that have it

## Motivation
* Manual wiring is messy and tedious especially when an app gets big
* Constructor injection avoids spaghetti code
* It's trivial to depend on an object anywhere in the graph as long as you don't create a reference cycle e.g. most objects will depend on the same config instance
    * No need to resort to globals, which come with a big risk of leaking state between unit tests
* Unit testing is easy when an object only interacts with what was passed into its constructor

## Convention
* When depending on a config object the constructor should first extract what it needs and assign those values to fields
* Collaborators should also be assigned to fields, and ideally the constructor won't do anything else

## Advanced
* Parameter defaults are honoured, this can be used to depend on module log object in real life and pass in a mock in unit tests
* Decorating an instance method (without 'this' kwarg) will make it behave as an additional constructor
    * Take advantage of name mangling (start with double underscore e.g. \_\_init) to avoid having to call super
* Decorating an instance method with 'this' kwarg will make it behave as a factory function
    * Adding a class to DI will implicity add all such methods it has as factories
* You can play fast and loose with types, diapyr doesn't care whether a factoried object satisfies the declared type

## Install
These are generic installation instructions.

### To use, permanently
The quickest way to get started is to install the current release from PyPI:
```
pip3 install --user diapyr
```

### To use, temporarily
If you prefer to keep .local clean, install to a virtualenv:
```
python3 -m venv venvname
venvname/bin/pip install diapyr
. venvname/bin/activate
```

### To develop
First clone the repo using HTTP or SSH:
```
git clone https://github.com/combatopera/diapyr.git
git clone git@github.com:combatopera/diapyr.git
```
Now use pyven's pipify to create a setup.py, which pip can then use to install the project editably:
```
python3 -m venv pyvenvenv
pyvenvenv/bin/pip install pyven
pyvenvenv/bin/pipify diapyr

python3 -m venv venvname
venvname/bin/pip install -e diapyr
. venvname/bin/activate
```
