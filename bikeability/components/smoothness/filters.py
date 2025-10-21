def too_bumpy_to_ride(d: dict) -> bool:
    return d.get('smoothness') in ['very_bad', 'horrible', 'very_horrible', 'impassable']


def bad(d: dict) -> bool:
    return d.get('smoothness') == 'bad'


def intermediate(d: dict) -> bool:
    return d.get('smoothness') == 'intermediate'


def good(d: dict) -> bool:
    return d.get('smoothness') == 'good'


def excellent(d: dict) -> bool:
    return d.get('smoothness') == 'excellent'
