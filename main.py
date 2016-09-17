#! /usr/bin/python

try:
    import pygame_sdl2

    pygame_sdl2.import_as_pygame()
except ImportError:
    pass

import pygame
from pygame import *
from spritesheet import SpriteSheet
import random

WIN_WIDTH = 800
WIN_HEIGHT = 640
HALF_WIDTH = int(WIN_WIDTH / 2)
HALF_HEIGHT = int(WIN_HEIGHT / 2)

DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
DEPTH = 32
FLAGS = 0
CAMERA_SLACK = 30

TOP_OFFSET = 0


# This class handles sprite sheets
# This was taken from www.scriptefun.com/transcript-2-using
# sprite-sheets-and-drawing-the-background
# I've added some code to fail if the file wasn't found..
# Note: When calling images_at the rect is the format:
# (x, y, x + offset, y + offset)



def _get_floor(floor_number, dept):
    if (floor_number == 1):
        floor = "11111111111111111111111111111111111111111111"
    else:
        random.seed(floor_number)
        base = [" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                " ", " ", "1", "2", " ", "4", "1", " ", " ", "1", " ", " ", "5", "2", " ", " ", " ", " ", " ", " ", "1"]
        floor_array = random.sample(base, len(base))
        floor = "1"
        pos = 0
        for item in floor_array:
            if dept == 0:
                if str(item) == "4" or str(item) == "2":
                    bellow_floor = _get_floor((floor_number - 1), (dept + 1))
                    if (bellow_floor[pos + 1] == " " and str(item) == "4") \
                            or (bellow_floor[pos + 1] != " " and str(item) == "2"):
                        item = "1"

            floor += str(item)
            pos += 1
        floor += "1"

    return floor


def get_floor(floor_number):
    return _get_floor(floor_number, 0)


def calc_window(camera_top):
    return Window(int((camera_top / 32) + 20), int((camera_top / 32)))


def load_image(game_sprite_sheet, top_x, top_y):
    return game_sprite_sheet.image_at((top_x, top_y, 32, 32), colorkey=(90, 82, 104))


def main():
    global cameraX, cameraY
    global TOP_OFFSET
    CURRENT_TOP = 0
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("Use arrows to move!")
    timer = pygame.time.Clock()

    # Declare events
    ANIMATE_BLOCK_EVENT = pygame.USEREVENT + 1

    # Load sprite sheet
    global game_images
    global player_image
    global player_walk_1
    global player_walk_2
    global player_jump
    global platform_image
    global platform_image_alt
    global loose_platform_image
    global platform_trampoline
    global live_platform_images

    game_sprite_sheet = SpriteSheet('simples_pimples.png')
    player_base_x = 832

    # Load sprites
    player_jump = load_image(game_sprite_sheet, player_base_x, 32)

    player_walk_1 = load_image(game_sprite_sheet, player_base_x + 32 * 1, 32)
    player_walk_2 = load_image(game_sprite_sheet, player_base_x + 32 * 2, 32)
    player_image = player_walk_2
    platform_image_alt = load_image(game_sprite_sheet, 320, 928)
    platform_image = load_image(game_sprite_sheet, 352, 928)
    loose_platform_image = load_image(game_sprite_sheet, 448, 960)
    platform_trampoline = load_image(game_sprite_sheet, 0, 640)
    start_live = [512, 928]
    live_platform_images = []
    for i in range(0,4):
        live_platform_images.append( load_image(game_sprite_sheet, start_live[0], start_live[1] + (32 * i)))


    up = down = left = right = running = False
    bg = Surface((32, 32))
    bg.convert()
    bg.fill(Color("#000000"))
    entities = pygame.sprite.Group()
    player = Player(32, (32 * 15))
    platforms = []
    loose_platforms = []
    live_platforms = []
    x = y = 0
    entity_rows = []

    # Build the level
    # y = 0
    for map in range(0, 20):
        row = 20 - map

        floor = get_floor(row)
        # print(floor)
        entity_rows.append(int(row))
        for col in floor:
            if col == "1":
                p = Platform(x, y, row)
                platforms.append(p)
                entities.add(p)
            if col == "2":
                p = LooseBlock(x, y, row)
                platforms.append(p)
                loose_platforms.append(p)
                entities.add(p)
            if col == "3":
                p = FloatingBlock(x, y, row)
                platforms.append(p)
                loose_platforms.append(p)
                entities.add(p)
            if col == "4":
                p = PlatformTrampoline(x, y, row)
                platforms.append(p)
                entities.add(p)
            if col == "E":
                e = ExitBlock(x, y, row)
                platforms.append(e)
                entities.add(e)
            if col == "5":
                p = LiveBlock(x, y, row)
                platforms.append(p)
                live_platforms.append(p)
                entities.add(p)
            x += 32
        y += 32
        x = 0

    my_level = get_floor(1)
    total_level_width = len(my_level) * 32
    # total_level_width  = len(level[0])*32
    # total_level_height = len(level)*32
    total_level_height = 20 * 32
    camera = Camera(complex_camera, total_level_width, total_level_height)
    entities.add(player)
    LAST_TOP = 0
    LAST_MIN = 0
    lastItem = 0

    # Create a timed event to animate a sprite
    timed = pygame.time.set_timer(ANIMATE_BLOCK_EVENT, 60)

    last_window = Window(0, 0)
    myfont = pygame.font.SysFont("monospace", 15)
    WINY = 0
    while 1:
        timer.tick(60)
        toggle_animate = False

        for e in pygame.event.get():
            if e.type == QUIT: raise SystemExit("QUIT")
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                raise SystemExit("ESCAPE")
            if e.type == KEYDOWN and e.key == K_UP:
                up = True
            if e.type == KEYDOWN and e.key == K_DOWN:
                down = True
            if e.type == KEYDOWN and e.key == K_LEFT:
                left = True
            if e.type == KEYDOWN and e.key == K_RIGHT:
                right = True
            if e.type == KEYDOWN and e.key == K_SPACE:
                running = True

            if e.type == KEYUP and e.key == K_UP:
                up = False
            if e.type == KEYUP and e.key == K_DOWN:
                down = False
            if e.type == KEYUP and e.key == K_RIGHT:
                right = False
            if e.type == KEYUP and e.key == K_LEFT:
                left = False
            if e.type == ANIMATE_BLOCK_EVENT:
                # Animate block
                toggle_animate = True

        # draw background
        for y in range(32):
            for x in range(32):
                screen.blit(bg, (x * 32, y * 32))

        camera.update(player)
        # print("Window " + str((camera.state.top/32)+20) + " " + str((camera.state.top/32)))

        topRow = (camera.state.top / 32) + 20
        # View window changed
        reported_row = []
        windows_changed = False
        if int(topRow) != last_window.topRow:
            windows_changed = True
            newWindow = calc_window(camera.state.top)
            last_window.topRow = int((camera.state.top / 32) + 20)
            last_window.bottomRow = int((camera.state.top / 32))

            # print("Window " + str(last_window.topRow) + " " + str(last_window.bottomRow) )
            windowRows = range(last_window.bottomRow, last_window.topRow)
            missing_rows = []

            missing_rows = [obj for obj in range(last_window.bottomRow - 1, last_window.topRow + 1) if
                            obj not in entity_rows]
            # Create missing rows
            for row in missing_rows:
                x = 0
                entity_rows.append(int(row))
                floor = get_floor(int(row))
                # y = ((row-20) * 32) * -1
                y = ((20 - row) * 32)
                if row not in reported_row:
                    reported_row.append(row)
                    # print("Creating Row |" + str(int(row)) + "|")
                    # print( "|" + floor + "|")
                for col in floor:
                    if col == "1":
                        p = Platform(x, y, (int(row)))
                        platforms.append(p)
                        entities.add(p)
                    if col == "2":
                        p = LooseBlock(x, y, row)
                        platforms.append(p)
                        loose_platforms.append(p)
                        entities.add(p)
                    if col == "3":
                        p = FloatingBlock(x, y, row)
                        platforms.append(p)
                        loose_platforms.append(p)
                        entities.add(p)
                    if col == "4":
                        p = PlatformTrampoline(x, y, row)
                        platforms.append(p)
                        entities.add(p)
                    if col == "5":
                        p = LiveBlock(x, y, row)
                        platforms.append(p)
                        live_platforms.append(p)
                        entities.add(p)
                    if col == "E":
                        e = ExitBlock(x, y, int(row))
                        platforms.append(e)
                        entities.add(e)
                    x += 32
        # check if row not found
        # row = (camera.state.top/32)+20

        # update player, draw everything else
        player.update(up, down, left, right, running, platforms)
        # update loose platforms
        for lp in loose_platforms:
            lp.update(platforms)

        if toggle_animate :
            for lp in live_platforms:
                lp.animate()

        minRow = int(camera.state.top / 32)

        LAST_MIN = minRow
        entity_rows = []
        reported_row = []
        for e in entities:
            draw_this = True
            try:
                if windows_changed and e.row > 0 and (int(e.row) > int(last_window.topRow) or int(e.row) < minRow):
                    # if e.row not in reported_row:
                    #    print("Eat row " + str(e.row) + " " + str(minRow))
                    entities.remove(e)
                    platforms.remove(e)
                    try:
                        loose_platforms.remove(e)
                    except:
                        pass
                    try:
                        live_platforms.remove(e)
                    except:
                        pass
                    draw_this = False
            except AttributeError:
                draw_this = True
            if draw_this:
                try:
                    if e.row not in entity_rows:
                        entity_rows.append(e.row)
                except AttributeError:
                    pass
                screen.blit(e.image, camera.apply(e))

        pygame.display.update()


class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)


def simple_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    return Rect(-l + HALF_WIDTH, -t + HALF_HEIGHT, w, h)


def complex_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t, _, _ = -l + HALF_WIDTH, -t + HALF_HEIGHT, w, h

    l = min(0, l)  # stop scrolling at the left edge
    l = max(-(camera.width - WIN_WIDTH), l)  # stop scrolling at the right edge
    t = max(-(camera.height - WIN_HEIGHT), t)  # stop scrolling at the bottom
    # t = min(0, t)                           # stop scrolling at the top
    return Rect(l, t, w, h)


class Entity(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)


class Player(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        global game_images
        self.flip_pos = x
        self.look_right = True
        self.walk_status = True
        self.x_vel = 0
        self.y_vel = 0
        self.onGround = False
        # self.image = Surface((32,32))
        self.image = player_image
        # self.image.fill(Color("#0000FF"))
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)
        self.last_rect = Rect(self.rect)

    def refresh_image(self):
        tmp_image = self.image
        if self.rect.y == self.last_rect.y:
            if self.last_rect.x == self.rect.x:
                tmp_image = player_image
            elif self.flip_pos != self.rect.x and abs(abs(self.flip_pos) - abs(self.rect.x)) > 6:
                self.walk_status = not self.walk_status
                self.flip_pos = self.rect.x
                if self.walk_status:
                    tmp_image = player_walk_1
                else:
                    tmp_image = player_walk_2
        else:
            tmp_image = player_jump

        if not self.look_right and tmp_image != self.image:
            tmp_image = pygame.transform.flip(tmp_image, True, False)

        self.image = tmp_image
        # saves last y pos
        self.last_rect = Rect(self.rect)

    def update(self, up, down, left, right, running, platforms):
        if up:
            # only jump if on the ground
            if self.onGround: self.y_vel -= 10
            # self.y_vel -= .01
        if down:
            pass
        if running:
            self.x_vel = 10
        if left:
            self.x_vel = -4
            self.look_right = False
        if right:
            self.x_vel = 4
            self.look_right = True

        if not self.onGround:
            # only accelerate with gravity if in the air
            self.y_vel += 0.3
            self.onGround = False
            # max falling speed
            if self.y_vel > 50: self.y_vel = 50

        if not (left or right):
            self.x_vel = 0

        # increment in x direction
        self.rect.left += self.x_vel
        # do x-axis collisions
        self.collide(self.x_vel, 0, platforms)
        # increment in y direction
        self.rect.top += self.y_vel
        # assuming we're in the air
        self.onGround = False
        # do y-axis collisions
        self.collide(0, self.y_vel, platforms)
        self.refresh_image()

    def collide(self, x_vel, y_vel, platforms):
        global platform_image_alt
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, ExitBlock):
                    pygame.event.post(pygame.event.Event(QUIT))
                if x_vel > 0:
                    self.rect.right = p.rect.left
                    # print ( "collide right" )
                if x_vel < 0:
                    self.rect.left = p.rect.right
                    # print ( "collide left" )
                if y_vel > 0:
                    self.rect.bottom = p.rect.top
                    self.onGround = True
                    try:
                        p.step_over()
                    except:
                        pass
                    # if p.image == platform_image_alt:
                    self.y_vel = p.is_rubber()
                    # if p.is_rubber() != 0:
                    #    self.y_vel = -2
                    # else:
                    #    self.y_vel = 0
                if y_vel < 0:
                    try:
                        p.bellow_touch()
                    except:
                        pass
                    # p.image = platform_image_alt
                    self.rect.top = p.rect.bottom
                    self.y_vel = 0


class Window():
    def __init__(self, topRow, bottomRow):
        self.topRow = topRow
        self.bottomRow = bottomRow


class BaseEntity(Entity):
    def __init__(self, row):
        Entity.__init__(self)
        self.row = int(row)

    def is_rubber(self):
        return 0


class Platform(BaseEntity):
    def __init__(self, x, y, map_row):
        BaseEntity.__init__(self, map_row)
        global game_images
        # self.image = Surface((32, 32))
        self.image = self.default_image()
        self.image.convert()
        # self.image.fill(Color("#DDDDDD"))
        self.rect = Rect(x, y, 32, 32)

    def default_image(self):
        return platform_image

    def bellow_touch(self):
        self.image = platform_image_alt

    def step_over(self):
        pass

    def is_rubber(self):
        if self.image == platform_image_alt:
            return -2
        else:
            return 0

    def update(self):
        pass


class PlatformTrampoline(Platform):
    def __init__(self, x, y, map_row):
        Platform.__init__(self, x, y, map_row)
        self.image = platform_trampoline

    def default_image(self):
        return platform_trampoline

    def is_rubber(self):
        return -10

    def bellow_touch(self):
        pass


class LiveBlock(Platform):
    def __init__(self, x, y, map_row):
        Platform.__init__(self, x, y, map_row)
        self.image_iterator = iter(live_platform_images)
        self.image = next(self.image_iterator)

    def default_image(self):
        return live_platform_images[0]

    def animate(self):
        #toggle image
        try:
            self.image = next(self.image_iterator)
        except:
            self.image_iterator = iter(live_platform_images)
            self.image = next(self.image_iterator)

    def is_rubber(self):
        return 0

    def bellow_touch(self):
        pass


class LooseBlock(BaseEntity):
    def __init__(self, x, y, map_row):
        BaseEntity.__init__(self, map_row)
        self.x_vel = 0
        self.y_vel = 0
        self.onGround = True
        self.image = self.default_image()
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)

    def default_image(self):
        return loose_platform_image

    def refresh_image(self):
        pass

    def step_over(self):
        self.y_vel = 1

    def update(self, platforms):
        if self.y_vel == 0:
            return
        if not self.onGround:
            # only accelerate with gravity if in the air
            self.y_vel += 0.3
            # max falling speed
            if self.y_vel > 50: self.y_vel = 50

        # increment in y direction
        self.rect.top += self.y_vel
        # assuming we're in the air
        # self.onGround = False
        # do y-axis collisions
        self.collide(0, self.y_vel, platforms)
        self.refresh_image()

    def collide(self, x_vel, y_vel, platforms):
        # global platform_image_alt
        for p in platforms:
            # only check collition with other platforms
            if p != self and pygame.sprite.collide_rect(self, p):
                if y_vel > 0:
                    self.rect.bottom = p.rect.top
                    self.onGround = True
                    self.y_vel = 0
                if y_vel < 0:
                    # p.image = platform_image
                    self.rect.top = p.rect.bottom
                    self.y_vel = 0


class FloatingBlock(LooseBlock):
    def __init__(self, x, y, map_row):
        LooseBlock.__init__(self, x, y, map_row)

    def step_over(self):
        self.y_vel = -1


class ExitBlock(Platform):
    def __init__(self, x, y, map_row):
        Platform.__init__(self, x, y, map_row)
        self.image.fill(Color("#0033FF"))


if __name__ == "__main__":
    main()
