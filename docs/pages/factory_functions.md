Typically getting the necessary dependencies is enough to construct an object. However, there are scenarios
where you need to delegate the creation of an object to a special function called a 
[factory](https://en.wikipedia.org/wiki/Factory_(object-oriented_programming)){: target=_blank }.

## Use cases

Some of the use cases for factories are as follows:

* Object construction needs additional logic or configuration.
* Depending on the runtime environment or configuration, you may need to create different objects 
inheriting from the same base (See: [Strategy Pattern](https://en.wikipedia.org/wiki/Strategy_pattern){: target=_blank }) or configure them differently. 
* Inject a model/dto which represents the result of an action, such as the current authenticated user.
* Inject a class from another library where it's not possible to add annotations.

## Usage

In order for the container to inject these dependencies you must register the factory function.
This can be achieved by using the `@container.register` decorator or by calling `container.register(fn)` directly.

When the container needs to inject a dependency it checks known factories to see if any of them can create it.


!!! info
    * The return type of the function is mandatory to annotate as tells the container what 
    type of dependency it can create.
    * Factories can only depend on objects known by the container!

!!! warning
    Modules which perform service registration need to be imported, otherwise `@container.register` calls
    may not be triggered. This can be an issue when the service does not reside in the same file as the
    factory. 

    E.g: A model residing in `app.model.user` and the factory being in `app.service.factory`.
    If `app.service.factory` is never imported the container won't know how to build the user model.

    Passing the module name to the `warmup_container(service_modules=[service])` 
    or the `wireup_init_*_integration` calls will import it recursively and bring it into scope.

    If you're not using either, `import_util.load_module` can be used once on startup in order to trigger registrations.

## Examples

### Inject a model

Assume in the context of a web application a class `User` exists and represents a user of the system.

```python
# Create a factory and inject the authenticated user directly.
# You may want to create a new type to make a disctinction on the type of user this is.
AuthenticatedUser = NewType("AuthenticatedUser", User)

@container.register(lifetime=ServiceLifetime.TRANSIENT)
def get_current_user(auth_service: AuthService) -> AuthenticatedUser:
    return AuthenticatedUser(auth_service.get_current_user())

# Now it is possible to inject the authenticated user directly wherever it is necessary.
@container.autowire
def get_user_logs(user: AuthenticatedUser):
    ...
```

### Implement strategy pattern

Assume a base class `Notifier` with implementations that define how the notification is sent (IMAP, POP, WebHooks, etc.)
Given a user it is possible to instantiate the correct type of notifier based on user preferences.


```python
@container.register(lifetime=ServiceLifetime.TRANSIENT)
def get_user_notifier(
    user: AuthenticatedUser, 
    slack_notifier: SlackNotifier, 
    email_mailer: EmailNotifier
) -> Notifier:
    notifier = ... # get notifier type from preferences.

    return notifier
```

When injecting `Notifier` the correct type will be created based on the authenticated user's preferences.

### Inject a third-party class

You can use factory functions to inject a class which you have not declared yourself. Let's take redis client as an
example.

=== "@ Annotations"

    ```python
    @container.register
    def redis_factory(redis_url: Annotated[str, Wire(param="redis_url")]) -> Redis:
        return redis.from_url(redis_url)
    ```

=== "🏭 Programmatic"

    ```python
    @container.register
    def redis_factory(settings: Settings) -> Redis:
        return redis.from_url(settings.redis_url)
    ```


## Links

* [Introduce to an existing project](introduce_to_an_existing_project.md)
