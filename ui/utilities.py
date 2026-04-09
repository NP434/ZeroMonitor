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

def dim_background(app, surface):
    overlay = pygame.Surface((app.width, app.height), pygame.SRCALPHA) 
    overlay.fill((0, 0, 0, 120)) 
    surface.blit(overlay, (0, 0))

def format_metric_value(self, metric_name, metric_value):
        if metric_value is None:
            return "N/A"

        # Uptime formatting
        if metric_name == "uptime_seconds":
            total = int(metric_value)
            days = total // 86400
            hours = (total % 86400) // 3600
            mins = (total % 3600) // 60
            if days > 0:
                return f"{days}d {hours}h {mins}m"
            return f"{hours}h {mins}m"

        # Network Formatting
        if metric_name in {"net_rx_kbps", "net_tx_kbps"}:
            if metric_value >= 1000:
                return f"{metric_value / 1000.0:.2f} Mbps"
            return f"{metric_value:.0f} kbps"

        # Memory Formatting
        if metric_name in {"mem_used_mb", "mem_total_mb"}:
            return f"{int(metric_value)}{self.METRIC_UNITS.get(metric_name, '')}"

        # CPU Temperature formatting
        if metric_name == "cpu_temp_c":
            unit = self.app.temp_unit
            value = float(metric_value)

            if unit == "F":
                value = value * 9/5 + 32
            
            return f"{value:.1f}°{unit}"

        # CPU load formatting
        if metric_name == "cpu_load_1m":
            return f"{metric_value:.2f}"

        if isinstance(metric_value, float):
            return f"{metric_value:.2f}{self.METRIC_UNITS.get(metric_name, '')}"

        return f"{metric_value}{self.METRIC_UNITS.get(metric_name, '')}"
