#! /usr/bin/python

try:
    import pygame_sdl2

    pygame_sdl2.import_as_pygame()
except ImportError:
    pass
import pygame
import random
from random import randint
from pygame import *
from threading import Timer
from game_lib import Scene
from spritesheet import SpriteSheet
from collections import deque

WIN_WIDTH = 800
WIN_HEIGHT = 640
HALF_WIDTH = int(WIN_WIDTH / 2)
HALF_HEIGHT = int(WIN_HEIGHT / 2)

DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
DEPTH = 32
FLAGS = 0
CAMERA_SLACK = 30

# This class handles sprite sheets
# This was taken from www.scriptefun.com/transcript-2-using
# sprite-sheets-and-drawing-the-background
# I've added some code to fail if the file wasn't found..
# Note: When calling images_at the rect is the format:
# (x, y, x + offset, y + offset)

img_sprites = 'img/simples_pimples2.png'


class ScoreBoard:
    def __init__(self, ):
        # self.screen = screen
        self.score = 0
        self.highest = 0
        self.font = pygame.font.Font("freesansbold.ttf", 25)

    def render(self, screen):
        text = self.font.render("Score: " + str(self.score), True, (255, 255, 255))
        screen.blit(text, (0, 0))
        text = self.font.render("Highest Score: " + str(self.highest), True, (255, 255, 255))
        screen.blit(text, (0, 30))

    def set_score(self, score):
        self.score = int(score)
        if int(score) > self.highest:
            self.highest = int(score)

    def set_score_smart(self, score):
        if int(score) > self.score:
            self.score = int(score)


def _get_floor(floor_number, dept):
    if floor_number == 1:
        floor = '11111111111111111111111111111111111111111111'
    else:
        random.seed(floor_number)
        base = [" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                " ", " ", "1", "1", " ", "4", "1", " ", " ", "1", " ", " ", "5", "1", " ", " ", " ", " ", " ", " ", "1"]
        # " ", " ", "1", "2", " ", "4", "1", " ", " ", "1", " ", " ", "5", "2", " ", " ", " ", " ", " ", " ", "1"]
        floor_array = random.sample(base, len(base))
        floor = "1"
        pos = 0
        for item in floor_array:
            if dept == 0:
                if str(item) == "4" or str(item) == "2":
                    # check floor above
                    try:
                        over_floor = _get_floor((floor_number + 1), (dept + 1))
                        if over_floor[pos + 1] != " " and (str(item) == "4" \
                                                                   or str(item) == "2"):
                            item = "1"
                    except:
                        pass

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


class GameScene(Scene):
    def __init__(self):
        Scene.__init__(self)
        # initialize scoreboard
        self.toggle_animate = True
        self.scoreboard = ScoreBoard()

        # Declare events
        self.ANIMATE_BLOCK_EVENT = pygame.USEREVENT + 1

        # Load sprite sheet
        self.game_sprite_sheet = SpriteSheet(img_sprites)
        self.player_base_x = 832

        # Load sprites
        self.platform_image_alt = load_image(self.game_sprite_sheet, 672, 928)
        self.platform_image = load_image(self.game_sprite_sheet, 352, 928)
        # create platform images
        self.platform_images = [load_image(self.game_sprite_sheet, 352, 928),
                                load_image(self.game_sprite_sheet, 352, 928 + 32),
                                load_image(self.game_sprite_sheet, 352, 928 + 32 * 2),
                                load_image(self.game_sprite_sheet, 352, 928 + 32 * 3)]

        # create alternate platform images
        self.platform_images_alt = [load_image(self.game_sprite_sheet, 672, 928),
                                    load_image(self.game_sprite_sheet, 672, 928 + 32),
                                    load_image(self.game_sprite_sheet, 672, 928 + 32 * 2),
                                    load_image(self.game_sprite_sheet, 672, 928 + 32 * 3)]

        self.loose_platform_image = load_image(self.game_sprite_sheet, 448, 960)
        self.platform_trampoline = load_image(self.game_sprite_sheet, 0, 640)
        self.platform_trampoline_alt = load_image(self.game_sprite_sheet, 0, 672)
        self.platform_image_broke_1 = load_image(self.game_sprite_sheet, 704, 928)
        self.platform_image_broke_2 = load_image(self.game_sprite_sheet, 736, 928)

        self.start_live = [512, 928]
        self.live_platform_images = []
        for i in range(0, 4):
            self.live_platform_images.append(
                load_image(self.game_sprite_sheet, self.start_live[0], self.start_live[1] + (32 * i)))

        self.bg = Surface((32, 32))
        self.bg.convert()
        self.bg.fill(Color("#000000"))
        self.entities = pygame.sprite.Group()
        # player = Player(32, (32 * 15), player_image, [player_walk_1, player_walk_2], player_jump)
        self.player = Player(32, (32 * 15), self.game_sprite_sheet, self.player_base_x, 32)
        self.ghost = Ghost(32, (32 * 15), self.game_sprite_sheet, self.player_base_x, 32 * 6)
        self.platforms = []
        self.loose_platforms = []
        self.live_platforms = []
        self.entity_rows = []

        self.my_level = get_floor(1)
        self.total_level_width = len(self.my_level) * 32
        self.total_level_height = 20 * 32
        self.camera = Camera(complex_camera, self.total_level_width, self.total_level_height)
        self.entities.add(self.player)
        self.entities.add(self.ghost)

        # Create a timed event to animate a sprite
        pygame.time.set_timer(self.ANIMATE_BLOCK_EVENT, 60)

        self.last_window = Window(0, 0)

    def render(self, screen):
        # draw background
        for y in range(32):
            for x in range(32):
                screen.blit(self.bg, (x * 32, y * 32))

        min_row = int(self.camera.state.top / 32)
        entity_rows = []

        top_row = (self.camera.state.top / 32) + 20
        # View window changed
        windows_changed = False
        if int(top_row) != self.last_window.top_row:
            windows_changed = True

        for e in self.entities:
            draw_this = True
            try:
                if self.windows_changed and e.row > 0 and (
                                int(e.row) > int(self.last_window.top_row) or int(e.row) < min_row):


                    try:
                        if not isinstance(e, Ghost):
                            self.entities.remove(e)
                            self.platforms.remove(e)
                            self.loose_platforms.remove(e)
                    except:
                        pass
                    try:
                        self.live_platforms.remove(e)
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
                screen.blit(e.image, self.camera.apply(e))
        self.scoreboard.render(screen)

    def update(self):
        self.camera.update(self.player)

        # Update scoreboard
        self.scoreboard.set_score((self.camera.state.top / 32))

        top_row = (self.camera.state.top / 32) + 20
        # View window changed
        reported_row = []
        windows_changed = False
        if int(top_row) != self.last_window.top_row:
            windows_changed = True
            self.last_window.top_row = int((self.camera.state.top / 32) + 20)
            self.last_window.bottom_row = int((self.camera.state.top / 32))

            missing_rows = [obj for obj in range(self.last_window.bottom_row - 1, self.last_window.top_row + 1) if
                            obj not in self.entity_rows]
            # Create missing rows
            for row in missing_rows:
                x = 0
                self.entity_rows.append(int(row))
                floor = get_floor(int(row))
                y = ((20 - row) * 32)
                if row not in reported_row:
                    reported_row.append(row)
                    # print("Creating Row |" + str(int(row)) + "|")
                    # print( "|" + floor + "|")
                for col in floor:
                    if col == "1":
                        if randint(0, 9) == 3:
                            p = PlatformCrackable(x, y, (int(row)),
                                                  [self.platform_image, self.platform_image_broke_1,
                                                   self.platform_image_broke_2])
                        else:
                            p = Platform(x, y, (int(row)), self.platform_images, self.platform_images_alt)
                        self.platforms.append(p)
                        self.entities.add(p)
                    if col == "2":
                        p = LooseBlock(x, y, row, self.loose_platform_image)
                        self.platforms.append(p)
                        self.loose_platforms.append(p)
                        self.entities.add(p)
                    if col == "3":
                        p = FloatingBlock(x, y, row)
                        self.platforms.append(p)
                        self.loose_platforms.append(p)
                        self.entities.add(p)
                    if col == "4":
                        p = PlatformTrampoline(x, y, row, self.platform_trampoline, self.platform_trampoline_alt)
                        self.platforms.append(p)
                        self.entities.add(p)
                    if col == "E":
                        e = ExitBlock(x, y, row)
                        self.platforms.append(e)
                        self.entities.add(e)
                    if col == "5":
                        p = LiveBlock(x, y, row, self.live_platform_images)
                        self.platforms.append(p)
                        self.live_platforms.append(p)
                        self.entities.add(p)
                    x += 32

        # update player, draw everything else
        self.player.update(self.up, self.down, self.left, self.right, self.running, self.platforms)
        try:
            # self.ghost.update(self.running, self.platforms)
            #if self.ghost is not None:
                # Check if ghost is in the window if not remove it
            #    if not self.camera.state.contains(Rect(self.ghost.rect.x,self.ghost.rect.y, self.ghost.rect.x+32, self.ghost.rect.y -32) ):
                    # ghost is not inside the camera, kill it!
            #        self.kill_enemy(self.ghost)
            #        self.ghost = None
            #    else:
            self.ghost.update(self.up, self.down, self.left, self.right, self.running, self.platforms)
        except:
            pass

        # check if collide
        if (self.ghost is None or not self.ghost.alive) and self.player.alive:
            self.ghost = Ghost(self.player.rect.x, self.player.rect.y, self.game_sprite_sheet, self.player_base_x,
                               32 * 6)
            self.entities.add(self.ghost)

        if self.ghost is not None and self.ghost.active and pygame.sprite.collide_rect(self.player, self.ghost):
            self.player.alive = False
            self.kill_enemy(self.ghost)
            self.ghost = None

        # update loose platforms
        [lp.update(self.platforms) for lp in self.loose_platforms]

        # Do animation for live platform (fans)
        if self.toggle_animate:
            [lp.animate() for lp in self.live_platforms]

    def handle_events(self, events):
        for e in events:
            if e.type == self.ANIMATE_BLOCK_EVENT:
                self.toggle_animate = True
        # Get user input
        pressed = pygame.key.get_pressed()
        self.up, self.down, self.left, self.right, self.running = [pressed[key_code] for key_code in
                                                                   (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE)]

    def kill_enemy(self, enemy):
        enemy.alive = False
        enemy.reboot()
        self.entities.remove(enemy)
        enemy.kill()
        # enemy = None


def main():
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("PyJump Use arrows to move!")
    timer = pygame.time.Clock()

    game_scene = GameScene()

    while 1:
        timer.tick(60)
        toggle_animate = False

        for e in pygame.event.get():
            if e.type == QUIT: raise SystemExit("QUIT")
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                raise SystemExit("ESCAPE")

        # handle events
        game_scene.handle_events(pygame.event.get())
        # Render scene
        game_scene.render(screen)
        # Process actions
        game_scene.update()

        # print("Window " + str((camera.state.top/32)+20) + " " + str((camera.state.top/32)))

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


# image_standing, images_walking, image_jump):
class Player(Entity):
    def __init__(self, x, y, sprite_sheet, player_base_x, player_base_y):
        Entity.__init__(self)
        self.alive = True
        self.flip_pos = x
        self.look_right = True
        self.walk_status = True
        self.x_vel = 0
        self.y_vel = 0
        self.onGround = False
        self.image_jump = load_image(sprite_sheet, player_base_x, player_base_y)
        self.images_walking = [load_image(sprite_sheet, player_base_x + 32 * 1, player_base_y),
                               load_image(sprite_sheet, player_base_x + 32 * 2, player_base_y)]
        self.image_standing = self.images_walking[1]
        self.image = self.image_standing

        self.image.convert()
        self.rect = Rect(x, y, 32, 32)
        self.last_rect = Rect(self.rect)

    def refresh_image(self):
        tmp_image = self.image
        if self.rect.y == self.last_rect.y:
            if self.last_rect.x == self.rect.x:
                tmp_image = self.image_standing
            elif self.flip_pos != self.rect.x and abs(abs(self.flip_pos) - abs(self.rect.x)) > 6:
                self.walk_status = not self.walk_status
                self.flip_pos = self.rect.x
                if self.walk_status:
                    tmp_image = self.images_walking[0]
                else:
                    tmp_image = self.images_walking[1]
        else:
            tmp_image = self.image_jump

        if not self.look_right and tmp_image != self.image:
            tmp_image = pygame.transform.flip(tmp_image, True, False)

        self.image = tmp_image
        # saves last y pos
        self.last_rect = Rect(self.rect)

    def update(self, up, down, left, right, running, platforms):
        if not self.alive:
            self.rect.top += -5
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
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):

                if isinstance(p, Enemy):
                    self.alive = False
                if p.row <= 1:
                    self.alive = True
                if not self.alive:
                    return

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


class Enemy:
    def __init__(self):
        pass


class Window():
    def __init__(self, top_row, bottom_row):
        self.top_row = top_row
        self.bottom_row = bottom_row


class BaseEntity(Entity):
    def __init__(self, row):
        Entity.__init__(self)
        self.row = int(row)

    def is_rubber(self):
        return 0


class Platform(BaseEntity):
    def __init__(self, x, y, map_row, images, images_alt):
        BaseEntity.__init__(self, map_row)
        self.images = images
        self.images_alt = images_alt
        self.image_index = randint(0, len(images) - 1)
        self.image = self.default_image()
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)

    def default_image(self):
        return self.images[self.image_index]

    def bellow_touch(self):
        self.image = self.images_alt[self.image_index]

    def step_over(self):
        pass

    def is_rubber(self):
        try:
            if self.image == self.images_alt[self.image_index]:
                return -2
            else:
                return 0
        except:
            return 0

    def update(self):
        pass


class PlatformCrackable(Platform):
    def __init__(self, x, y, map_row, images):
        Platform.__init__(self, x, y, map_row, images, None)
        self.image_pos = 0
        self.images = images

    def default_image(self):
        return self.images[0]

    def bellow_touch(self):
        if self.image_pos < (len(self.images) - 1):
            self.image_pos += 1
            self.image = self.images[self.image_pos]


class PlatformTrampoline(Platform):
    def __init__(self, x, y, map_row, image, image_alt):
        Platform.__init__(self, x, y, map_row, [image], None)
        self.rect = Rect(x, y, 32, 32)
        self.image = image
        self.image_alt = image_alt
        self.press_count = 0

    def is_rubber(self):
        return -10

    def release(self):
        self.image = self.default_image()

    def step_over(self):
        self.image = self.image_alt
        t = Timer(0.1, self.release)
        t.start()

    def bellow_touch(self):
        pass


class LiveBlock(Platform):
    def __init__(self, x, y, map_row, images):
        Platform.__init__(self, x, y, map_row, images, None)
        self.image_iterator = iter(self.images)
        # Be on/off default as random
        self.is_active = bool(random.getrandbits(1))

    def animate(self):
        if not self.is_active:
            return
        # toggle image
        try:
            self.image = next(self.image_iterator)
        except:
            self.image_iterator = iter(self.images)
            self.image = next(self.image_iterator)

    def is_rubber(self):
        return 0

    def bellow_touch(self):
        self.is_active = not self.is_active


class LooseBlock(BaseEntity):
    def __init__(self, x, y, map_row, image):
        BaseEntity.__init__(self, map_row)
        self.x_vel = 0
        self.y_vel = 0
        self.onGround = True
        self.image = image
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)

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


class Action:
    def __init__(self, up, down, left, right, running):
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.running = running


class Ghost(Player, Enemy):
    def __init__(self, x, y, sprite_sheet, player_base_x, player_base_y):
        Player.__init__(self, x, y, sprite_sheet, player_base_x, player_base_y)
        self.active = False
        self.born = pygame.time.get_ticks()
        self.delay_start = 1500
        self.action_queue = deque()

    def reboot(self):
        self.born = pygame.time.get_ticks()
        self.action_queue.clear()
        self.active = False

    def get_age(self):
        return pygame.time.get_ticks() - self.born

    def update(self, up, down, left, right, running, platforms):
        self.action_queue.append(Action(up, down, left, right, running))
        if not self.active and self.get_age() > self.delay_start:
            self.active = True
        if self.active:
            action = self.action_queue.popleft()
            Player.update(self, action.up, action.down, action.left, action.right, action.running, platforms)


class StupidEnemy(Player, Enemy):
    def __init__(self, x, y, sprite_sheet, player_base_x, player_base_y):
        Player.__init__(self, x, y, sprite_sheet, player_base_x, player_base_y)
        self.x_vel = 2
        self.row = abs(self.rect.bottom / 32)

    def update_row(self):
        self.row = abs(self.rect.bottom / 32)

    def update(self, running, platforms):
        # switch Side
        # if self.x_vel == 0:
        #    self.look_right = not self.look_right
        #    self.x_vel = -2

        # print (self.x_vel)

        if running:
            self.x_vel = 10
        if self.x_vel < 0:
            # self.x_vel = -4
            self.look_right = False
        if self.x_vel > 0:
            # self.x_vel = 4
            self.look_right = True

        if not self.onGround:
            # only accelerate with gravity if in the air
            self.y_vel += 0.3
            self.onGround = False
            # max falling speed
            if self.y_vel > 50: self.y_vel = 50

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
        self.update_row()

    def random_jump(self):
        if bool(random.getrandbits(1)):
            # Get a Random height
            self.y_vel = random.randint(4, 20) * -1

    def collide(self, x_vel, y_vel, platforms):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, ExitBlock):
                    pygame.event.post(pygame.event.Event(QUIT))
                if x_vel > 0:
                    self.rect.right = p.rect.left
                    self.x_vel = -1 * x_vel
                    self.look_right = not self.look_right
                    self.random_jump()
                if x_vel < 0:
                    self.rect.left = p.rect.right
                    self.x_vel = -1 * x_vel
                    self.look_right = not self.look_right
                    self.random_jump()
                if y_vel > 0:
                    self.rect.bottom = p.rect.top
                    self.onGround = True
                    try:
                        p.step_over()
                    except:
                        pass
                    try:
                        self.y_vel = p.is_rubber()
                    except:
                        pass
                if y_vel < 0:
                    try:
                        p.bellow_touch()
                    except:
                        pass
                    # p.image = platform_image_alt
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
