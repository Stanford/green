import re

def volume_base_name(volume_name: str) -> str:
    """
    """

    match = re.match(r'^(.*)\.(?:backup|readonly)$', volume_name)
    if (match):
        return match.group(1)

    return volume_name
