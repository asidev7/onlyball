from django.db import transaction

from ..models import Config, ConfigChangeLog

TRACKED_FIELDS = (
    'ball_price_usdt', 'ticket_threshold', 'jackpot_bps', 'rollover_bps',
    'fee_bps', 'min_withdraw_usdt', 'kyc_threshold_usdt', 'manual_deposit_address',
)


@transaction.atomic
def update_config(changes: dict, changed_by=None) -> Config:
    """The only sanctioned way to mutate Config: every changed field is
    mirrored into the immutable ConfigChangeLog audit trail.
    """
    config = Config.objects.select_for_update().get(pk=Config.get_solo().pk)
    for field, new_value in changes.items():
        if field not in TRACKED_FIELDS:
            continue
        old_value = getattr(config, field)
        if str(old_value) == str(new_value):
            continue
        ConfigChangeLog.objects.create(
            field_name=field,
            old_value=str(old_value),
            new_value=str(new_value),
            changed_by=changed_by,
        )
        setattr(config, field, new_value)
    config.save()
    return config
