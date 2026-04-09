import pygame
import ui.theme as theme
import ui.utilities as utilities

class DropDown:
    def __init__(self, app, rect, options, default=None):
        self.app = app
        self.rect = rect
        self.options = options
        self.selected = default if default else options[0]
        self.expanded = False

        self.option_height = rect.height
        self.font = theme.FONT_MEDIUM
        self.max_visible = 5
        self.scroll_offset = 0

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def handle_event(self, event):
        pos = utilities.get_event_pos(event, self.app)

        if event.type == pygame.MOUSEWHEEL and self.expanded:
            self.scroll_offset = max(0, min(self.scroll_offset - event.y, max(0, len(self.options) - self.max_visible)))
            return None

        if event.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            return

        # Toggle open/close when clicking the collapsed box
        if self.is_clicked(pos):
            self.expanded = not self.expanded
            self.scroll_offset = 0  # reset scroll when opening
            return None

        # Handle option clicks when open
        if self.expanded:
            menu_rect = self._expanded_rect()

            # If click inside menu
            if menu_rect.collidepoint(pos):
                visible_options = self.options[self.scroll_offset:self.scroll_offset + self.max_visible]
                index = (pos[1] - menu_rect.y) // self.option_height
                if 0 <= index < len(visible_options):
                    self.selected = visible_options[index]
                    self.expanded = False
                    return self.selected

            # Click outside closes menu
            self.expanded = False

        return None

    # ------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------
    def draw(self, surface):
        """Draw ONLY the collapsed dropdown box."""
        pygame.draw.rect(surface, theme.GRAY, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme.WHITE, self.rect, width=2, border_radius=10)

        text = self.font.render(self.selected, True, theme.WHITE)
        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))

        # Draw arrow
        arrow = "▲" if self.expanded else "▼"
        arrow_surf = self.font.render(arrow, True, theme.WHITE)
        surface.blit(
            arrow_surf,
            (self.rect.right - arrow_surf.get_width() - 10,
             self.rect.y + (self.rect.height - arrow_surf.get_height()) // 2)
        )

    def draw_expanded(self, surface):
        """Draw ONLY the expanded menu. Called last by the screen."""
        if not self.expanded:
            return

        visible_options = self.options[self.scroll_offset:self.scroll_offset + self.max_visible]
        menu_rect = pygame.Rect(
            self.rect.x,
            self.rect.y + self.rect.height,
            self.rect.width,
            len(visible_options) * self.option_height
        )

        # Background
        pygame.draw.rect(surface, theme.GRAY, menu_rect, border_radius=10)
        pygame.draw.rect(surface, theme.WHITE, menu_rect, width=2, border_radius=10)

        # Options
        for i, opt in enumerate(visible_options):
            opt_rect = pygame.Rect(
                menu_rect.x,
                menu_rect.y + i * self.option_height,
                menu_rect.width,
                self.option_height
            )

            # Highlight selected option
            if opt == self.selected:
                pygame.draw.rect(surface, theme.BLUE, opt_rect)

            t = self.font.render(opt, True, theme.WHITE)
            surface.blit(t, (opt_rect.x + 10, opt_rect.y + 10))

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _expanded_rect(self):
        """Rectangle for the expanded menu."""
        visible_count = min(self.max_visible, len(self.options) - self.scroll_offset)
        return pygame.Rect(
            self.rect.x,
            self.rect.y + self.rect.height,
            self.rect.width,
            self.option_height * visible_count
        )
