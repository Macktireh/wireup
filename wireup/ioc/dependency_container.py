from __future__ import annotations

import asyncio
import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from .container_util import (
    ContainerInjectionRequest,
    ContainerProxy,
    ContainerProxyQualifier,
    ContainerProxyQualifierValue,
    DependencyInitializationContext,
    ParameterWrapper,
)
from .service_registry import _ServiceRegistry
from .util import AnnotatedParameter, find_classes_in_module

if TYPE_CHECKING:
    from types import ModuleType

    from .parameter import ParameterBag

__T = TypeVar("__T")


class DependencyContainer:
    """Dependency Injection and Service Locator container registry.

    This contains all the necessary information to initialize registered classes.
    Objects instantiated by the container are lazily loaded and initialized only on first use.

    Provides the following decorators: `register`, `abstract` and `autowire`. Use register on factory functions
    and concrete classes which are to be injected from the container.
    Abstract classes are to be used as interfaces and will not be injected directly, rather concrete classes
    which implement them will be injected instead.

    Use the `autowire` decorator on methods where dependency injection must be performed.
    Services will be injected automatically where possible. Parameters will have to be annotated as they cannot
    be located from type alone.
    """

    def __init__(self, parameter_bag: ParameterBag) -> None:
        """:param parameter_bag: ParameterBag instance holding parameter information."""
        self.__service_registry: _ServiceRegistry = _ServiceRegistry()

        self.__initialized_objects: dict[tuple[__T, ContainerProxyQualifierValue], object] = {}
        self.__initialized_proxies: dict[tuple[__T, ContainerProxyQualifierValue], ContainerProxy] = {}

        self.params: ParameterBag = parameter_bag
        self.initialization_context = DependencyInitializationContext()

    def get(self, klass: type[__T], qualifier: ContainerProxyQualifierValue = None) -> __T:
        """Get an instance of the requested type.

        Use this to locate services by their type but strongly prefer using injection instead.

        :param qualifier: Qualifier for the class if it was registered with one.
        :param klass: Class of the dependency already registered in the container.
        :return: An instance of the requested object. Always returns an existing instance when one is available.
        """
        self.__assert_dependency_exists(klass, qualifier)

        return self.__get_proxy_object(klass, qualifier)

    def abstract(self, klass: type[__T]) -> type[__T]:
        """Register a type as an interface.

        This type cannot be initialized directly and one of the components implementing this will be injected instead.
        """
        self.__service_registry.register_abstract(klass)

        return klass

    def register(
        self,
        obj: type[__T] | Callable | None = None,
        *,
        qualifier: ContainerProxyQualifierValue = None,
        singleton: bool = True,
    ) -> type[__T]:
        """Register a dependency in the container.

        Use `@register` without parameters on a class or with a single parameter `@register(qualifier=name)`
        to register this with a given name when there are multiple implementations of the interface this implements.

        Use `@register` on a function to register that function as a factory method which produces an object
        that matches its return type.

        The container stores all necessary metadata for this class and the underlying class remains unmodified.
        """
        # Allow register to be used either with or without arguments
        if obj is None:

            def decorated(inner_class: type[__T]) -> type[__T]:
                return self.register(inner_class, qualifier=qualifier, singleton=singleton)

            return decorated

        if inspect.isclass(obj):
            self.__service_registry.register_service(obj, qualifier, singleton=singleton)
        else:
            self.__service_registry.register_factory(obj, singleton=singleton)

        return obj

    def autowire(self, fn: Callable) -> Callable:
        """Automatically inject resources from the container to the decorated methods.

        Any arguments which the container does not know about will be ignored
        so that another decorator or framework can supply their values.
        This decorator can be used on both async and blocking methods.

        * Classes will be automatically injected.
        * Parameters need to be annotated in order for container to be able to resolve them
        * When injecting an interface for which there are multiple implementations you need to supply a qualifier
          using annotations.
        """
        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_inner(*args: Any, **kwargs: Any) -> Any:
                return await self.__autowire_inner(fn, *args, **kwargs)

            return async_inner

        @functools.wraps(fn)
        def sync_inner(*args: Any, **kwargs: Any) -> Any:
            return self.__autowire_inner(fn, *args, **kwargs)

        return sync_inner

    def register_all_in_module(self, module: ModuleType, pattern: str = "*") -> None:
        """Register all modules inside a given module.

        Useful when your components reside in one place, and you'd like to avoid having to `@register` each of them.
        Alternatively this can be used if you want to use the library without having to rely on decorators.

        See Also: `self.initialization_context` to wire parameters without having to use a default value.

        :param module: The package name to recursively search for classes.
        :param pattern: A pattern that will be fed to fnmatch to determine if a class will be registered or not.
        """
        for klass in find_classes_in_module(module, pattern):
            self.register(klass)

    def __autowire_inner(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        self.__service_registry.register_targets_meta(fn)

        return fn(*args, **{**kwargs, **self.__callable_get_params_to_inject(fn)})

    def __callable_get_params_to_inject(self, fn: Callable[..., Any], klass: type[__T] | None = None) -> dict:
        meta = self.__service_registry.class_meta[klass] if klass else self.__service_registry.targets_meta[fn]

        params_from_context = {
            name: self.params.get(wrapper.param) for name, wrapper in self.initialization_context.context[klass].items()
        }

        values_from_parameters = {}
        for name, annotated_parameter in meta.signature.items():
            # Dealing with parameter, return the value as we cannot proxy int str etc.
            # We don't want to check here for none because as long as it exists in the bag, the value is good.
            if isinstance(annotated_parameter.annotation, ParameterWrapper):
                values_from_parameters[name] = self.params.get(annotated_parameter.annotation.param)

            if obj := self.__initialize_container_proxy_object_from_parameter(annotated_parameter):
                values_from_parameters[name] = obj

        return {**params_from_context, **values_from_parameters}

    def __get(self, klass: type[__T], qualifier: ContainerProxyQualifierValue) -> __T:
        """Create the real instances of dependencies. Additional dependencies they may have will be lazily created."""
        is_singleton = self.__service_registry.is_impl_singleton(klass)

        if is_singleton and (obj := self.__initialized_objects.get((klass, qualifier))):
            return obj

        self.__assert_dependency_exists(klass, qualifier)
        class_to_initialize = klass
        if self.__service_registry.is_interface_known(klass) and (
            concrete_class := self.__get_concrete_class_from_interface_and_qualifier(klass, qualifier)
        ):
            class_to_initialize = concrete_class

        if self.__service_registry.is_impl_known_from_factory(class_to_initialize):
            fn = self.__service_registry.factory_functions[class_to_initialize]
            instance = fn(**self.__callable_get_params_to_inject(fn))
        else:
            instance = class_to_initialize(**self.__callable_get_params_to_inject(klass.__init__, class_to_initialize))

        if is_singleton:
            self.__initialized_objects[class_to_initialize, qualifier] = instance

        return instance

    def __initialize_container_proxy_object_from_parameter(self, annotated_parameter: AnnotatedParameter) -> Any:
        if annotated_parameter.klass is None:
            return None

        annotated_type = annotated_parameter.klass

        if self.__service_registry.is_impl_known_from_factory(annotated_type):
            # Objects generated from factories do not have qualifiers
            return self.__get_proxy_object(annotated_type, None)

        qualifier_value = (
            annotated_parameter.annotation.qualifier
            if isinstance(annotated_parameter.annotation, ContainerProxyQualifier)
            else None
        )

        if self.__service_registry.is_interface_known(annotated_parameter.klass):
            concrete_class = self.__get_concrete_class_from_interface_and_qualifier(annotated_type, qualifier_value)
            return self.__get_proxy_object(concrete_class, qualifier_value)

        if self.__service_registry.is_impl_known(annotated_type):
            if not self.__service_registry.is_impl_with_qualifier_known(annotated_type, qualifier_value):
                msg = (
                    f"Cannot instantiate concrete class for {annotated_type} as qualifier '{qualifier_value}'"
                    f" is unknown. Available qualifiers: {self.__service_registry.known_impls[annotated_type]}"
                )
                raise ValueError(msg)
            return self.__get_proxy_object(annotated_type, qualifier_value)

        # Normally the container won't throw if it encounters a type it doesn't know about
        # But if it's explicitly marked as to be injected then we need to throw.
        if isinstance(annotated_parameter.annotation, ContainerInjectionRequest):
            self.__assert_dependency_exists(annotated_type, qualifier=None)

        # When injecting dependencies and a qualifier is used, throw if it's being used on an unknown type.
        # This prevents the default value from being used by the runtime.
        # We don't actually want that to happen as the value is used only for hinting the container
        # and all values should be supplied.
        if qualifier_value:
            msg = f"Cannot use qualifier {qualifier_value} on a type that is not managed by the container."
            raise ValueError(msg)

        return None

    def __get_proxy_object(self, klass: type[__T], qualifier: ContainerProxyQualifierValue) -> ContainerProxy:
        obj_id = klass, qualifier

        if self.__service_registry.is_impl_singleton(klass) and (obj := self.__initialized_proxies.get(obj_id)):
            return obj

        proxy = ContainerProxy(lambda: self.__get(klass, qualifier))
        self.__initialized_proxies[obj_id] = proxy

        return proxy

    def __get_concrete_class_from_interface_and_qualifier(
        self,
        klass: type[__T],
        qualifier: ContainerProxyQualifierValue,
    ) -> type[__T]:
        concrete_classes = self.__service_registry.known_interfaces.get(klass, {})

        if qualifier in concrete_classes:
            return concrete_classes[qualifier]

        # We have to raise here otherwise if we have a default hinting the qualifier for an unknown type
        # which will result in the value of the parameter being ContainerProxyQualifier.
        msg = (
            f"Cannot instantiate concrete class for {klass} as qualifier '{qualifier}' is unknown. "
            f"Available qualifiers: {set(concrete_classes.keys())}"
        )
        raise ValueError(msg)

    def __assert_dependency_exists(self, klass: type[__T], qualifier: ContainerProxyQualifierValue) -> None:
        """Assert that there exists an impl with that qualifier or an interface with an impl and the same qualifier."""
        if not self.__service_registry.is_type_with_qualifier_known(klass, qualifier):
            msg = f"Cannot wire unknown class {klass}. Use @Container.{{register,abstract}} to enable autowiring"
            raise ValueError(msg)
