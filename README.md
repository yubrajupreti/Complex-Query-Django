# Complex-Query-in-Django

The filter accept two fields:
    1. allowed_fields
    2.search_phrase

allowed_fields should be list type. 

search_phrase should be list type.

The example of Json data is :
{
    "allowed_fields":[
        "(id lt 5 )", 
        "((email eq yubraj@user.com),(is_active eq True))"
    ] ,

    "search_phrase":[
        "AND",
        "OR"
    ]
}

The search_phrase data should be in respective order to perform the operation.
The programs takes first elements with allowed_fields first expression to perform AND or OR operation.