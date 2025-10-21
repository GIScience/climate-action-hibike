from enum import Enum


class SpeedLimitCategory(Enum):
    WALKING_SPEED = 15
    LOW = 30
    MEDIUM = 50
    HIGH = 100
    UNKNOWN = None


potential_bikeable_highway_values = (
    'primary',
    'primary_link',
    'secondary',
    'secondary_link',
    'tertiary',
    'tertiary_link',
    'road',
    'unclassified',
    'residential',
    'track',
    'living_street',
    'service',
)


def _shared_with_pedestrians(d: dict) -> bool:
    return (d.get('foot') in ['yes', 'designated'] and d.get('segregated') != 'yes') or (
        d.get('highway') in ['footway', 'pedestrian', 'path'] and d.get('foot') is None
    )


def designated_shared_with_pedestrians(d: dict) -> bool:
    return (d.get('highway') in ['cycleway', 'path', 'footway', 'pedestrian'] and _shared_with_pedestrians(d)) or d.get(
        'highway'
    ) == 'track'


def designated_exclusive(d: dict) -> bool:
    return d.get('highway') in ['cycleway', 'path', 'footway', 'pedestrian'] and not _shared_with_pedestrians(d)


def shared_with_motorised_traffic_walking_speed(d: dict, speed_limit: SpeedLimitCategory) -> bool:
    if speed_limit == SpeedLimitCategory.WALKING_SPEED:
        return True

    return d.get('highway') in ['living_street', 'service']


def shared_with_motorised_traffic_low_speed(d: dict, speed_limit: SpeedLimitCategory) -> bool:
    if speed_limit == SpeedLimitCategory.LOW:
        return True
    return d.get('zone:maxspeed') in ['DE:30', '30']


def shared_with_motorised_traffic_medium_speed(d: dict, speed_limit: SpeedLimitCategory) -> bool:
    if speed_limit == SpeedLimitCategory.MEDIUM:
        return True
    return (
        d.get('maxspeed:type') in ['DE:urban', 'AT:urban']
        or d.get('zone:maxspeed') in ['DE:urban', 'AT:urban']
        or d.get('highway') == 'residential'
    )


def shared_with_motorised_traffic_high_speed(d: dict, speed_limit: SpeedLimitCategory) -> bool:
    if speed_limit == SpeedLimitCategory.HIGH:
        return True
    return (
        d.get('maxspeed:type') in ['DE:rural', 'AT:rural'] or d.get('zone:maxspeed') in ['DE:rural', 'AT:rural']
    ) or d.get('highway') == 'unclassified'


def shared_with_motorised_traffic_unknown_speed(d: dict, speed_limit: SpeedLimitCategory) -> bool:
    if speed_limit == SpeedLimitCategory.UNKNOWN:
        return True
    return d.get('highway') in potential_bikeable_highway_values


def requires_dismounting(d: dict) -> bool:
    return (
        d.get('bicycle') == 'dismount'
        or '1012-32' in d.get('traffic_sign', 'no')
        or (
            d.get('highway') == 'steps'
            and (
                d.get('ramp:bicycle') == 'yes' or d.get('ramp') == 'yes' or d.get('ramp:wheelchair') == 'yes',
                d.get('ramp:stroller') == 'yes',
            )
        )
        or d.get('railway') == 'platform'
        or d.get('highway') == 'platform'
        or d.get('ford') is not None
    )


def pedestrian_exclusive(d: dict) -> bool:
    return (
        d.get('highway') in ['footway', 'pedestrian']
        and (
            d.get('bicycle')
            not in [
                'yes',
                'designated',
                'dismount',
            ]
            or d.get('bicycle:conditional') is not None
        )
        and (d.get('access') not in ['no', 'private', 'permit', 'military', 'delivery', 'customers', 'emergency'])
    )


###############or d.get('highway') == 'footway'
##############and (d.get('bicycle') not in ['yes', 'designated', 'permissive'])        #### this one shoul dbe added?


def restricted_access(d: dict) -> bool:
    return (
        d.get('access') in ['no', 'private', 'permit', 'military', 'delivery', 'customers', 'emergency']
        or d.get('motorroad') == 'yes'
        or d.get('bicycle') in ['no', 'private', 'use_sidepath', 'discouraged', 'destination']
        or d.get('highway')
        not in [
            *potential_bikeable_highway_values,
            'pedestrian',
            'path',
            'cycleway',
            'footway',
            'steps',
            'platform',
        ]
    )


def parse_maxspeed_tag(d: dict) -> SpeedLimitCategory:
    max_speed: str | None = d.get('maxspeed')
    max_speed = d.get('maxspeed:forward') if max_speed is None else max_speed
    max_speed = d.get('maxspeed:backward') if max_speed is None else max_speed
    max_speed = d.get('maxspeed:type') if max_speed is None else max_speed
    max_speed = d.get('zone:maxspeed') if max_speed is None else max_speed

    match max_speed:
        case None:
            return SpeedLimitCategory.UNKNOWN
        case 'walk':
            return SpeedLimitCategory.WALKING_SPEED
        case 'DE:urban' | 'AT:urban':
            return SpeedLimitCategory.MEDIUM
        case 'none' | 'DE:rural' | 'AT:rural':
            return SpeedLimitCategory.HIGH

    try:
        if max_speed.endswith('mph'):
            max_speed_list = max_speed.split('mph')
            if not len(max_speed_list) == 2:
                return SpeedLimitCategory.UNKNOWN
            max_speed_mph = int(max_speed_list[0])
            max_speed_kph = max_speed_mph * 1.609344
        else:
            max_speed_kph = int(max_speed)

        if max_speed_kph <= SpeedLimitCategory.WALKING_SPEED.value:
            return SpeedLimitCategory.WALKING_SPEED
        elif max_speed_kph <= SpeedLimitCategory.LOW.value:
            return SpeedLimitCategory.LOW
        elif max_speed_kph <= SpeedLimitCategory.MEDIUM.value:
            return SpeedLimitCategory.MEDIUM
        elif max_speed_kph > SpeedLimitCategory.MEDIUM.value:
            return SpeedLimitCategory.HIGH
        else:
            return SpeedLimitCategory.UNKNOWN
    except ValueError:
        return SpeedLimitCategory.UNKNOWN
