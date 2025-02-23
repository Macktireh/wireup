import unittest
from typing import NewType

from typing_extensions import Annotated
from wireup import Inject, ServiceLifetime
from wireup.errors import (
    DuplicateServiceRegistrationError,
    FactoryReturnTypeIsEmptyError,
)
from wireup.ioc.service_registry import ServiceRegistry
from wireup.ioc.types import AnnotatedParameter, ParameterWrapper

from test.unit.services.no_annotations.random.random_service import RandomService


class TestServiceRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ServiceRegistry()

    def test_register_service(self):
        self.registry.register(MyService, qualifier="default", lifetime=ServiceLifetime.SINGLETON)

        # Check if the service is registered correctly
        self.assertTrue(self.registry.is_impl_known(MyService))
        self.assertTrue(self.registry.is_impl_with_qualifier_known(MyService, "default"))
        self.assertTrue(self.registry.is_type_with_qualifier_known(MyService, "default"))
        self.assertTrue(self.registry.is_impl_singleton(MyService))

        # Test registering a duplicate service
        with self.assertRaises(DuplicateServiceRegistrationError):
            self.registry.register(MyService, qualifier="default", lifetime=ServiceLifetime.SINGLETON)

    def test_register_abstract(self):
        self.registry.register_abstract(MyInterface)

        # Check if the interface is registered correctly
        self.assertTrue(self.registry.is_interface_known(MyInterface))

    def test_register_factory(self):
        self.registry.register(my_factory, lifetime=ServiceLifetime.SINGLETON)

        # Check if the factory function is registered correctly
        self.assertTrue(self.registry.is_impl_known_from_factory(RandomService, None))

        # Test registering a factory function with missing return type
        def invalid_factory():
            pass

        with self.assertRaises(FactoryReturnTypeIsEmptyError):
            self.registry.register(invalid_factory, lifetime=ServiceLifetime.SINGLETON)

        # Test registering a duplicate factory function
        with self.assertRaises(DuplicateServiceRegistrationError):
            self.registry.register(my_factory, lifetime=ServiceLifetime.SINGLETON)

    def test_is_impl_known(self):
        self.assertFalse(self.registry.is_impl_known(MyService))

        self.registry.register(MyService, qualifier="default", lifetime=ServiceLifetime.SINGLETON)
        self.assertTrue(self.registry.is_impl_known(MyService))

    def test_is_impl_with_qualifier_known(self):
        self.assertFalse(self.registry.is_impl_with_qualifier_known(MyService, "default"))

        self.registry.register(MyService, qualifier="default", lifetime=ServiceLifetime.SINGLETON)
        self.assertTrue(self.registry.is_impl_with_qualifier_known(MyService, "default"))

    def test_is_type_with_qualifier_known(self):
        self.assertFalse(self.registry.is_type_with_qualifier_known(MyService, "default"))

        self.registry.register(MyService, qualifier="default", lifetime=ServiceLifetime.SINGLETON)
        self.assertTrue(self.registry.is_type_with_qualifier_known(MyService, "default"))

    def test_is_impl_known_from_factory(self):
        self.assertFalse(self.registry.is_impl_known_from_factory(str, None))

        self.registry.register(my_factory, lifetime=ServiceLifetime.SINGLETON)
        self.assertTrue(self.registry.is_impl_known_from_factory(RandomService, None))

    def test_is_impl_singleton(self):
        self.assertFalse(self.registry.is_impl_singleton(MyService))

        self.registry.register(MyService, qualifier="default", lifetime=ServiceLifetime.SINGLETON)
        self.assertTrue(self.registry.is_impl_singleton(MyService))

    def test_is_interface_known(self):
        self.assertFalse(self.registry.is_interface_known(MyInterface))

        self.registry.register_abstract(MyInterface)
        self.assertTrue(self.registry.is_interface_known(MyInterface))

    def test_register_only_injectable_params(self):
        def target(_a, _b, _c, _d: RandomService, _e: str, _f: Annotated[str, Inject(param="name")]): ...

        self.registry.target_init_context(target)
        self.assertEqual(
            self.registry.context.dependencies[target],
            {
                "_d": AnnotatedParameter(klass=RandomService),
                "_f": AnnotatedParameter(klass=str, annotation=ParameterWrapper("name")),
            },
        )

    def test_registry_newtypes_class(self) -> None:
        class X:
            pass

        Y = NewType("Y", X)

        def y_factory() -> Y:
            return Y(X())

        self.registry.register(y_factory, lifetime=ServiceLifetime.SINGLETON)

        self.assertTrue(self.registry.is_impl_singleton(Y))

    def test_registry_newtypes_anything(self) -> None:
        Y = NewType("Y", str)

        def y_factory() -> Y:
            return Y("Hi")

        self.registry.register(y_factory, lifetime=ServiceLifetime.SINGLETON)

        self.assertTrue(self.registry.is_impl_singleton(Y))


class MyService:
    pass


class MyInterface:
    pass


def my_factory() -> RandomService:
    return RandomService()
