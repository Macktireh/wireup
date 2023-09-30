from __future__ import annotations

import inspect
from collections import defaultdict
from inspect import Parameter
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from wireup.ioc.container_util import InjectableType, ServiceLifetime
from wireup.ioc.initialization_context import AutowireTarget, InitializationContext
from wireup.ioc.util import AnnotatedParameter, is_type_autowireable, parameter_get_type_and_annotation

if TYPE_CHECKING:
    from wireup.ioc.container_util import (
        ContainerProxyQualifierValue,
    )

__T = TypeVar("__T")


class _ServiceRegistry(Generic[__T]):
    def __init__(self) -> None:
        self.known_interfaces: dict[type[__T], dict[ContainerProxyQualifierValue, type[__T]]] = {}
        self.known_impls: dict[type[__T], set[ContainerProxyQualifierValue]] = defaultdict(set)
        self.factory_functions: dict[type[__T], Callable[..., __T]] = {}

        self.context: InitializationContext[__T] = InitializationContext()

    def register_service(
        self,
        klass: type[__T],
        qualifier: ContainerProxyQualifierValue,
        lifetime: ServiceLifetime,
    ) -> None:
        if self.is_type_with_qualifier_known(klass, qualifier):
            msg = f"Cannot register type {klass} with qualifier '{qualifier}' as it already exists."
            raise ValueError(msg)

        if self.is_interface_known(klass.__base__):
            if qualifier in self.known_interfaces[klass.__base__]:
                msg = (
                    f"Cannot register implementation class {klass} for {klass.__base__} "
                    f"with qualifier '{qualifier}' as it already exists"
                )
                raise ValueError(msg)

            self.known_interfaces[klass.__base__][qualifier] = klass

        self.known_impls[klass].add(qualifier)
        self.register_context(klass, lifetime)

    def register_abstract(self, klass: type[__T]) -> None:
        self.known_interfaces[klass] = defaultdict()

    def register_factory(self, fn: Callable[..., __T], lifetime: ServiceLifetime) -> None:
        return_type = inspect.signature(fn).return_annotation

        if return_type is Parameter.empty:
            msg = "Factory functions must specify a return type denoting the type of dependency it can create."
            raise ValueError(msg)

        if self.is_impl_known_from_factory(return_type):
            msg = f"A function is already registered as a factory for dependency type {return_type}."
            raise ValueError(msg)

        if self.is_impl_known(return_type):
            msg = f"Cannot register factory function as type {return_type} is already known by the container."
            raise ValueError(msg)

        self.register_context(fn, lifetime=lifetime)
        self.factory_functions[return_type] = fn

        # The target and its lifetime just needs to be known. No need to check its dependencies
        # as the factory will be the one to create it.
        self.context.init(return_type, lifetime)

    def register_context(self, target: AutowireTarget[__T], lifetime: ServiceLifetime | None = None) -> None:
        if not self.context.init(target, lifetime):
            return

        for name, parameter in inspect.signature(target).parameters.items():
            annotated_param: AnnotatedParameter[__T] = parameter_get_type_and_annotation(parameter)

            if not (annotated_param.klass or annotated_param.annotation):
                continue

            # Add to the context only if it's something we can inject
            # or if it is a class that's not one of the builtins: int str dict etc.
            # This is the case for services which are only typed and do not require an annotation.
            if isinstance(annotated_param.annotation, InjectableType) or is_type_autowireable(annotated_param.klass):
                self.context.put(target, name, annotated_param)

    def is_impl_known(self, klass: type[__T]) -> bool:
        return klass in self.known_impls

    def is_impl_with_qualifier_known(self, klass: type[__T], qualifier_value: ContainerProxyQualifierValue) -> bool:
        return klass in self.known_impls and qualifier_value in self.known_impls[klass]

    def is_type_with_qualifier_known(self, klass: type[__T], qualifier: ContainerProxyQualifierValue) -> bool:
        is_known_impl = self.is_impl_with_qualifier_known(klass, qualifier)
        is_known_intf = self.__is_interface_with_qualifier_known(klass, qualifier)
        is_known_from_factory = self.is_impl_known_from_factory(klass)

        return is_known_impl or is_known_intf or is_known_from_factory

    def __is_interface_with_qualifier_known(
        self,
        klass: type[__T],
        qualifier: ContainerProxyQualifierValue,
    ) -> bool:
        return klass in self.known_interfaces and qualifier in self.known_interfaces[klass]

    def is_impl_known_from_factory(self, klass: type[__T]) -> bool:
        return klass in self.factory_functions

    def is_impl_singleton(self, klass: type[__T]) -> bool:
        return self.context.lifetime.get(klass) == ServiceLifetime.SINGLETON

    def is_interface_known(self, klass: type[__T]) -> bool:
        return klass in self.known_interfaces
