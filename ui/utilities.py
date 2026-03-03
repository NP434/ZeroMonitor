"""
File of functions used in multiple places within /ui
"""
import pygame

def get_event_pos(event, app):
    """ Return a pixel (x,y) location for different types of events """
    if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
        return (
            int(event.x * app.width),
            int(event.y * app.height)
        )
   
    if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
        return event.pos

    return None
