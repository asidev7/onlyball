from rest_framework import serializers

from .models import Account, Round, Ticket


class TicketSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source="account.address", read_only=True)
    round_index = serializers.IntegerField(source="round.index", read_only=True)
    round_status = serializers.CharField(source="round.status", read_only=True)
    winning_numbers = serializers.JSONField(
        source="round.winning_numbers", read_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "address",
            "round_index",
            "round_status",
            "winning_numbers",
            "numbers",
            "txid",
            "paid_fudsx",
            "matched",
            "is_winner",
            "created_at",
        ]


class RoundSerializer(serializers.ModelSerializer):
    tickets_count = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = [
            "index",
            "status",
            "opens_at",
            "draws_at",
            "winning_numbers",
            "jackpot_fudsx",
            "tickets_count",
        ]

    def get_tickets_count(self, obj) -> int:
        return obj.tickets.count()


class AccountSerializer(serializers.ModelSerializer):
    tickets_count = serializers.SerializerMethodField()
    referrals_count = serializers.SerializerMethodField()
    referred_by = serializers.CharField(
        source="referred_by.address", read_only=True, default=None
    )

    class Meta:
        model = Account
        fields = [
            "address",
            "referral_code",
            "referred_by",
            "referral_earnings_fudsx",
            "tickets_count",
            "referrals_count",
            "created_at",
        ]

    def get_tickets_count(self, obj) -> int:
        return obj.tickets.count()

    def get_referrals_count(self, obj) -> int:
        return obj.referrals.count()
