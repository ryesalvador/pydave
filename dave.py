"""
Copyright (c) 2015-2020 Ryan Dela Rosa Salvador

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the Software), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import tmx, pygame, pyganim
from pygame.sprite import Sprite

class Item(Sprite):
    def __init__(self, location, *groups):
        Sprite.__init__(self, *groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())

    def update(self, dt, game):
        if self.rect.colliderect(game.player.rect):
            game.score = game.score + self.score
            print(game.score)
            self.kill()
    
class Diamond(Item):
    image = pygame.image.load('data/diamond.png')
    score = 100

class Ruby(Item):
    image = pygame.image.load('data/ruby.png')
    score = 150

class Pearl(Item):
    image = pygame.image.load('data/pearl.png')
    score = 50

class Trophy(Item):
    image = pygame.image.load('data/trophy000.png')
    imagesAndDurations = [('data/trophy%s.png' % str(num).rjust(3, '0'), 0.1) for num in range(5)]
    animTrophy = pyganim.PygAnimation(imagesAndDurations)
    score = 1000

    def update(self, dt, game):
        self.animTrophy.play()
        self.image = self.animTrophy.getCurrentFrame() 
        if self.rect.colliderect(game.player.rect):
            self.animTrophy.stop()
            game.score = game.score + self.score
            print('Go thru the door!')
            print(game.score)
            game.exit_door = True
            self.kill()

class Player(Sprite):
    right_jumping = pygame.image.load('data/dave_right_jump.png')
    left_jumping = pygame.transform.flip(right_jumping, True, False)
    animObjs = {}
    imagesAndDurations = [('data/dave_right_walk.%s.png' % str(num).rjust(3, '0'), 0.1) for num in range(4)]
    animObjs['right_walk'] = pyganim.PygAnimation(imagesAndDurations)
 
    animObjs['left_walk'] = animObjs['right_walk'].getCopy()
    animObjs['left_walk'].flip(True, False)
    animObjs['left_walk'].makeTransformsPermanent()

    moveConductor = pyganim.PygConductor(animObjs)

    def __init__(self, location, *groups):
        Sprite.__init__(self, *groups)
        self.image = pygame.image.load('data/dave_front.png')
        self.front_standing = self.image
        self.direction = 'left'
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.resting = False
        self.walking = False
        self.dy = 0

    def update(self, dt, game):
        last = self.rect.copy()

        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            if self.resting:
                self.walking = True
            self.direction = 'left'
            if self.walking:
                self.moveConductor.play()
                self.image = self.animObjs['left_walk'].getCurrentFrame()
            else:
                self.image = self.left_jumping
            self.rect.x -= 100 * dt
        if key[pygame.K_RIGHT]:
            if self.resting:
                self.walking = True
            self.direction = 'right'
            if self.walking:
                self.moveConductor.play()
                self.image = self.animObjs['right_walk'].getCurrentFrame()
            else:
                self.image = self.right_jumping
            self.rect.x += 100 * dt

        if self.resting and key[pygame.K_UP]:
            self.walking = False
            self.moveConductor.stop()
            if self.direction == 'left':
                self.image = self.left_jumping
            else:
                self.image = self.right_jumping
            self.dy = -500
        self.dy = min(400, self.dy + 40)

        self.rect.y += self.dy * dt

        if self.rect.y > last.y + 1:
            self.moveConductor.stop()
            self.walking = False

        new = self.rect
        self.resting = False

        for cell in game.tilemap.layers['triggers'].collide(new, 'blockers'):
            if last.right <= cell.left and new.right > cell.left:
                self.moveConductor.pause()
                new.right = cell.left
            if last.left >= cell.right and new.left < cell.right:
                self.moveConductor.pause()
                new.left = cell.right
            if last.bottom <= cell.top and new.bottom > cell.top:
                self.resting = True
                if not self.walking:
                    self.image = self.front_standing
                new.bottom = cell.top
                self.dy = 0
            if last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0

        if game.exit_door and game.tilemap.layers['triggers'].collide(new, 'exit'):
                print("Good work! 9 more to go")
                game.running = False

        game.tilemap.set_focus(new.x, new.y)

class Game(object):
    exit_door = False
    running = True
    score = 0

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load('data/background.png')
        self.tilemap = tmx.load('map.tmx', screen.get_size())
        self.sprites = tmx.SpriteLayer()
        start_cell = self.tilemap.layers['triggers'].find('player')[0]
        self.player = Player((start_cell.px, start_cell.py), self.sprites)
        self.tilemap.layers.append(self.sprites)
        self.items = tmx.SpriteLayer()

    def start(self):
        for item in self.tilemap.layers['triggers'].find('items'):
            item_value = item['items']
            if 'diamond' in item_value:
                Diamond((item.px, item.py), self.items)
            elif 'ruby' in item_value:
                Ruby((item.px, item.py), self.items)
            elif 'pearl' in item_value:
                Pearl((item.px, item.py), self.items)
            elif 'trophy' in item_value:
                Trophy((item.px, item.py), self.items)
        self.tilemap.layers.append(self.items)

        while self.running:
            dt = self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            self.tilemap.update(dt / 1000., self)
            self.screen.blit(self.background, (0, 0))
            self.tilemap.draw(screen)
            pygame.display.flip()

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    game = Game(screen)
    game.start()
