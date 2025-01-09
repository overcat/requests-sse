# Changes

## Version 0.5.0

Released 2025-01-09

- chore: change the log level. ([#21](https://github.com/overcat/requests-sse/pull/21))
- feat: allow users to set `latest_event_id` during initialization. ([#24](https://github.com/overcat/requests-sse/pull/24))

## Version 0.4.0

Released 2025-01-07

- fix: close session in `EventSource.close()` instead of `EventSource.__exit__()` ([#17](https://github.com/overcat/requests-sse/pull/17))
- chore: drop support for Python 3.7. You may still be able to use this library on Python 3.7, but we are not testing it and are no longer sure if it will work well.

## Version 0.3.2

Released 2024-05-06

- chore: fix whitespace sensitive content-type. ([#15](https://github.com/overcat/requests-sse/pull/15))

## Version 0.3.1

Released 2023-12-13

- chore: add support for Python 3.7. ([#12](https://github.com/overcat/requests-sse/pull/12))

## Version 0.3.0

Released 2023-11-12

- Fix the issue where the kwargs could be modified. ([#4](https://github.com/overcat/requests-sse/pull/4))
- Provide better error handling. ([#5](https://github.com/overcat/requests-sse/pull/5))
- Remove `option` param. ([#6](https://github.com/overcat/requests-sse/pull/6))

## Version 0.2.0

Released 2023-11-11

- Allow users to set the `timeout` duration, which can enhance the reliability of `EventSource` by configuring
  it. ([#1](https://github.com/overcat/requests-sse/pull/1))
- Fix the issue where `on_message` is called when the message type is
  not `message`. ([#2](https://github.com/overcat/requests-sse/pull/2))

## Version 0.1.0

Released 2023-11-08

- Initial release.
