Services refer to standalone classes that performs specific tasks or functions. 
Contrary to static utility classes or methods services handle dynamic and stateful operations.

Examples refer to the default container provided by the library in `wireup.container` but any other instance can be
used in its place. The process is meant to be simple and the short [Quickstart](quickstart.md) page shows by example and
already contains all the key concepts you need to know about.

## Registration
Declaration and usage of services is designed to be as simple as possible. They may live anywhere in the application
but must be registered with the container.

To register a class as a service the following options are available.

* Decorate the class using the `container.register`.
* Call `container.register(YourService)` directly on the service.
* Use `wireup.register_all_in_module`.
  (See: [Manual Configuration](manual_configuration.md#using-wireup-without-registration-decorators))

### Lifetime
By default, services will be registered as singletons. If your service or [Factory function](factory_functions.md)
needs to generate a fresh instance every time it is injected it needs to be registered with the `lifetime` parameter
set to `TRANSIENT`.

## Injection
The container will perform autowiring based on the type hints given. No manual configuration is needed to inject
services.

### Autowiring
To perform autowiring the method to be autowired must be decorated with `@container.autowire`. Given the nature of
Python decorators it is also possible to simply call it as a regular function which will return a callable with
arguments the containers knows about already bound.


