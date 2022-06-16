## Tip for the module debugging:

use `autoreload` magic (see https://ipython.org/ipython-doc/3/config/extensions/autoreload.html for more info):

```ipython
%load_ext autoreload # enable magic
%autoreload 2 #Reload all modules (except those excluded by %aimport) every time before executing the Python code typed.

```