import ecosystem


_singletons = {}


def ecosystem_instance(settings='default', recreate=False):
    global _singletons

    if settings in _singletons and not recreate:
        return _singletons[settings]

    supported_settings = ['default']
    if settings not in supported_settings:
        raise ValueError('Supported singleton settings {!r}'
                         .format(supported_settings))

    if settings == 'default':
        _singletons[settings] = ecosystem.Ecosystem()

    return _singletons[settings]
