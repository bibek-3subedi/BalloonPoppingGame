import pygame

def midpoint_ellipse(cx: int, cy: int, rx: int, ry: int):
    """
    Implements the midpoint ellipse drawing algorithm.
    Returns a list of points (x, y) representing the boundary of the ellipse.
    """
    points = []
    
    # Region 1
    x = 0
    y = ry
    d1 = (ry**2) - (rx**2 * ry) + (0.25 * rx**2)
    dx = 2 * ry**2 * x
    dy = 2 * rx**2 * y
    
    while dx < dy:
        # Add points in all 4 quadrants (symmetry)
        points.append((cx + x, cy + y))
        points.append((cx - x, cy + y))
        points.append((cx + x, cy - y))
        points.append((cx - x, cy - y))
        
        if d1 < 0:
            x += 1
            dx += 2 * ry**2
            d1 += dx + ry**2
        else:
            x += 1
            y -= 1
            dx += 2 * ry**2
            dy -= 2 * rx**2
            d1 += dx - dy + ry**2
            
    # Region 2
    d2 = ((ry**2) * ((x + 0.5)**2)) + ((rx**2) * ((y - 1)**2)) - (rx**2 * ry**2)
    
    while y >= 0:
        points.append((cx + x, cy + y))
        points.append((cx - x, cy + y))
        points.append((cx + x, cy - y))
        points.append((cx - x, cy - y))
        
        if d2 > 0:
            y -= 1
            dy -= 2 * rx**2
            d2 += rx**2 - dy
        else:
            y -= 1
            x += 1
            dx += 2 * ry**2
            dy -= 2 * rx**2
            d2 += dx - dy + rx**2
            
    return points

def filled_ellipse(screen: pygame.Surface, cx: int, cy: int, rx: int, ry: int, color: tuple):
    """
    Draws a filled ellipse using scanline fill based on the midpoint algorithm logic.
    """
    x = 0
    y = ry
    d1 = (ry**2) - (rx**2 * ry) + (0.25 * rx**2)
    dx = 2 * ry**2 * x
    dy = 2 * rx**2 * y
    
    while dx < dy:
        # Draw horizontal lines between symmetric points
        pygame.draw.line(screen, color, (cx - x, cy + y), (cx + x, cy + y))
        pygame.draw.line(screen, color, (cx - x, cy - y), (cx + x, cy - y))
        
        if d1 < 0:
            x += 1
            dx += 2 * ry**2
            d1 += dx + ry**2
        else:
            x += 1
            y -= 1
            dx += 2 * ry**2
            dy -= 2 * rx**2
            d1 += dx - dy + ry**2
            
    d2 = ((ry**2) * ((x + 0.5)**2)) + ((rx**2) * ((y - 1)**2)) - (rx**2 * ry**2)
    
    while y >= 0:
        pygame.draw.line(screen, color, (cx - x, cy + y), (cx + x, cy + y))
        pygame.draw.line(screen, color, (cx - x, cy - y), (cx + x, cy - y))
        
        if d2 > 0:
            y -= 1
            dy -= 2 * rx**2
            d2 += rx**2 - dy
        else:
            y -= 1
            x += 1
            dx += 2 * ry**2
            dy -= 2 * rx**2
            d2 += dx - dy + rx**2
