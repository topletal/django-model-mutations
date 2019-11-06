import pytest
from django.contrib.auth.models import Permission

from .client import ApiClient, UserApiClient

from .models import Author


@pytest.fixture
def create_authors(db):
    return Author.objects.bulk_create(
        [
            Author(name='Mark Steven', public_id='id1'),
            Author(name='John Sunny', public_id='id2'),
            Author(name='Peter Jacobs', public_id='id3')
        ]
    )


@pytest.mark.django_db
def test_simple_create_mutation():
    query = '''mutation {
        authorCreate (input: {name:"John Doe"}) {
            author {
                id
                name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorCreate']['author']['name'] == 'John Doe'
    assert data['data']['authorCreate']['author']['id'] == '1'
    assert data['data']['authorCreate']['errors'] == []


@pytest.mark.django_db
def test_simple_bulk_create_mutation():
    query = '''mutation {
        authorBulkCreate (input: [{name:"John Doe"}, {name:"Mark Steven"}]) {
            count
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorBulkCreate']['count'] == 2
    assert data['data']['authorBulkCreate']['errors'] == []


@pytest.mark.django_db
def test_simple_bulk_delete_mutation(create_authors):
    query = '''mutation {
        authorBulkDelete (ids: [2, 3]) {
            count
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorBulkDelete']['count'] == 2
    assert data['data']['authorBulkDelete']['errors'] == []


@pytest.mark.django_db
def test_simple_delete_mutation(create_authors):
    query = '''mutation {
        authorDelete (id: 2) {
            author {
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorDelete']['author']['id'] == '2'
    assert data['data']['authorDelete']['author']['name'] == create_authors[1].name
    assert data['data']['authorDelete']['errors'] == []


@pytest.mark.django_db
def test_simple_update_mutation(create_authors):
    query = '''mutation {
        authorUpdate (id: 2, input: {name:"Bart Stevens"} ) {
            author {
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorUpdate']['author']['id'] == '2'
    assert data['data']['authorUpdate']['author']['name'] == 'Bart Stevens'
    assert data['data']['authorUpdate']['errors'] == []


@pytest.mark.django_db
def test_simple_bulk_update_mutation(create_authors):
    query = '''mutation {
            authorBulkUpdate (ids: [2, 3], isActive: false ) {
                count
                errors {
                    field
                    messages
                }
            }
        }  
    '''

    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorBulkUpdate']['count'] == 2
    assert data['data']['authorBulkUpdate']['errors'] == []


@pytest.mark.django_db
def test_update_no_permissions(create_authors):
    query = '''mutation {
        authorPermissionUpdate (id: 2, input: {isActive: false} ) {
            author {
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''

    client = UserApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorPermissionUpdate'] is None
    assert data['errors'][0]['message'] == 'Permission denied'


def test_update_permissions(create_authors):
    query = '''mutation {
        authorPermissionUpdate (id: 2, input: {isActive: false} ) {
            author {
               id
               name
               isActive
            }
            errors {
                field
                messages
            }
        }
    }    
    '''

    client = UserApiClient()
    response = client.query_with_permissions(query)
    data = response.json()
    assert data['data']['authorPermissionUpdate']['author']['isActive'] == False
    assert data['data']['authorPermissionUpdate']['errors'] == []



@pytest.mark.django_db
def test_error_create_mutation():
    query = '''mutation {
        authorCreate (input: {name: ""}) {
            author {
                id
                name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorCreate']['author'] == None
    assert data['data']['authorCreate']['errors'][0]['field'] == 'name'



@pytest.mark.django_db
def test_simple_update_mutation(create_authors):
    query = '''mutation {
        authorUpdate (id: 100, input: {name:"Bart Stevens"} ) {
            author {
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorUpdate']['author'] == None
    assert data['data']['authorUpdate']['errors'][0]['field'] == 'id'


@pytest.mark.django_db
def test_lookup_field_mutation(create_authors):
    query = '''mutation {
        authorLookupUpdate (publicId: "id2", input: {name:"Bart Stevens"} ) {
            author {
               publicId
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''

    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorLookupUpdate']['author']['publicId'] == 'id2'
    assert data['data']['authorLookupUpdate']['author']['id'] == '2'
    assert data['data']['authorLookupUpdate']['author']['name'] == 'Bart Stevens'
    assert data['data']['authorLookupUpdate']['errors'] == []


@pytest.mark.django_db
def test_lookup_field_bulk_mutation(create_authors):
    query = '''mutation {
        authorLookupBulkDelete (publicIds: ["id2", "id3"]) {
            count
            errors {
                field
                messages
            }
        }
    }    
    '''

    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorLookupBulkDelete']['count'] == 2
    assert data['data']['authorLookupBulkDelete']['errors'] == []


@pytest.mark.django_db
def test_no_login_update_mutation(create_authors):
    query = '''mutation {
        authorLoginRequiredUpdate (id: 2, input: {name:"Bart Stevens"} ) {
            author {
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorLoginRequiredUpdate'] is None
    assert data['errors'][0]['message'] == 'Login required'


@pytest.mark.django_db
def test_login_update_mutation(create_authors):
    query = '''mutation {
        authorLoginRequiredUpdate (id: 2, input: {name:"Bart Stevens"} ) {
            author {
               id
               name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = UserApiClient()
    response = client.query_with_permissions(query)
    data = response.json()
    assert data['data']['authorLoginRequiredUpdate']['author']['id'] == '2'
    assert data['data']['authorLoginRequiredUpdate']['author']['name'] == 'Bart Stevens'
    assert data['data']['authorLoginRequiredUpdate']['errors'] == []


@pytest.mark.django_db
def test_custom_fields_create_mutation():
    query = '''mutation {
        authorCustomFieldCreate (newAuthor: {name:"John Doe"}) {
            customAuthor {
                id
                name
            }
            errors {
                field
                messages
            }
        }
    }    
    '''
    client = ApiClient()
    response = client.query(query)
    data = response.json()
    assert data['data']['authorCustomFieldCreate']['customAuthor']['name'] == 'John Doe'
    assert data['data']['authorCustomFieldCreate']['errors'] == []
