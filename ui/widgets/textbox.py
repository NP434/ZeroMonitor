import pygame
import ui.theme as theme
from ui.widgets.Button import Button

class Textbox:
    def __init__(self,
                 rect,
                 text="",
    ):
        
        self.rect = pygame.Rect(rect)
        self.txt = text
        self.color_inactive = ('black')
        self.color_active = ('gray')
        self.color = self.color_inactive
        self.active = False
        self.font = pygame.font.Font(None,32)
 
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def consume(self, text:str):
        print("current text: %s" % text)
        self.txt = text
    
    def activate(self, keyboard):
        keyboard.set_consumer(self.consume)
        self.active = True
    
    def handle_event(self, event):
        # Handles user clicking into text box, and activates virtual keyboard
        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            # determine position
            if event.type == pygame.FINGERDOWN:
                # Finger coordinates are normalized (0.0 - 1.0)
                pos = (
                    int(event.x * self.app.width),
                    int(event.y * self.app.height)
                )
            else:
                # Mouse event provides pixel coordinates
                pos = event.pos

            if self.is_clicked(pos):
                self.active = True
                self.color = self.color_active
            else:
                self.active = False
                self.color = self.color_inactive


    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

        txt_surf = self.font.render(self.txt,True,color="white")
        surface.blit(txt_surf, (self.rect.x+5, self.rect.y+5))






        
                    
                    

            

    
