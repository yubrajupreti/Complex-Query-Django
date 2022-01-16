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
        allowed_data=[]
        for key, value in allowed_fields.items():
            # import pdb;pdb.set_trace()
            if isinstance(allowed_fields[key],dict):
                key_data=[(k,v) for k, v in allowed_fields[key].items() ]
                allowed_data.append((key_data))
            else:
                allowed_data.append((key,value))

        counter=0
        count = 0
        all_q_exp_list=[]
        for data in allowed_data:
            if isinstance(data,list):
                q_exp_list=[]
                count=0
                for single_data in data:

                    value=Q(single_data)
                    if count ==0:
                        q_exp_list.append(value)
                    else:
                        if phrase[count-1]=='AND':
                            processed_value=q_exp_list[0] & value
                            q_exp_list.pop(0)
                            q_exp_list.append(processed_value)
                        else:
                            processed_value = q_exp_list[0] | value
                            q_exp_list.pop(0)
                            q_exp_list.append(processed_value)

                    count = count + 1

                if counter==0:
                    all_q_exp_list.append(q_exp_list[0])

                else:
                    if phrase[count - 1] == 'AND':
                        all_processed_value = all_q_exp_list[0] & q_exp_list[0]
                        all_q_exp_list.pop(0)
                        all_q_exp_list.append(all_processed_value)
                    else:
                        all_processed_value = all_q_exp_list[0] | q_exp_list[0]
                        all_q_exp_list.pop(0)
                        all_q_exp_list.append(all_processed_value)
            else:

                value=Q(data)
                if counter==0:
                    all_q_exp_list.append(value)

                else:
                    if phrase[count - 1] == 'AND':
                        all_processed_value = all_q_exp_list[0] & value
                        all_q_exp_list.pop(0)
                        all_q_exp_list.append(all_processed_value)
                    else:
                        all_processed_value = all_q_exp_list[0] | value
                        all_q_exp_list.pop(0)
                        all_q_exp_list.append(all_processed_value)

            counter=counter+1

        return all_q_exp_list[0]


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

        if not isinstance(search_phrase,list):
            raise ValidationError({"detail":"search_phrase field should be list type"})

        if len(search_phrase) >0:
            for operator in search_phrase:
                if operator not in ['AND','OR']:
                    raise ValidationError({'detail':f'{operator} is not a valid operator'})

        if len(allowed_fields) >= 1:
            count=0
            for key,value in allowed_fields.items():
                    # raise ValidationError({'detail':'search_phrase field has unwanted operators'})
                if isinstance(allowed_fields[key],dict):
                    count_element=len(allowed_fields[key])
                    count=count+count_element
                else:
                    count = count + 1

            if count-1 !=len(search_phrase):
                raise ValidationError({'detail': 'Data and operator are not applicable with each other'})



        search_filter=self.parse_search_phrase(allowed_fields,search_phrase)

        try:
            queryset=User.objects.filter(search_filter)

        except FieldError as e:
            raise ValidationError({'detail':e})


        serializers=UserSerializer(queryset,many=True)

        return Response(serializers.data)


