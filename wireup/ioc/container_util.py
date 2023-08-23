from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Type, Union


@dataclass(frozen=True)
class TemplatedString:
    value: str


ParameterReference = Union[str, TemplatedString]


@dataclass(frozen=True)
class ParameterWrapper:
    param: ParameterReference


@dataclass(frozen=True)
class ContainerProxyQualifier:
    qualifier: str


ContainerParameterInitializationType = Union[ContainerProxyQualifier, ParameterWrapper]


class DependencyInitializationContext:
    context: Dict[Type, Dict[str, ParameterWrapper]] = defaultdict(dict)

    def add_param(self, klass: Type, argument_name, parameter_ref: ParameterReference):
        self.context[klass][argument_name] = ParameterWrapper(parameter_ref)

    def update(self, klass: Type, params: Dict[str, ParameterReference]):
        self.context[klass].update({k: ParameterWrapper(v) for k, v in params.items()})


class ContainerProxy:
    def __init__(self, instance_supplier: Callable) -> None:
        self.__supplier = instance_supplier
        self.__proxy_object = None

    def __getattr__(self, name: Any) -> Any:
        if not self.__proxy_object:
            self.__proxy_object = self.__supplier()

        return getattr(self.__proxy_object, name)
