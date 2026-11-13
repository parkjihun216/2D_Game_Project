# LEC 14: 0번 레이어는 배경, 1번 레이어는 캐릭터입니다.
world = [[], []]


def add_object(obj, depth=0):
    world[depth].append(obj)


def update(delta_time):
    for layer in world:
        for obj in layer:
            obj.update(delta_time)


def render():
    for layer in world:
        for obj in layer:
            obj.draw()


def clear():
    for layer in world:
        layer.clear()
