# Complex-Query-in-Django

The filter accept two fields:
    1. allowed_fields
    2.search_phrase

allowed_fields should be dictionary type. 

search_phrase should be list type.

The example of Json data is :
{
    "allowed_fields":{

        "AND":{"username":"yubraj",
        "email":"yubraj@user.co"},
        "OR":{"first_name":"yubraj"}

        },
        
    "search_phrase":[
        "AND","OR","AND"
        
    ]
}
OR
{
    "allowed_fields":{

        "AND":{"username":"yubraj",
        "email":"yubraj@user.co"},
        "first_name":"yubraj",
     },
        
    "search_phrase":[
        "AND","OR","AND"
    ]
}

The allowed_fields contain nested dictionary when the condition is:
((distance=10) AND (distance<15)) OR(distance>5).

Here,
((distance=10) AND (distance<15)) is express as nested dictionary.
The key for nested dictionary can be anythings. As per defined by user.

The search_phrase data should be in respective order to perform the operation.
The programs takes first elements with allowed_fields first expression to perform AND or OR operation.