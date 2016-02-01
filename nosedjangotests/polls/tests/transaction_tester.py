from django.db.transaction import atomic


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
