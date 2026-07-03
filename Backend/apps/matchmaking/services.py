from django.db import transaction
from rest_framework.exceptions import APIException, ValidationError

from .models import Match, MatchPlayer


class MatchFull(APIException):
    status_code = 409
    default_detail = "This match is already full."
    default_code = "match_full"


def join_match(*, match: Match, user) -> MatchPlayer:
    with transaction.atomic():
        m = Match.objects.select_for_update().get(pk=match.pk)
        if m.status == Match.Status.CANCELLED:
            raise ValidationError("This match has been cancelled.")
        if m.status == Match.Status.CONFIRMED:
            raise ValidationError("This match is already confirmed.")

        # Create as LEFT so a brand-new row isn't counted as joined before the
        # capacity check below promotes it.
        player, _ = MatchPlayer.objects.get_or_create(
            match=m, user=user, defaults={"status": MatchPlayer.Status.LEFT}
        )
        if player.status == MatchPlayer.Status.JOINED:
            return player

        joined = m.players.filter(status=MatchPlayer.Status.JOINED).count()
        if joined >= m.max_players:
            raise MatchFull()

        player.status = MatchPlayer.Status.JOINED
        player.save(update_fields=["status", "updated_at"])

        if joined + 1 >= m.max_players and m.status == Match.Status.OPEN:
            m.status = Match.Status.FULL
            m.save(update_fields=["status", "updated_at"])
        return player


def leave_match(*, match: Match, user):
    with transaction.atomic():
        m = Match.objects.select_for_update().get(pk=match.pk)
        if m.host_id == user.id:
            raise ValidationError("The host can't leave; cancel the match instead.")
        player = m.players.filter(user=user, status=MatchPlayer.Status.JOINED).first()
        if not player:
            raise ValidationError("You haven't joined this match.")
        player.status = MatchPlayer.Status.LEFT
        player.save(update_fields=["status", "updated_at"])
        if m.status == Match.Status.FULL:
            m.status = Match.Status.OPEN
            m.save(update_fields=["status", "updated_at"])


def cancel_match(*, match: Match):
    match.status = Match.Status.CANCELLED
    match.save(update_fields=["status", "updated_at"])
    return match
