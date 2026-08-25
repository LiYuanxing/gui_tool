#
# Load vendor DSDL that pydronecan does not include by default.
# Stock load_dsdl() only scans: uavcan, dronecan, ardupilot, com, cuav.
#

import os
from logging import getLogger

import dronecan

logger = getLogger(__name__)

_BUILTIN_NAMESPACES = frozenset({'uavcan', 'dronecan', 'ardupilot', 'com', 'cuav'})


def vendor_dsdl_paths():
    """Namespace roots (e.g. .../hy) to pass to dronecan.load_dsdl()."""
    paths = []
    seen = set()

    def add(path):
        path = os.path.abspath(path)
        if path not in seen and os.path.isdir(path):
            seen.add(path)
            paths.append(path)

    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dsdl')
    if os.path.isdir(bundled):
        for name in sorted(os.listdir(bundled)):
            add(os.path.join(bundled, name))

    specs = os.path.join(os.path.dirname(os.path.abspath(dronecan.__file__)), 'dsdl_specs')
    if os.path.isdir(specs):
        for name in sorted(os.listdir(specs)):
            if name in _BUILTIN_NAMESPACES or name.startswith('.'):
                continue
            add(os.path.join(specs, name))

    return paths


def load_vendor_dsdl(*extra):
    """Reload DSDL including extra vendor namespaces such as hy.control.ControlSetpoint."""
    paths = vendor_dsdl_paths()
    for item in extra:
        if item and os.path.isdir(item):
            item = os.path.abspath(item)
            if item not in paths:
                paths.append(item)
    if not paths:
        return []
    logger.info('Loading extra DSDL from %s', paths)
    dronecan.load_dsdl(*paths)
    return paths
