import graphene
from graphene_django import DjangoObjectType

from django_model_mutations import mutations, mixins
from tests.models import Author
from tests.serializers import AuthorSerializer


class AuthorType(DjangoObjectType):
    class Meta:
        model = Author


class AuthorCreateMutation(mutations.CreateModelMutation):
    class Meta:
        serializer_class = AuthorSerializer


class AuthorBulkCreateMutation(mutations.CreateBulkModelMutation):
    class Meta:
        serializer_class = AuthorSerializer


class AuthorDeleteMutation(mutations.DeleteModelMutation):
    class Meta:
        model = Author


class AuthorBulkDeleteMutation(mutations.DeleteBulkModelMutation):
    class Meta:
        model = Author


class AuthorUpdateMutation(mutations.UpdateModelMutation):
    class Meta:
        serializer_class = AuthorSerializer


class AuthorBulkUpdateMutation(mutations.UpdateBulkModelMutation):
    class Arguments:
        is_active = graphene.Boolean()

    class Meta:
        model = Author


class AuthorPermissionUpdateMutation(mutations.UpdateModelMutation):
    class Meta:
        serializer_class = AuthorSerializer
        permissions = ('tests.change_active',)


class AuthorLookupUpdateMutation(mutations.UpdateModelMutation):
    class Meta:
        serializer_class = AuthorSerializer
        lookup_field = 'public_id'


class AuthorLookupBulkMutation(mutations.DeleteBulkModelMutation):
    class Meta:
        lookup_field = 'public_id'
        model = Author


class AuthorLoginRequiredMutation(mixins.LoginRequiredMutationMixin, mutations.UpdateModelMutation):
    class Meta:
        serializer_class = AuthorSerializer


class AuthorCustomFieldCreateMutation(mutations.CreateModelMutation):
    class Meta:
        serializer_class = AuthorSerializer
        return_field_name = 'customAuthor'
        input_field_name = 'newAuthor'


class Mutation(graphene.ObjectType):
    author_create = AuthorCreateMutation.Field()
    author_bulk_create = AuthorBulkCreateMutation.Field()
    author_delete = AuthorDeleteMutation.Field()
    author_bulk_delete = AuthorBulkDeleteMutation.Field()
    author_update = AuthorUpdateMutation.Field()
    author_bulk_update = AuthorBulkUpdateMutation.Field()
    author_permission_update = AuthorPermissionUpdateMutation.Field()
    author_lookup_update = AuthorLookupUpdateMutation.Field()
    author_lookup_bulk_delete = AuthorLookupBulkMutation.Field()
    author_login_required_update = AuthorLoginRequiredMutation.Field()
    author_custom_field_create = AuthorCustomFieldCreateMutation.Field()


schema = graphene.Schema(mutation=Mutation)
