# The Qolsys Panel interactions

As of now, two types of interactions with the Qolsys IQ Panel 2+ seem possible:
- **actions**, which are commands that we are sending to the panel to expect
  a reaction, and
- **events** which are information that the panel share with us

There is also an `ACK` response that is given by the panel in reponse to
anything being sent to it, to indicate that it properly received the request;
note that receiving an `ACK` response does not mean that the panel will do
anything with what we sent, nor that the command was valid.

This document cannot be expected to be an exhaustive review of the Qolsys
Panel's Control4 interface. However, it contains all of the information
that is currently available to me. If you know of other command types,
other actions, other events, or even other parameters as part of the
actions and events, please make a pull request.



## Actions

All actions seem to be sharing a common part of their payload, and specific
other values. Every action type (e.g. `INFO`) seem to have a field to
indicate a subtype of that action (e.g. `info_type`).

All actions require a `token` to work, which is provided from the Qolsys
Panel.


### INFO

The `INFO` action type is principally used to query for the summary of the
state of the panel at the current time, which includes information about all
the partitions and sensors. An `INFO` action will generally be followed by
an `INFO` event as response from the panel.

```json
{
  "action": "INFO",
  "info_type": "SUMMARY",
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```

### ARMING

The `ARMING` action type allows to handle everything about arming and
disarming the Qolsys Panel. The `arming_type` field will be used to
indicate if we want to arm or disarm the panel, and in the former case,
if we want to arm in the stay or away modes.

This action requires to provide a `partition_id`, which is the ID of
the partition on which we want to act.


#### ARM_STAY

There is no extra parameter when using `ARM_STAY` as `arming_type`.

```json
{
  "action": "ARMING",
  "arming_type": "ARM_STAY",
  "partition_id": 0,
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```


#### ARM_AWAY

When using `ARM_AWAY` as `arming_type`, we can use the `delay` parameter
to specify how long to leave as exit delay, between the moment the panel
enters the arming mode, and the moment the panel is fully armed. If that
parameter is not provided, it will simply use the default value configured
in the panel. If the `delay` is set to `0`, the panel will immediately
be armed, without an arming period.

```json
{
  "action": "ARMING",
  "arming_type": "ARM_AWAY",
  "partition_id": 0,
  "delay": 10,
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```


#### DISARM

When using `DISARM` as `arming_type`, the extra parameter `usercode`
is required, and must contain a valid disarm code for the panel.

```json
{
  "action": "ARMING",
  "arming_type": "DISARM",
  "partition_id": 0,
  "usercode": "4242",
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```


### TRIGGER

The `ALARM` action type allows to trigger the alarm of the panel.
The `alarm_type` field will be used to indicate which type of alarm is
being triggered.

This action requires to provide a `partition_id`, which is the ID of
the partition on which we want to act.


#### POLICE

There is no extra parameter when using `POLICE` as `alarm_type`.
This alarm type is for a police emergency.

```json
{
  "action": "ALARM",
  "alarm_type": "POLICE",
  "partition_id": 0,
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```


#### FIRE

There is no extra parameter when using `FIRE` as `alarm_type`.
This alarm type is for a fire, CO or smoke emergency.

```json
{
  "action": "ALARM",
  "alarm_type": "FIRE",
  "partition_id": 0,
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```


#### AUXILIARY

There is no extra parameter when using `AUXILIARY` as `alarm_type`.
This alarm type is for a medical emergency.

```json
{
  "action": "ALARM",
  "alarm_type": "AUXILIARY",
  "partition_id": 0,
  "token": "<token>",
  "nonce": "qolsys",
  "source": "C4",
  "version": 0
}
```


## Events

Events represent what is happening in the panel or the linked sensors, either
through our control (we sent an action to request that event) or outside of
our control.

The common field to all events is the `request_id`, which represents a
UUID-formatted identifiant of the request.


### INFO

The `INFO` event type gives information about the state of the system, either
following an `INFO` action type (requesting the alarm system to provide the
information) or simply because of a change in state of the system (e.g. someone
manually changing a parameter in the alarm system).

#### SUMMARY

```json
{
  "event": "INFO",
  "info_type": "SUMMARY",
  "partition_list": [
    {
      "partition_id": 0,
      "name": "partition1",
      "status": "DISARM",
      "secure_arm": false,
      "zone_list": [
        {
          "id": "xxx-yyyy",
          "type": "Door_Window",
          "name": "Door NNN",
          "group": "entryexitdelay",
          "status": "Closed",
          "state": "0",
          "zone_id": 42,
          "zone_physical_type": 1,
          "zone_alarm_type": 3,
          "zone_type": 1,
          "partition_id": 0
        },
        ...
      ]
    }
  ],
  "nonce": "qolsys",
  "requestID": "<request_id>"
}
```

The `status` field contains the current status of the alarm, which are:
- `DISARM` when the alarm is disarmed
- `ARM_STAY` when the alarm is armed in stay mode (no motion sensors, just the door and window sensors)
- `ARM_AWAY` when the alarm is armed in away mode
- `ENTRY_DELAY` when the alarm is pending to be triggered, but we have time to disarm with the code
- `ALARM` when the alarm is triggered
- `EXIT_DELAY` when the alarm is arming, giving time to leave the place before being armed (also `ARM-AWAY-EXIT-DELAY` on some panels, it seems)

The `zone_list` field contains a list of sensors, for which the possible `type` values are:
- `Door_Window` for door/window sensors
- `Motion` for motion sensors
- `Panel Motion` for the motion sensor using the panel's camera
- `Glass Break` for the glass break detection
- `Panel Glass Break` for the glass break detection through the panel's microphone
- `Bluetooth` for the bluetooth devices linked to the panel
- `Smoke Detector` for the smoke detectors
- `CO Detector` for the CO detectors
- `Water` for the water leaks detectors

#### SECURE_ARM

```json
{
  "event": "INFO",
  "info_type": "SECURE_ARM",
  "partition_id": 0,
  "value": true,
  "version": 1,
  "requestID": "<request_id>"
}
```

The `value` can be `true` or `false`, depending if Secure Arm has respectively been
enabled or disabled. When Secure Arm is enabled, the alarm system requires a valid
code to arm the alarm system.


### ZONE_EVENT

The `ZONE_EVENT` event type has two subtypes. Both will provide a `version`
field as well as a `zone` field, the latter containing an object with updated
information on a sensor. The `zone_event_type` field will indicate the type of
`ZONE_EVENT` that happened.


#### ZONE_ACTIVE

This event happens when a sensor changes state (e.g. a door has been opened
or closed), and gives us information about the zone (i.e. sensor) and its
new status (open vs. closed).

```json
{
  "event": "ZONE_EVENT",
  "zone_event_type": "ZONE_ACTIVE",
  "version": 1,
  "zone": {
    "status": "Open",
    "zone_id": 42
  },
  "requestID": "<request_id>"
}
```


#### ZONE_UPDATE

This event happens when a sensor was altered and is back in service, but also
seem to happen regularly as to inform that the sensors are still in a given
state, if they have not had any event in a while.


```json
{
  "event": "ZONE_EVENT",
  "zone_event_type": "ZONE_UPDATE",
  "zone": {
    "id": "xxx-yyyy",
    "type": "Motion",
    "name": "Motion MMM",
    "group": "awayinstantmotion",
    "status": "Closed",
    "state": "0",
    "zone_id": 1337,
    "zone_physical_type": 2,
    "zone_alarm_type": 3,
    "zone_type": 2,
    "partition_id": 0
  },
  "version": 1,
  "requestID": "<request_id>"
}
```


#### ZONE_ADD

This event happens when a sensor is added.

```json
{
  "event": "ZONE_EVENT",
  "zone_event_type":" ZONE_ADD",
  "zone": {
    "id":" xxx-yyyy",
    "type": "Door_Window",
    "name": "Door NNN",
    "group": "entryexitdelay",
    "status": "Closed",
    "state": "0",
    "zone_id": 5,
    "zone_physical_type": 1,
    "zone_alarm_type": 3,
    "zone_type": 1,
    "partition_id": 0
  },
  "version": 1,
  "requestID": "<request_id>"
}
```


### ARMING

The `ARMING` event type happens when a change occurs in arming state
for one of the partitions of the panel.

```json
{
  "event": "ARMING",
  "arming_type": "DISARM",
  "partition_id": 0,
  "version": 1,
  "requestID": "<request_id>"
}
```

The `arming_type` correspond to the different valid `status` mentionned
above when talking about [the `INFO` event](#info), except for the `ALARM`
status, which is not an `ARMING` state and thus wouldn't appear here.


### ALARM

The `ALARM` event type happens when an alarm is triggered on the panel.

```json
{
  "event": "ALARM",
  "alarm_type": "",
  "partition_id": 0,
  "version": 1,
  "requestID": "<request_id>"
}
```

The `alarm_type` can be one of `POLICE`, `FIRE` or `AUXILIARY`. It can also be
empty, which is the case when the alarm is triggered by a sensor being `Open`
while the alarm is armed.


### ERROR

The `ERROR` event type happens when an error happens following a command
sent to the panel through the Control4 interface. This means that any
operation done directly on the panel (like typing a disarm code physically)
will not lead to any of those messages.

```json
{
  "event": "ERROR",
  "partition_id": 0,
  "error_type": "DISARM_FAILED",
  "description": "Invalid usercode",
  "version": 1,
  "requestID": "<request_id>"
}
```

The `error_type` corresponds to the type of the error. At the moment, we have
only observed the following ones:
- `usercode` which happened when trying to arm/disarm the alarm while the
  keypad was locked (using partitions), or if the 6-digit usercodes are not
  enabled on a panel version that requires it
- `DISARM_FAILED` which happened when trying to arm/disarm the alarm with
  an invalid usercode

The `description` gives a human-readable version of the `error_type`, which
contains a bit more information than the `error_type` itself.
