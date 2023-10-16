from __future__ import annotations

from typing import Any

from wireup.annotation import ParameterEnum, Wire, wire
from wireup.ioc.dependency_container import DependencyContainer
from wireup.ioc.parameter import ParameterBag
from wireup.ioc.types import ParameterReference, ServiceLifetime
from wireup.ioc.util import import_all_in_module
from wireup.util import register_all_in_module, warmup_container

container: DependencyContainer[Any] = DependencyContainer(ParameterBag())
"""Singleton DI container instance.

Use when your application only needs one container.
"""


__all__ = [
    "DependencyContainer",
    "ParameterBag",
    "ParameterEnum",
    "ParameterReference",
    "ServiceLifetime",
    "Wire",
    "container",
    "import_all_in_module",
    "register_all_in_module",
    "warmup_container",
    "wire",
]
