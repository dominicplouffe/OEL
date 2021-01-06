# def cgrad():
#     list_of_colors = [(71, 170, 27), (212, 101, 18), (153, 24, 64)]

#     no_steps = 100

#     def LerpColour(c1, c2, t):
#         return (
#             c1[0] + (
#                 c2[0] - c1[0]
#             ) * t, c1[1] + (
#                 c2[1] - c1[1]
#             ) * t, c1[2] + (
#                 c2[2] - c1[2]
#             ) * t
#         )

#     c = 0
#     gradient = []
#     for i in range(len(list_of_colors)-1):
#         for j in range(no_steps):
#             colour = LerpColour(
#                 list_of_colors[i],
#                 list_of_colors[i + 1],
#                 j / no_steps
#             )

#             hexcolor = '#%s%s%s' % (
#                 hex(int(colour[0]))[2:],
#                 hex(int(colour[1]))[2:],
#                 hex(int(colour[2]))[2:]
#             )

#             if i % 2 == 0:
#                 gradient.append(hexcolor)
#             c += 1

#     return gradient


# GRADIENTS = cgrad()

GRADIENTS = [
    '#0f71b8',  # Blue
    '#6ab52f',  # Green
    '#ef7611',  # Orange
    '#e61723',  # Red
]


def get_gradient(value):
    if value < 1:
        value = value * 100

    if value <= 10:
        return GRADIENTS[0]
    elif value > 10 and value <= 50:
        return GRADIENTS[1]
    elif value > 50 and value <= 80:
        return GRADIENTS[2]

    return GRADIENTS[3]
