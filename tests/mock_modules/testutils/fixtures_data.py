from types import SimpleNamespace


def get_summary(secure_arm=False, partition_ids=None,
                zone_ids=None, partition_status=None):
    if partition_status is None:
        partition_status = {}

    event = {
        'event': 'INFO',
        'info_type': 'SUMMARY',
        'partition_list': [
            {
                'partition_id': 0,
                'name': 'partition0',
                'status': partition_status.get(0, 'DISARM'),
                'secure_arm': secure_arm,
                'zone_list': [
                    {
                        'id': '001-0000',
                        'type': 'Door_Window',
                        'name': 'My Door',
                        'group': 'entryexitdelay',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 100,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 3,
                        'zone_type': 1,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0001',
                        'type': 'Door_Window',
                        'name': 'My Window',
                        'group': 'entryexitlongdelay',
                        'status': 'Open',
                        'state': '0',
                        'zone_id': 101,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 3,
                        'zone_type': 1,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0010',
                        'type': 'Motion',
                        'name': 'My Motion',
                        'group': 'awayinstantmotion',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 110,
                        'zone_physical_type': 2,
                        'zone_alarm_type': 3,
                        'zone_type': 2,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0011',
                        'type': 'Panel Motion',
                        'name': 'Panel Motion',
                        'group': 'safetymotion',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 111,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 3,
                        'zone_type': 119,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0020',
                        'type': 'GlassBreak',
                        'name': 'My Glass Break',
                        'group': 'glassbreakawayonly',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 120,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 0,
                        'zone_type': 116,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0021',
                        'type': 'Panel Glass Break',
                        'name': 'Panel Glass Break',
                        'group': 'glassbreakawayonly',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 121,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 0,
                        'zone_type': 116,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0030',
                        'type': 'Bluetooth',
                        'name': 'My Phone',
                        'group': 'mobileintrusion',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 130,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 1,
                        'zone_type': 115,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0040',
                        'type': 'SmokeDetector',
                        'name': 'My Smoke Detector',
                        'group': 'smoke_heat',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 140,
                        'zone_physical_type': 9,
                        'zone_alarm_type': 9,
                        'zone_type': 5,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0041',
                        'type': 'CODetector',
                        'name': 'My CO Detector',
                        'group': 'entryexitdelay',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 141,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 3,
                        'zone_type': 1,
                        'partition_id': 0,
                    },
                    {
                        'id': '001-0050',
                        'type': 'Water',
                        'name': 'My Water Detector',
                        'group': 'WaterSensor',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 150,
                        'zone_physical_type': 8,
                        'zone_alarm_type': 0,
                        'zone_type': 15,
                        'partition_id': 0,
                    },
                ],
            },
            {
                'partition_id': 1,
                'name': 'partition1',
                'status': partition_status.get(1, 'DISARM'),
                'secure_arm': secure_arm,
                'zone_list': [
                    {
                        'id': '002-0000',
                        'type': 'Door_Window',
                        'name': 'My 2nd Door',
                        'group': 'instantperimeter',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 200,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 3,
                        'zone_type': 1,
                        'partition_id': 1,
                    },
                    {
                        'id': '002-0010',
                        'type': 'Freeze',
                        'name': 'My Freeze Sensor',
                        'group': 'freeze',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 210,
                        'zone_physical_type': 6,
                        'zone_alarm_type': 0,
                        'zone_type': 17,
                        'partition_id': 1,
                    },
                    {
                        'id': '002-0020',
                        'type': 'Heat',
                        'name': 'My Heat Sensor',
                        'group': 'smoke_heat',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 220,
                        'zone_physical_type': 10,
                        'zone_alarm_type': 0,
                        'zone_type': 8,
                        'partition_id': 1,
                    },
                    {
                        'id': '002-0030',
                        'type': 'Tilt',
                        'name': 'My Tilt Sensor',
                        'group': 'garageTilt1',
                        'status': 'Closed',
                        'state': '0',
                        'zone_id': 230,
                        'zone_physical_type': 1,
                        'zone_alarm_type': 3,
                        'zone_type': 16,
                        'partition_id': 1,
                    },
                ],
            },
        ],
        'nonce': 'qolsys',
        'requestID': '<request_id>',
    }

    if partition_ids is not None:
        event['partition_list'] = [
            p for p in event['partition_list']
            if p['partition_id'] in partition_ids
        ]

    if zone_ids is not None:
        for i, partition in enumerate(event['partition_list']):
            partition['zone_list'] = [
                z for z in partition['zone_list']
                if z['zone_id'] in zone_ids
            ]

    # Prepare the entity ids so we can go over those easily
    entity_ids = [
        z['name'].lower().replace(' ', '_')
        for p in event['partition_list']
        for z in p['zone_list']
    ]

    topics = [
        'config',
        'availability',
        'state',
        'attributes',
    ]

    last_topic = (f'homeassistant/binary_sensor/'
                  f'{entity_ids[-1]}/{topics[-1]}')

    return SimpleNamespace(
        event=event,
        entity_ids=entity_ids,
        topics=topics,
        last_topic=last_topic,
    )
