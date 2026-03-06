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
    
    def activate(self, active):
        self.active = active
        self.color = self.color_active if active else self.color_inactive
    
    def handle_event(self, pos):
        if self.is_clicked(pos):
            self.active = True
            self.color = self.color_active
        else:
            self.active = False
            self.color = self.color_inactive


    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

        txt_surf = self.font.render(self.txt,True,(255,255,255))
        surface.blit(txt_surf, (self.rect.x+5, self.rect.y+5))


        
                    
                    

            

    
