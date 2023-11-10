# Changes

## Version 0.2.0

Released 2023-11-08

- Allow users to set the `timeout` duration, which can enhance the reliability of `EventSource` by configuring
  it. ([#1](https://github.com/overcat/requests-sse/pull/1))
- Fix the issue where `on_message` is called when the message type is
  not `message`. ([#2](https://github.com/overcat/requests-sse/pull/2))

## Version 0.1.0

Released 2023-11-08

- Initial release.