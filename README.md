# Ecosystem 

## About this fork

This is a prototype to determine what features of this code are valid an useful and which are not. It is meant as a compilation of ideas to improve the original [Ecosystem](https://github.com/PeregrineLabs/Ecosystem).

```python
from ecosystem import Ecosystem, Environment
import os
import subprocess


eco = Ecosystem()
env = eco.get_tools('maya2016.5', 'mtoa1.2.7.3', 'alShaders1.0.0rc14')

# OR

maya_tool = eco.get_tool('maya2016.5')
mtoa_tool = eco.get_tool('mtoa1.2.7.3')
alshaders_tool = eco.get_tool('alShaders1.0.0rc14')

env = Environment(eco, maya_tool, mtoa_tool, alshaders_tool)


# The "clean" way
print os.getenv('MAYA_LOCATION')  # Nothing specified
with env:
    print os.getenv('MAYA_LOCATION')  # Now it is
    subprocess.call('maya')

print os.getenv('MAYA_LOCATION')  # Now it has been restored to none

# The "dirty" way
env.resolve()
subprocess.call('maya')

```

```
ecosystem -t maya2016.5 mtoa1.2.7.3 alShaders1.0.0rc14 -r maya
``` 
