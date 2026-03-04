from django.template import Library

register = Library()


def is_manager(user):
    return user.is_authenticated and user.role in ['ADMIN', 'DIRECTOR']


register.filter('is_manager', is_manager)


@register.filter(name='has_group')
def has_group(user, group_name):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()
