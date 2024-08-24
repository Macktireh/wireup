---
hide:
    - navigation
---

Performant, concise, and easy-to-use dependency injection container for Python 3.8+.

[![GitHub](https://img.shields.io/github/license/maldoinc/wireup)](https://github.com/maldoinc/wireup)
[![Code Climate maintainability](https://img.shields.io/codeclimate/maintainability/maldoinc/wireup?label=Code+Climate)](https://codeclimate.com/github/maldoinc/wireup)
[![Coverage](https://img.shields.io/codeclimate/coverage/maldoinc/wireup?label=Coverage)](https://codeclimate.com/github/maldoinc/wireup)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wireup)](https://pypi.org/project/wireup/)
[![PyPI - Version](https://img.shields.io/pypi/v/wireup)](https://pypi.org/project/wireup/)


## Key features


<div class="grid cards" markdown>

-   :arrow_heading_down:{ .lg .middle } __Dependency Injection__

    ---

    Inject services and configuration using a clean and intuitive syntax.

    [:octicons-arrow-right-24:Getting Started](getting_started.md)

-   :gear:{ .lg .middle } __Autoconfiguration__

    ---
    Automatically inject dependencies based on their types without additional configuration for the
    most common use cases.

    [:octicons-arrow-right-24: Learn more](annotations.md)

-   :scroll:{ .lg .middle } __Interfaces / Abstract classes__

    ---

    Define abstract types and have the container automatically inject the implementation.

    [:octicons-arrow-right-24: Learn more](interfaces.md)


-   :factory:{ .lg .middle } __Factory pattern__

    ---

    Defer instantiation to specialized factories for full control over object creation when necessary.

    [:octicons-arrow-right-24: Learn more](factory_functions.md)


-   :one:{ .lg .middle } __Singletons/Transient dependencies__

    ---

    Declare dependencies as transient or singletons which tells the container whether to inject a fresh copy or reuse existing instances.

    [:octicons-arrow-right-24: Learn more](services.md)


-   :package:{ .lg .middle } __Declarative/Imperative__

    ---
    Configure services through annotations in a fully declarative style or
    build everything by code for full control over instantiation.

    [:octicons-arrow-right-24: Learn more](configuration.md)
</div>


## Framework integrations

Simplified use with the following frameworks.

- [x] [Django](integrations/django.md)
- [x] [FastAPI](integrations/fastapi.md)
- [x] [Flask](integrations/flask.md)

## License

This project is licensed under the terms of the
[MIT](https://github.com/maldoinc/wireup/blob/master/license.md){: target=_blank } license.
