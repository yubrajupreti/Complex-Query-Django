from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.db.models import Q

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from user.serializers import UserSerializer


class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def parse_search_phrase(self,allowed_fields, phrase):
        allowed_data=[(k,v) for k,v in allowed_fields.items()]

        if len(allowed_data) == 1:
            return Q(allowed_data[0])

        elif len(allowed_data)==2:
            if 'AND' in phrase:
                return Q(allowed_data[0]) & Q(allowed_data[1])
            else:
                return Q(allowed_data[0]) | Q(allowed_data[1])

        elif len(allowed_data) ==3:
            if phrase[0]=='AND' and phrase[1]=='OR':
                return Q(allowed_data[0]) & Q(allowed_data[1]) | Q(allowed_data[2])
            else:
                return Q(allowed_data[0]) | Q(allowed_data[1]) & Q(allowed_data[2])

        else:
            raise ValidationError({'detail':'Only three condition can be applied'})




    def perform_create(self, serializer):
        serializer.validated_data['password'] = make_password((serializer.validated_data['password']))
        serializer.save()


    @action(methods=['post'], detail=False)
    def filter(self, request, *args, **kwargs):

        data_keys=request.data.keys()

        if 'allowed_fields' not in data_keys:
            raise ValidationError({"detail":"allowed_fields field cannot be null"})

        if 'search_phrase' not in data_keys:
            raise ValidationError({"detail":"search_phrase field cannot be null"})

        allowed_fields = request.data['allowed_fields']
        search_phrase = request.data['search_phrase']

        if not isinstance(allowed_fields,dict):
            raise ValidationError({"detail":"allowed_fields field should be dictionary type"})

        elif not isinstance(search_phrase,list):
            raise ValidationError({"detail":"search_phrase field should be list type"})

        elif len(search_phrase) >0:
            for operator in search_phrase:
                if operator not in ['AND','OR']:
                    raise ValidationError({'detail':f'{operator} is not a valid operator'})

        elif len(allowed_fields) == 1 and len(search_phrase)>0:
            raise ValidationError({'detail':'search_phrase field has unwanted operators'})

        elif len(allowed_fields)-1 != len(search_phrase):
            raise ValidationError({'detail':'Data and operator are not applicable with each other'})

        else:
            search_filter=self.parse_search_phrase(allowed_fields,search_phrase)

        try:
            queryset=User.objects.filter(search_filter)

        except FieldError as e:
            raise ValidationError({'detail':e})


        serializers=UserSerializer(queryset,many=True)

        return Response(serializers.data)







