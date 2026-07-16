from decimal import Decimal

from ..models import Config


def ball_to_tickets(ball_balance: Decimal) -> int:
    """tickets = floor(ball_balance / ticket_threshold). Holding $BALL is
    what earns entries -- balances are never consumed by a drawing.
    """
    config = Config.get_solo()
    threshold = Decimal(config.ticket_threshold)
    if threshold <= 0 or ball_balance <= 0:
        return 0
    return int(ball_balance // threshold)
