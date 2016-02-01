from django.db import transaction
try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic


@atomic
def decorator_reset_choice(choice):
    choice.votes = 0
    choice.save()
    return choice.pk


@atomic()
def callable_reset_choice(choice):
    choice.votes = 0
    choice.save()
    return choice.pk


def ctxt_man_reset_choice(choice):
    with atomic():
        choice.votes = 0
        choice.save()
        return choice.pk


@transaction.atomic
def transaction_decorator_reset_choice(choice):
    choice.votes = 0
    choice.save()
    return choice.pk


@transaction.atomic()
def transaction_callable_reset_choice(choice):
    choice.votes = 0
    choice.save()
    return choice.pk


def transaction_ctxt_man_reset_choice(choice):
    with transaction.atomic():
        choice.votes = 0
        choice.save()
        return choice.pk
