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

def format_metric_value(metric_name, metric_value, metric_units=None, temp_unit="C"):
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
        unit_str = metric_units.get(metric_name, '') if metric_units else ''
        return f"{int(metric_value)}{unit_str}"

    # CPU Temperature formatting
    if metric_name == "cpu_temp_c":
        value = float(metric_value)
        if temp_unit == "F":
            value = value * 9/5 + 32
        return f"{value:.1f}°{temp_unit}"

    # CPU load formatting
    if metric_name == "cpu_load_1m":
        return f"{metric_value:.2f}"

    if isinstance(metric_value, float):
        unit_str = metric_units.get(metric_name, '') if metric_units else ''
        return f"{metric_value:.2f}{unit_str}"

    unit_str = metric_units.get(metric_name, '') if metric_units else ''
    return f"{metric_value}{unit_str}"