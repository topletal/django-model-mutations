from collections import OrderedDict

import graphene
from django.core.exceptions import ValidationError, ImproperlyConfigured, ObjectDoesNotExist
from graphene.types.mutation import MutationOptions
from graphene_django.types import ErrorType
from django.utils.translation import ugettext_lazy as _

from .utils import get_errors, get_output_fields, get_model_name, convert_serializer_to_input_type, serialize_errors


####################
# BASE MUTATIONS #
class BaseModelMutationOptions(MutationOptions):
    model = None
    lookup_field = None
    permissions = None


class BaseModelMutation(graphene.Mutation):
    class Meta:
        abstract = True

    errors = graphene.List(ErrorType, description="List of errors")

    @classmethod
    def __init_subclass_with_meta__(
            cls,
            model=None,
            lookup_field=None,
            arguments=None,
            return_field_name=None,
            _meta=None,
            permissions=None,
            **options
    ):

        if not _meta:
            _meta = BaseModelMutationOptions(cls)

        if not model and not _meta.model:
            raise ImproperlyConfigured("model is required for {}".format(cls.__name__))

        if not lookup_field and not _meta.lookup_field:
            lookup_field = model._meta.pk.name

        _meta.lookup_field = lookup_field
        _meta.model = model
        _meta.permissions = permissions
        super(BaseModelMutation, cls).__init_subclass_with_meta__(_meta=_meta, **options)
        arguments = cls.get_arguments(arguments)
        if arguments:
            _meta.arguments.update(arguments)

    @classmethod
    def get_arguments(cls, arguments):
        if not arguments:
            arguments = OrderedDict()
        return arguments

    @classmethod
    def mutate(cls, root, info, **input):
        if not cls.check_permissions(root, info, **input):
            raise PermissionError(_("Permission denied"))

        try:
            mutation_object = cls.get_mutation_object(root, info, **input)
            return cls.perform_mutate(mutation_object, root, info, **input)
        except ValidationError as e:
            errs = get_errors(e.error_dict)
            return cls(errors=errs)

    @classmethod
    def check_permissions(cls, root, info, **input):
        if not cls._meta.permissions:
            return True
        if info.context.user.has_perms(cls._meta.permissions):
            return True
        return False

    @classmethod
    def get_mutation_object(cls, root, info, **input):
        raise NotImplementedError()

    @classmethod
    def perform_mutate(cls, mutation_object, root, info, **input):
        return cls.save(mutation_object, root, info, **input)

    @classmethod
    def save(cls, mutation_object, root, info, **input):
        raise NotImplementedError()


class BaseSingleModelMutationOptions(BaseModelMutationOptions):
    return_field_name = None


class BaseSingleModelMutation(BaseModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
            cls,
            model=None,
            lookup_field=None,
            arguments=None,
            return_field_name=None,
            _meta=None,
            **options
    ):
        if not _meta:
            _meta = BaseSingleModelMutationOptions(cls)

        if not return_field_name:
            return_field_name = get_model_name(model or _meta.model)
        _meta.return_field_name = return_field_name
        _meta.fields = get_output_fields(model, return_field_name)
        super(BaseSingleModelMutation, cls).__init_subclass_with_meta__(model=model, arguments=arguments,
                                                                        lookup_field=lookup_field,
                                                                        _meta=_meta, **options)

    @classmethod
    def get_arguments(cls, arguments):
        if not arguments:
            arguments = OrderedDict()
        arguments[cls._meta.lookup_field] = graphene.ID(required=True, description="Object identifier")
        return super(BaseSingleModelMutation, cls).get_arguments(arguments)

    @classmethod
    def get_mutation_object(cls, root, info, **input):
        lookup_id = input.get(cls._meta.lookup_field, None)
        instance = None
        if lookup_id:
            try:
                instance = cls.get_object(lookup_id, info, **input)
            except ObjectDoesNotExist:
                pass
        return cls.validate_instance(instance, info, **input)

    @classmethod
    def get_object(cls, object_id, info, **input):
        return cls._meta.model.objects.get(**{cls._meta.lookup_field: object_id})

    @classmethod
    def validate_instance(cls, instance, info, **input):
        if instance is None:
            raise ValidationError({cls._meta.lookup_field: _("Object does not exist")})
        return instance

    @classmethod
    def return_success(cls, instance):
        kwargs = {cls._meta.return_field_name: instance}
        return cls(errors=[], **kwargs)

    @classmethod
    def save(cls, mutation_object, root, info, **input):
        raise NotImplementedError()


class BaseBulkModelMutation(BaseModelMutation):
    class Meta:
        abstract = True

    count = graphene.Int(description="Number of objects mutation was performed on")

    @classmethod
    def __init_subclass_with_meta__(
            cls,
            model=None,
            lookup_field=None,
            arguments=None,
            input_field_name='input',
            _meta=None,
            **options
    ):
        if not _meta:
            _meta = BaseModelMutationOptions(cls)
        super(BaseBulkModelMutation, cls).__init_subclass_with_meta__(model=model, arguments=arguments,
                                                                      lookup_field=lookup_field,
                                                                      _meta=_meta, **options)

    @classmethod
    def get_arguments(cls, arguments):
        if not arguments:
            arguments = OrderedDict()

        arguments[cls.get_input_lookup_field()] = graphene.List(graphene.ID, required=True,
                                                                description="Object identifiers")
        return super(BaseBulkModelMutation, cls).get_arguments(arguments)

    @classmethod
    def get_mutation_object(cls, root, info, **input):
        lookup_field = cls.get_input_lookup_field()
        lookup_ids = input.get(lookup_field, None)
        queryset = cls.get_queryset(lookup_ids, info, **input)
        return queryset

    @classmethod
    def get_queryset(cls, object_ids, info, **input):
        return cls._meta.model.objects.filter(**{"{}__in".format(cls._meta.lookup_field): object_ids})

    @classmethod
    def return_success(cls, count):
        kwargs = {"count": count}
        return cls(errors=[], **kwargs)

    @classmethod
    def get_input_lookup_field(cls):
        return "{}s".format(cls._meta.lookup_field)

    @classmethod
    def save(cls, mutation_object, root, info, **input):
        raise NotImplementedError()


class ModelSerializerMutationOptions(BaseModelMutationOptions):
    serializer_class = None
    input_field_name = None


class ModelSerializerMutation(BaseModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
            cls,
            serializer_class=None,
            model=None,
            lookup_field=None,
            input_field_name='input',
            fields=(),
            exclude=(),
            arguments=None,
            _meta=None,
            **options
    ):

        if not _meta:
            _meta = ModelSerializerMutationOptions(cls)

        if not serializer_class:
            raise ImproperlyConfigured("serializer_class is required for {}".format(cls.__name__))

        if not model:
            model = serializer_class.Meta.model

        if not model:
            raise ImproperlyConfigured("model is required for {}".format(cls.__name__))

        _meta.serializer_class = serializer_class
        _meta.input_field_name = input_field_name
        super(ModelSerializerMutation, cls).__init_subclass_with_meta__(
            _meta=_meta, model=model, lookup_field=lookup_field, arguments=arguments, **options
        )

    @classmethod
    def is_input_required(cls):
        return True

    @classmethod
    def get_arguments(cls, arguments):
        if not arguments:
            arguments = OrderedDict()
        input_type = convert_serializer_to_input_type(cls._meta.serializer_class, cls.is_input_required())
        arguments[cls._meta.input_field_name] = graphene.Argument(input_type, required=True)
        return super(ModelSerializerMutation, cls).get_arguments(arguments)

    @classmethod
    def get_serializer_kwargs(cls, serializer_object, serializer_input):
        kwargs = {"instance": serializer_object, "data": serializer_input, "partial": not cls.is_input_required()}
        return kwargs

    @classmethod
    def get_serializer(cls, serializer_object, info, **input):
        serializer_input = input[cls._meta.input_field_name]
        serializer_kwargs = cls.get_serializer_kwargs(serializer_object, serializer_input)
        serializer = cls._meta.serializer_class(**serializer_kwargs)
        return serializer

    @classmethod
    def perform_mutate(cls, mutation_object, root, info, **input):
        serializer = cls.get_serializer(mutation_object, info, **input)
        if not serializer.is_valid():
            raise ValidationError(serialize_errors(serializer.errors))
        return cls.save(serializer, root, info, **input)

    @classmethod
    def save(cls, serializer, root, info, **input):
        raise NotImplementedError()


class SingleModelSerializerMutation(ModelSerializerMutation, BaseSingleModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def save(cls, serializer, root, info, **input):
        saved_object = serializer.save()
        return cls.return_success(saved_object)


class BulkModelSerializerMutation(ModelSerializerMutation, BaseBulkModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def save(cls, serializer, root, info, **input):
        raise NotImplementedError

    @classmethod
    def get_serializer_kwargs(cls, serializer_object, serializer_input):
        kwargs = super(BulkModelSerializerMutation, cls).get_serializer_kwargs(serializer_object, serializer_input)
        kwargs['many'] = True
        return kwargs


####################
# CREATE MUTATIONS #
class CreateModelMutation(SingleModelSerializerMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_mutation_object(cls, root, info, **input):
        return None

    @classmethod
    def get_arguments(cls, arguments):
        arguments = super(CreateModelMutation, cls).get_arguments(arguments)
        if arguments and cls._meta.lookup_field in arguments:
            del arguments[cls._meta.lookup_field]
        return arguments


class CreateBulkModelMutation(BulkModelSerializerMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_mutation_object(cls, root, info, **input):
        return None

    @classmethod
    def get_arguments(cls, arguments):
        arguments = super(CreateBulkModelMutation, cls).get_arguments(arguments)
        lookup_field = cls.get_input_lookup_field()
        if arguments and lookup_field:
            del arguments[lookup_field]

        arguments[cls._meta.input_field_name] = graphene.List(arguments[cls._meta.input_field_name].type.of_type)
        return arguments

    @classmethod
    def save(cls, serializer, root, info, **input):
        saved = serializer.save()
        return cls.return_success(len(saved))


####################
# UPDATE MUTATIONS #
class UpdateModelMutation(SingleModelSerializerMutation):
    class Meta:
        abstract = True

    @classmethod
    def is_input_required(cls):
        return False


class UpdateBulkModelMutation(BaseBulkModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def save(cls, queryset, root, info, **input):
        input.pop(cls.get_input_lookup_field())
        saved = queryset.update(**input)
        return cls.return_success(saved)


####################
# DELETE MUTATIONS #
class DeleteModelMutation(BaseSingleModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def save(cls, instance, root, info, **input):
        saved_id = getattr(instance, cls._meta.model._meta.pk.name)
        instance.delete()
        setattr(instance, cls._meta.model._meta.pk.name, saved_id)
        return cls.return_success(instance)


class DeleteBulkModelMutation(BaseBulkModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def save(cls, queryset, root, info, **input):
        operation = queryset.delete()
        return cls.return_success(operation[0])
