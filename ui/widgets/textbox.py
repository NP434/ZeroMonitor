import pygame
import ui.theme as theme
from ui.widgets.Button import Button

class Textbox:
    def __init__(self,
                 rect,
                 text="",
                 title=""
    ):
        
        self.rect = pygame.Rect(rect)
        self.txt = ""
        self.placeholder = text
        self.color_inactive = theme.DARK_GRAY
        self.border_radius = 3
        self.color_active = theme.GRAY
        self.color = self.color_inactive
        self.active = False
        self.title = title
        self.font = pygame.font.Font(None,32)
 
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def consume(self, text:str):
        print("current text: %s" % text)
        self.txt += text
    
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
        if self.title:
            title_surf = self.font.render(self.title,True,(255,255,255))
            title_pos = (self.rect.x, self.rect.y - title_surf.get_height() - 5)
            surface.blit(title_surf, title_pos)


        pygame.draw.rect(surface, self.color, self.rect,self.border_radius)

        if self.active or self.txt is not "":
            display_text = self.txt
            text_color = (255, 255, 255)
        else:
            display_text = self.placeholder
            text_color = (150, 150, 150)

        txt_surf = self.font.render(display_text,True,text_color)
        surface.blit(txt_surf, (self.rect.x+5, self.rect.y+5))


        
                    
                    

            

    
