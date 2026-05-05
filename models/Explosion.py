import pygame


class Explosion(pygame.sprite.Sprite):
    DURATION = 20

    def __init__(self, center):
        super().__init__()
        self._center = center
        self._frame = 0
        self._build_image()

    def _build_image(self):
        t = self._frame / self.DURATION
        radius = int(5 + t * 16)
        size = radius * 2 + 2
        cx = cy = size // 2

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        # outer ring: orange, fades out
        alpha_outer = int(200 * (1 - t))
        pygame.draw.circle(self.image, (255, int(100 * (1 - t)), 0, alpha_outer), (cx, cy), radius)

        # inner core: bright yellow, shrinks and fades
        inner_r = max(1, int(radius * 0.5 * (1 - t)))
        alpha_inner = int(255 * (1 - t))
        pygame.draw.circle(self.image, (255, 240, 100, alpha_inner), (cx, cy), inner_r)

        self.rect = self.image.get_rect(center=self._center)

    def update(self):
        self._frame += 1
        if self._frame >= self.DURATION:
            self.kill()
            return
        self._build_image()
