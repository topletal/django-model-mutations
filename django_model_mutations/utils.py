from django.core.exceptions import ImproperlyConfigured
from graphene import Field, InputObjectType
from graphene_django.registry import get_global_registry
from graphene_django.types import ErrorType
from graphene_django.utils import camelize
from graphene_django.rest_framework.serializer_converter import convert_serializer_field


# HELPER FUNCTIONS
def convert_serializer_to_input_type(serializer_class, is_input=True):
    input_type_name = '{}{}'.format('Create' if is_input else 'Update', serializer_class.__name__)
    cached_type = convert_serializer_to_input_type.cache.get(input_type_name, None)
    if cached_type:
        return cached_type
    serializer = serializer_class()

    items = {
        name: convert_serializer_field(field, is_input=is_input)
        for name, field in serializer.fields.items()
    }
    ret_type = type(
        "{}Input".format(input_type_name),
        (InputObjectType,),
        items,
    )
    convert_serializer_to_input_type.cache[input_type_name] = ret_type
    return ret_type


convert_serializer_to_input_type.cache = {}


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_errors(errors):
    error_list = list()
    errors = camelize(errors)
    for key, value in errors.items():
        error_list.append(ErrorType(field=key, messages=value[0]))
    return error_list


def get_output_fields(model, return_field_name):
    """Return mutation output field for model instance."""
    model_type = get_global_registry().get_type_for_model(model)
    if not model_type:
        raise ImproperlyConfigured(
            "Unable to find type for model %s in graphene registry" % model.__name__
        )
    fields = {return_field_name: Field(model_type)}
    return fields


def serialize_errors(errors):
    if isinstance(errors, list):
        err_dict = dict()
        for error in errors:
            for key, value in error.items():
                if key not in err_dict:
                    err_dict[key] = value
                else:
                    err_dict[key].append(value)
        return err_dict
    else:
        return errors
