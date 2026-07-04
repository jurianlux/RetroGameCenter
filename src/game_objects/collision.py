def check_rect_collision(rect1, rect2):
    """矩形同士の衝突判定"""
    return rect1.colliderect(rect2)


def check_point_in_rect(x, y, rect):
    """点が矩形の中にあるか判定"""
    return rect.collidepoint(x, y)
