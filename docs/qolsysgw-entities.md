# Qolsys Gateway's entities

Qolsys Gateway creates a number of entities in Home Assistant and provides
attributes enabling to build automations around your Qolsys Panel with as
much of the information provided through the panel as possible.

> For the sake of simplicity, and because everyone's use of the information
> is different, some information are only provided as attributes on the
> entities instead of full-fledged sensors. Home Assistant however allows to
> easily build a sensor to track an attribute of another sensor; for instance,
> if you wish to have a sensor giving you the description of the last error
> raised by Qolsys Gateway, which is available as attribute `desc` on the
> sensor `qolsys_panel_last_error` (the `qolsys_panel` prefix being the
> default panel unique ID, which you might have changed in the `qolsysgw`
> configuration), you could use the following YAML code in your Home Assistant
> configuration:
>
> ```yaml
> template:
>   - sensor:
>       - name: qolsys_panel_last_error_desc
>         state: "{{state_attr('sensor.qolsys_panel_last_error', 'desc')}}"
> ```

This document aims at keeping track of the available entities and their
attributes.


## Qolsys State

A `sensor` entity will be provided for each instance of `qolsysgw`,
keeping track of the errors raised by the Gateway itself. The name
of the sensor will be in the format `{panel_unique_id}_last_error`
(default `qolsys_panel_last_error`) and will use the `timestamp`
device class, its value being the date of the last error raised by
the Gateway.

The following attributes are provided:

- `type`: the type of error raised by the Gateway
  (e.g. `UnknownQolsysSensorException`)
- `desc`: the description of the error raised by the Gateway
  (e.g. `Sensor type 'xxx' unsupported for sensor yyy`)

## Qolsys Partition

An `alarm_control_panel` entity will be provided for each partition found
in a panel.

The following attributes are provided:

- `secure_arm`: whether the partition has secure arming enabled, which
  means the panel would require to receive the user code when arming.
- `alarm_type`: one of `POLICE`, `FIRE`, `AUXILIARY` or (empty string)
  when an alarm is triggered on the partition. Set to `null` otherwise.
- `last_error_type`: the type of the last error received from the panel
  for that partition (e.g. `DISARM_FAILED`)
- `last_error_desc`: the description of the last error received from
  the panel for that partition (e.g. `Invalid usercode`)
- `last_error_at`: the timestamp of the last error received from the
  panel for that partition (particularly useful if you're tracking
  errors sent from the panel and want to identity two occurrences of
  the same error happening one after the other, since this value will
  be updated)
- `disarm_failed`: the number of failures to disarm the panel since
  it was last armed, or since `qolsysgw` was started

## Qolsys Sensor

A `binary_sensor` entity will be provided for each sensor found in a panel.
The device class of the sensor will depend on the sensor type as identified
by the panel.

The following attributes are provided:

- Attributes directly forwarded from the panel:
  - `group`: the group of the sensor
  - `state`: the state of the sensor
  - `zone_type`: the zone type of the sensor
  - `zone_physical_type`: the zone physical type
  - `zone_alarm_type`: the zone alarm type

- `tampered`: whether the sensor is currently tampered (note that this
  attribute will reset to `false` on a restart of the panel as the `SUMMARY`
  message of the panel does not provide sufficient information to know
  if a sensor is currently tampered)
