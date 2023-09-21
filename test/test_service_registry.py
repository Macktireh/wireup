import unittest

from test.services.random_service import RandomService
from wireup.ioc.service_registry import ServiceRegistry


class TestServiceRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ServiceRegistry()

    def test_register_service(self):
        self.registry.register_service(MyService, qualifier="default", singleton=True)

        # Check if the service is registered correctly
        self.assertTrue(self.registry.is_impl_known(MyService))
        self.assertTrue(self.registry.is_impl_with_qualifier_known(MyService, "default"))
        self.assertTrue(self.registry.is_type_with_qualifier_known(MyService, "default"))
        self.assertTrue(self.registry.is_impl_singleton(MyService))

        # Test registering a duplicate service
        with self.assertRaises(ValueError):
            self.registry.register_service(MyService, qualifier="default", singleton=True)

    def test_register_abstract(self):
        self.registry.register_abstract(MyInterface)

        # Check if the interface is registered correctly
        self.assertTrue(self.registry.is_interface_known(MyInterface))

    def test_register_factory(self):
        self.registry.register_factory(my_factory, singleton=True)

        # Check if the factory function is registered correctly
        self.assertTrue(self.registry.is_impl_known_from_factory(RandomService))

        # Test registering a factory function with missing return type
        def invalid_factory():
            pass

        with self.assertRaises(ValueError):
            self.registry.register_factory(invalid_factory, singleton=True)

        # Test registering a duplicate factory function
        with self.assertRaises(ValueError):
            self.registry.register_factory(my_factory, singleton=True)

    def test_register_targets_meta(self):
        self.registry.register_factory(my_factory, singleton=True)

        # Check if the target metadata is registered correctly
        self.assertTrue(my_factory in self.registry.targets_meta)

    def test_is_impl_known(self):
        self.assertFalse(self.registry.is_impl_known(MyService))

        self.registry.register_service(MyService, qualifier="default", singleton=True)
        self.assertTrue(self.registry.is_impl_known(MyService))

    def test_is_impl_with_qualifier_known(self):
        self.assertFalse(self.registry.is_impl_with_qualifier_known(MyService, "default"))

        self.registry.register_service(MyService, qualifier="default", singleton=True)
        self.assertTrue(self.registry.is_impl_with_qualifier_known(MyService, "default"))

    def test_is_type_with_qualifier_known(self):
        self.assertFalse(self.registry.is_type_with_qualifier_known(MyService, "default"))

        self.registry.register_service(MyService, qualifier="default", singleton=True)
        self.assertTrue(self.registry.is_type_with_qualifier_known(MyService, "default"))

    def test_is_impl_known_from_factory(self):
        self.assertFalse(self.registry.is_impl_known_from_factory(str))

        self.registry.register_factory(my_factory, singleton=True)
        self.assertTrue(self.registry.is_impl_known_from_factory(RandomService))

    def test_is_impl_singleton(self):
        self.assertFalse(self.registry.is_impl_singleton(MyService))

        self.registry.register_service(MyService, qualifier="default", singleton=True)
        self.assertTrue(self.registry.is_impl_singleton(MyService))

    def test_is_interface_known(self):
        self.assertFalse(self.registry.is_interface_known(MyInterface))

        self.registry.register_abstract(MyInterface)
        self.assertTrue(self.registry.is_interface_known(MyInterface))


class MyService:
    pass


class MyInterface:
    pass


def my_factory() -> RandomService:
    return RandomService()
