# Django Model Mutations

This package adds Mutation classes that make creating graphene mutations with django models easier using Django Rest Framework serializers. It extends graphene Mutation class in a similar way to Django Rest Framework views or original Django views.

It also provides easy way to add permissions checks or ensure logged-in user, as well as easy way to override or add funcionality similar to django forms or rest framework views - such as ```get_queryset()``` or ```save()``` functions.

There is also advanced error reporting from rest framework, that returns non-valid fields and error messages.

Inspired by [Saleor](https://github.com/mirumee/saleor), [graphene-django-extras](https://github.com/eamigo86/graphene-django-extras/tree/master/graphene_django_extras) and [django-rest-framework](https://github.com/encode/django-rest-framework)

## Installation
```
pip install django-model-mutations
```


## Basic Usage
Main classes that this package provides:

| mutations | mixins |
| ------ | ------ |
|CreateModelMutation|LoginRequiredMutationMixin|
|CreateBulkModelMutation|
|UpdateModelMutation|
|UpdateBulkModelMutation|
|DeleteModelMutation|
|DeleteBulkModelMutation|


#### Django usage
Input type (Arguments) is generated from serializer fields  
Return type is retrieved by model from global graphene registry, you just have to import it as in example
```python
from django_model_mutations import mutations, mixins
from your_app.types import UserType  # important to import types to register in global registry
from your_app.serializers import UserSerializer


# Create Mutations
# use mixins.LoginRequiredMutationMixin to ensure only logged-in user can perform this mutation
# MAKE SURE this mixin is FIRST in inheritance order
class UserCreateMutation(mixins.LoginRequiredMutationMixin, mutations.CreateModelMutation):
    class Meta:
        serializer_class = UserSerializer
        # OPTIONAL META FIELDS:
        permissions = ('your_app.user_permission',) # OPTIONAL: specify user permissions
        lookup_field = 'publicId'  # OPTIONAL: specify database lookup column, default is 'id' or 'ids'
        return_field_name = 'myUser' # OPTIONAL: specify return field name, default is model name
        input_field_name = 'myUser' # OPTIONAL: specify input field name, defauls is 'input'
        

class UserBulkCreateMutation(mutations.CreateBulkModelMutation):
    class Meta:
        serializer_class = UserSerializer


# Update Mutations
class UserUpdateMutation(mutations.UpdateModelMutation):
    class Meta:
        serializer_class = UserSerializer

# WARNING: Bulk update DOES NOT USE serializer, due to limitations of rest framework serializer. 
# Instead specify model and argument fields by yourself.
class UserBulkUpdateMutation(mutations.UpdateBulkModelMutation):
    class Arguments:
        is_active = graphene.Boolean()

    class Meta:
        model = User

# Delete Mutations
# delete mutations doesn't use serializers, as there is no need
class UserDeleteMutation(mutations.DeleteModelMutation):
    class Meta:
        model = User

class UserBulkDeleteMutation(mutations.DeleteBulkModelMutation):
    class Meta:
        model = User


# Add to graphene schema as usual
class Mutation(graphene.ObjectType):
    user_create = UserCreateMutation.Field()
    ....

schema = graphene.Schema(mutation=Mutation)
```


#### GraphQl usage
The generated GraphQl schema can be modified with ```Meta``` fields as described above in ```UserCreateMutation```.

By default all mutations have ```errors``` field with ```field``` and ```messages``` that contain validation errors from rest-framework serializer or lookup errors. For now permission denied and other exceptions will not use this error reporting, but a default one, for usage see tests.
```graphql
# default argument name is input
# default return field name is model name
mutation userCreate (input: {username: "myUsername"}) {
    user {
        id
        username
    }
    errors {
        field
        messages
    }
}


# Bulk operations return 'count' and errors
mutation userCreate (input: {username: "myUsername"}) {
    count
    errors {
        field
        messages
    }
}

# update mutations
# update and delete mutations by default specify lookup field 'id' or 'ids' for bulk mutations
mutation {
    userUpdate (id: 2, input: {username:"newUsername"} ) {
        user {
            id
            username
        }  
        errors {
            field
            messages
        }
    } 
}   


mutation {
    userBulkUpdate (ids: [2, 3], isActive: false ) {
        count
        errors {
           field
           messages
        }
    }
}  


# delete mutations
mutation {
    userDelete (id: 1) {
        user {
            id
        }
        errors {
           field
           messages
        }
    }
}  


mutation {
    userBulkDelete (ids: [1, 2, 3]) {
        count
        errors {
           field
           messages
        }
    }
}  
```

### Adding funcionality
All classes are derived from ```graphene.Mutation```. When you want to override some major functionality, the best place probabably is ```perform_mutate```, which is called after permission checks from graphene ```mutate```.  

In general probably the main functions that you want to override are: ```save()``` and ```get_object()``` for single object mutations or ```get_queryset()``` for bulk mutations.  
```get_object``` or ```get_queryset``` you should override to add more filters for fetching the object.   
```save``` performs final save/update/delete to database and you can add additional fields there.

Examples:
```python
# lets only update users that are inactive and add some random field
class UserUpdateInactiveMutation(mutations.UpdateModelMutation):
    class Meta:
        model = User

    @classmethod
    def get_object(cls, object_id, info, **input):
    # can get the object first and then check
        obj = super(UserUpdateInactiveMutation, cls).get_object(object_id, info, **input)
        if obj.is_active:
            return None
        return obj

    @classmethod
    def save(cls, serializer, root, info, **input):
        saved_object = serializer.save(updated_by=info.context.user)
        return cls.return_success(saved_object)


# same but for bulk mutation we have to override get_queryset
class UserBulkUpdateInactiveMutation(mutations.UpdateBulkModelMutation):
    class Meta:
        model = User

    @classmethod
    def get_queryset(cls, object_ids, info, **input):
        qs = super(UserBulkUpdateInactiveMutation, cls).get_queryset(object_ids, info, **input)
        qs.filter(is_active=False)
        return qs
```

For the whole function flow, please check the Base models in ```django_model_mutations\mutations.py```.
It was inspired by rest framework, so you can find functions like ```get_serializer_kwargs```, ```get_serializer```, ```validate_instance``` (for example here you can override default ```ValidationError``` exception and return None if you don't want exception of non existing id lookup etc.)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
