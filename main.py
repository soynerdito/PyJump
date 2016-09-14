#! /usr/bin/python

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


def get_floor(floor_number):
    if (floor_number == 1):
        floor = "11111111111111111111111111111111111111111111"
    else:
        random.seed(floor_number)
        base = [" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                " ", " ", "1", "1", " ", " ", "1", " ", " ", "1", " ", " ", "1", "1", " ", " ", " ", " ", " ", " ", "1"]
        floor_array = random.sample(base, len(base))
        floor = "1"
        for item in floor_array:
            floor += str(item)
        floor += "1"

    return floor


def calc_window(camera_top):
    return Window(int((camera_top / 32) + 20), int((camera_top / 32)))

def load_image( game_sprite_sheet, top_x, top_y ):
    return game_sprite_sheet.image_at((top_x, top_y, 32, 32), colorkey=(90, 82, 104))

def main():
    global cameraX, cameraY
    global TOP_OFFSET
    CURRENT_TOP = 0
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("Use arrows to move!")
    timer = pygame.time.Clock()

    # Load sprite sheet
    global game_images
    global player_image
    global player_walk_1
    global player_walk_2
    global player_jump
    global platform_image
    global platform_image_alt

    game_sprite_sheet = SpriteSheet('simples_pimples.png')
    player_base_x = 832

    # Load sprites
    player_jump = load_image(game_sprite_sheet, player_base_x, 32 )

    player_walk_1 = load_image(game_sprite_sheet, player_base_x + 32 * 1, 32 )
    player_walk_2 = load_image(game_sprite_sheet, player_base_x + 32 * 2, 32 )
    player_image = player_walk_2
    platform_image_alt = load_image(game_sprite_sheet, 320, 928 )
    platform_image = load_image(game_sprite_sheet, 352, 928 )

    up = down = left = right = running = False
    bg = Surface((32, 32))
    bg.convert()
    bg.fill(Color("#000000"))
    entities = pygame.sprite.Group()
    player = Player(32, (32 * 15))
    platforms = []

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
            if col == "E":
                e = ExitBlock(x, y, row)
                platforms.append(e)
                entities.add(e)
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

    last_window = Window(0, 0)
    myfont = pygame.font.SysFont("monospace", 15)
    WINY = 0
    while 1:
        timer.tick(60)

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

                    if col == "E":
                        e = ExitBlock(x, y, int(row))
                        platforms.append(e)
                        entities.add(e)
                    x += 32
        # check if row not found
        # row = (camera.state.top/32)+20

        # update player, draw everything else
        player.update(up, down, left, right, running, platforms)
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
                    if p.image == platform_image_alt:
                        self.y_vel = -2
                    else:
                        self.y_vel = 0
                if y_vel < 0:
                    p.image = platform_image_alt
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


class Platform(BaseEntity):
    def __init__(self, x, y, map_row):
        BaseEntity.__init__(self, map_row)
        global game_images
        # self.image = Surface((32, 32))
        self.image = platform_image
        self.image.convert()
        # self.image.fill(Color("#DDDDDD"))
        self.rect = Rect(x, y, 32, 32)

    def update(self):
        pass


class ExitBlock(Platform):
    def __init__(self, x, y, map_row):
        Platform.__init__(self, x, y, map_row)
        self.image.fill(Color("#0033FF"))


if __name__ == "__main__":
    main()
