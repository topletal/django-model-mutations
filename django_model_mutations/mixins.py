from django.utils.translation import gettext_lazy as _


class LoginRequiredMutationMixin:
    @classmethod
    def mutate(cls, root, info, **input):
        if not info.context.user.is_authenticated:
            raise PermissionError(_("Login required"))
        return super().mutate(root, info, **input)