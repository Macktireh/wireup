Services are classes in the application that provide functionality that the container knows about and is able to build.
They can depend on other services or [parameters](parameters.md).

The examples refer to the default container provided by the library in `wireup.container` but any other instance can be
used in its place. The process is meant to be simple and the short [Quickstart](quickstart.md) page shows by example and
already contains all the key concepts you need to know about.

## Registration

Declaration and usage of services is designed to be as simple as possible. They may live anywhere in the application
but must be registered with the container.

To register a class as a service the following options are available.

* Decorate the class using the `container.register`.
* Call `container.register(YourService)` directly on the service.
* Use `container.register_all_in_module`.
  (See: [Manual Configuration](manual_configuration.md#using-wireup-without-registration-decorators))

## Injection

The container will perform autowiring based on the type hints given. No manual configuration is needed to inject
services.

To perform autowiring the method to be autowired must be decorated with `@container.autowire`. Given the nature of
Python decorators it is also possible to simply call it as a regular function which will return a callable with
arguments the containers knows about already bound.
