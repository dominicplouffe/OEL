from api.models import OrgUser
from random import shuffle

COLORS = [
    '#f44336',
    '#e91e63',
    '#9c27b0',
    '#9c27b0',
    '#4050b5',
    '#2196f3',
    '#01a9f4',
    '#00bcd4',
    '#009688',
    '#8bc24b',
    '#cddd39',
    '#ffeb3b',
    '#ffc008',
    '#ff9800',
    '#ff5722',
    '#795548',
    '#607d8b',
    '#fa29ff'
]


def pick_color(org):

    if OrgUser.objects.filter(org=org).count() == len(COLORS):
        return '#cccccc'

    while True:
        shuffle(COLORS)

        color = COLORS[0]

        try:
            OrgUser.objects.get(org=org, color=color)
        except OrgUser.DoesNotExist:
            return color

    return '#cccccc'
