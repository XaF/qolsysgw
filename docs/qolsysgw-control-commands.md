# Qolsys Gateway's control commands

Qolsys Gateway offers a number of control commands, which are then used as
actions toward the Qolsys Panel. All of the control commands share the common
parameters `partition_id` to indicate which partition the control is to be
acted for, and `session_token` which allows to make sure that we are receiving
that control command from the expected instance of Home Assistant.

These commands are listened for on the `control_topic`.


## DISARM

This control command is to ask Qolsys Gateway to disarm the given partition.
In cases where Qolsys Gateway is to verify the code (`code_disarm_required`
set to `true` and `ha_check_user_code` set to `false`), or if the
`panel_user_code` was not provided in the configuration, the `code` field
needs to be provided. It will either be used to check for the validity of
the code, or sent directly to the panel, which can then either disarm or
ignore the command, depending on the validity of the code.

```json
{
  "action": "DISARM",
  "code": "4242",
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## ARM_AWAY

This control command is to ask Qolsys Gateway to arm the partition in away mode
(i.e. all sensors are active and trigger the alarm if open).

In cases where the `panel_user_code` is not defined in the configuration, or
if `code_arm_required` was set to `true` and the code is not checked in
Home Assistant directly, that command must contain the `code` field so Qolsys
Gateway can check it. In other cases, that field is not necessary and will be
ignored.

The optional field `bypass` is a boolean indicating whether or not to bypass
currently open sensors; setting this value will override the panel default
configuration.

The optional field `delay` is the exit delay (in seconds) before the panel
will be armed after receiving the command; setting this value will override
the panel default configuration.

```json
{
  "action": "ARM_AWAY",
  "code": "4242",
  "bypass": false,
  "delay": 0,
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## ARM_VACATION

This is an alias of `ARM_AWAY`.

```json
{
  "action": "ARM_VACATION",
  "code": "4242",
  "bypass": false,
  "delay": 0,
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## ARM_HOME

This control command is to ask Qolsys Gateway to arm the partition in stay mode
(i.e. only door and window sensors are active and trigger the alarm).

In cases where the `panel_user_code` is not defined in the configuration, or
if `code_arm_required` was set to `true` and the code is not checked in
Home Assistant directly, that command must contain the `code` field so Qolsys
Gateway can check it. In other cases, that field is not necessary and will be
ignored.

The optional field `bypass` is a boolean indicating whether or not to bypass
currently open sensors; setting this value will override the panel default
configuration.

The optional field `delay` is the exit delay (in seconds) before the panel
will be armed after receiving the command; setting this value will override
the panel default configuration.

```json
{
  "action": "ARM_HOME",
  "code": "4242",
  "bypass": false,
  "delay": 0,
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## ARM_NIGHT

This is an alias of `ARM_HOME`.

```json
{
  "action": "ARM_NIGHT",
  "code": "4242",
  "bypass": false,
  "delay": 0,
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## ARM_CUSTOM_BYPASS

This control command is to ask Qolsys Gateway to arm the partition in away
(default) or stay mode, depending on the configuration. When using this
control to arm the partition, all open sensors will be bypassed, which means
that even after closing those sensors, subsequent open will not trigger the
alarm.

In cases where the `panel_user_code` is not defined in the configuration, or
if `code_arm_required` was set to `true` and the code is not checked in
Home Assistant directly, that command must contain the `code` field so Qolsys
Gateway can check it. In other cases, that field is not necessary and will be
ignored.

The optional field `delay` is the exit delay (in seconds) before the panel
will be armed after receiving the command; setting this value will override
the panel default configuration.

```json
{
  "action": "ARM_CUSTOM_BYPASS",
  "code": "4242",
  "delay": 0,
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## TRIGGER

This control command is to ask Qolsys Gateway to trigger the alarm for the
partition. In cases where `code_trigger_required` is set to `true` and the
code is not checked in Home Assistant directly, that command must contain
the `code` field so Qolsys Gateway can check it. In other cases, that field
is not necessary.

By default, this command will trigger the `POLICE` alarm.

```json
{
  "action": "TRIGGER",
  "code": "4242",
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## TRIGGER_POLICE

This is an alias of `TRIGGER`.

```json
{
  "action": "TRIGGER_POLICE",
  "code": "4242",
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## TRIGGER_FIRE

This is an alias of `TRIGGER`, but will trigger the `FIRE` alarm.

```json
{
  "action": "TRIGGER_FIRE",
  "code": "4242",
  "partition_id": 0,
  "session_token": "<session_token>"
}
```


## TRIGGER_AUXILIARY

This is an alias of `TRIGGER`, but will trigger the `AUXILIARY` (or medical) alarm.

```json
{
  "action": "TRIGGER_AUXILIARY",
  "code": "4242",
  "partition_id": 0,
  "session_token": "<session_token>"
}
```
