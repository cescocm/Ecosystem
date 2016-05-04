# Ecosystem 

## About this fork

This is a prototype to determine what features of this code are valid an useful and which are not. It is meant as a compilation of ideas to improve the original [Ecosystem](https://github.com/PeregrineLabs/Ecosystem).

### Setup

* **ECO_ENV**: Path for environment files.
* **ECO_PRESET_PATH**: Path for ecosystem presets.
* **ECO_PLUGIN_PATH**: Path for ecosystem plugins.

### Basic python usage

```python
from ecosystem import Ecosystem
import subprocess


eco = Ecosystem()
env = eco.get_environment('maya2016.5', 'mtoa1.2.7.3', 'alShaders1.0.0rc14')


# OR

maya_tool = eco.get_tool('maya2016.5')
mtoa_tool = eco.get_tool('mtoa1.2.7.3')
alshaders_tool = eco.get_tool('alShaders1.0.0rc14')

env = Environment(eco, maya_tool, mtoa_tool, alshaders_tool)

# The "clean" way
with env:
    subprocess.call('maya')

# The "dirty" way
env.resolve()
subprocess.call('maya')

```

### Retrieving an environment

```python
from ecosystem import Ecosystem
import subprocess


eco = Ecosystem()
env = eco.get_environment('maya2016.5', 'mtoa1.2.7.3', 'alShaders1.0.0rc14')

with env:
    environ = env.environ

#  ...

subprocess.call(
    'maya',
    env=environ
)

```

### Presets

```python
from ecosystem import Ecosystem
import subprocess


eco = Ecosystem()
preset = eco.get_preset('maya2016_core')

# Execute defaults
preset.run()

# Execute custom command
preset.run(command=['maya', '--prompt'])


# Further customization

with preset.get_environment():
    environ = env.environ

#  ...

subprocess.call(
    'maya',
    env=environ
)

```

### Command line usage

``` bash
ecosystem -h
ecosystem -l
ecosystem --list-presets
ecosystem -t maya2016.5 mtoa1.2.7.3 alShaders1.0.0rc14 -r maya
ecosystem -p maya2016_core -r
ecosystem -p maya2016_core -r maya
``` 
