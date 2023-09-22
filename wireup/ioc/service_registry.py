from __future__ import annotations

import inspect
from collections import defaultdict
from inspect import Parameter, Signature
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from wireup.ioc.container_util import ServiceLifetime
from wireup.ioc.util import AnnotatedParameter, parameter_get_type_and_annotation

if TYPE_CHECKING:
    from wireup.ioc.container_util import (
        ContainerProxyQualifierValue,
    )

__T = TypeVar("__T")


class _ContainerTargetMeta(Generic[__T]):
    def __init__(self, signature: Signature) -> None:
        self.signature: dict[str, AnnotatedParameter[__T]] = {}

        for name, parameter in signature.parameters.items():
            annotated_param: AnnotatedParameter[__T] = parameter_get_type_and_annotation(parameter)

            if annotated_param.annotation or annotated_param.klass:
                self.signature[name] = annotated_param


class _ContainerClassMetadata(_ContainerTargetMeta[__T]):
    def __init__(self, signature: Signature, lifetime: ServiceLifetime) -> None:
        super().__init__(signature)
        self.lifetime = lifetime


class _ServiceRegistry(Generic[__T]):
    def __init__(self) -> None:
        self.known_interfaces: dict[type[__T], dict[ContainerProxyQualifierValue, type[__T]]] = {}
        self.known_impls: dict[type[__T], set[ContainerProxyQualifierValue]] = defaultdict(set)
        self.factory_functions: dict[type[__T], Callable[..., __T]] = {}

        self.impl_metadata: dict[type[__T], _ContainerClassMetadata[__T]] = {}
        self.injection_target_metadata: dict[Callable[..., Any], _ContainerTargetMeta[__T]] = {}

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
        self.__register_impl_meta(klass, lifetime)

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

        self.__register_impl_meta(return_type, lifetime=lifetime)
        self.register_targets_meta(fn)
        self.factory_functions[return_type] = fn

    def register_targets_meta(self, fn: Callable[..., Any]) -> None:
        if fn not in self.injection_target_metadata:
            self.injection_target_metadata[fn] = _ContainerTargetMeta(signature=inspect.signature(fn))

    def __register_impl_meta(self, klass: type[__T], lifetime: ServiceLifetime) -> None:
        self.impl_metadata[klass] = _ContainerClassMetadata(signature=inspect.signature(klass), lifetime=lifetime)

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
        meta = self.impl_metadata.get(klass)

        return meta is not None and meta.lifetime == ServiceLifetime.SINGLETON

    def is_interface_known(self, klass: type[__T]) -> bool:
        return klass in self.known_interfaces
