from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.db.models import Q

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
import re
from user.serializers import UserSerializer

import re

class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


    def conversion(self,value):
        data_list=[]
        count_item=0
        for data in value:
            value1 = re.sub("[()]", "", data)
            if 'eq' in value1:
                split = value1.split('eq')
                data1 = split[0].replace(" ", "")
                # data2= split[1]).replace(" ","")
                data_list.append((split[0].replace(" ", ""), split[1].replace(" ", "")))
            if 'lt' in value1:
                split = value1.split('lt')
                join_value = split[0] + '__lte'
                data_list.append((join_value.replace(" ", ""), split[1].replace(" ", "")))

            if 'gt' in value1:
                split = value1.split('gt')
                join_value = split[0] + '__gte'
                data_list.append((join_value.replace(" ", ""), split[1]).replace(" ", ""))

            count_item += 1

        return data_list,count_item

    def identifier(self,data_set):
        allowed_data=[]
        count_item=0
        for string in data_set:
            count=0
            for s in string:
                if s == '(':
                    count=count+1
                    if count==2:
                        own_fields=[]
                        value1=re.sub("[()]","",string)
                        value2=value1.split(",")
                        data_set,count=self.conversion(value2)
                        allowed_data.append(data_set)

                        count_item=count_item+count
                        print(value1)
                        break

                else:
                    value1=[re.sub("[()]","",string)]
                    data_set,count = self.conversion(value1)
                    allowed_data.append(data_set[0])
                    count_item = count_item + count

                    break

        return allowed_data,count_item

    def parse_search_phrase(self,allowed_fields,phrase):
        bracket = 0

        for single in allowed_fields:
            for i in single:
                if i == '(':
                    bracket += 1
                if i == ')':
                    if bracket == 0:
                        raise ValidationError({"detail":"Please check your opening and closing brackets"})
                    bracket -= 1
        if bracket !=0:
            raise ValidationError({"detail": "Please check your opening and closing brackets"})

        allowed_data,all_count=self.identifier(allowed_fields)

        if all_count - 1 != len(phrase):
            raise ValidationError({'detail': 'Data and operator are not applicable with each other'})
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
        #
        if 'search_phrase' not in data_keys:
            raise ValidationError({"detail":"search_phrase field cannot be null"})

        allowed_fields = request.data['allowed_fields']
        search_phrase = request.data['search_phrase']

        if not isinstance(allowed_fields,list):
            raise ValidationError({"detail":"allowed_fields field should be list type"})

        if not isinstance(search_phrase,list):
            raise ValidationError({"detail":"search_phrase field should be list type"})

        if len(search_phrase) >0:
            for operator in search_phrase:
                if operator not in ['AND','OR']:
                    raise ValidationError({'detail':f'{operator} is not a valid operator'})

        # if len(allowed_fields) >= 1:
        #     count=0
        #     for key,value in allowed_fields.items():
        #             # raise ValidationError({'detail':'search_phrase field has unwanted operators'})
        #         if isinstance(allowed_fields[key],dict):
        #             count_element=len(allowed_fields[key])
        #             count=count+count_element
        #         else:
        #             count = count + 1
        #
        #     if count-1 !=len(search_phrase):
        #         raise ValidationError({'detail': 'Data and operator are not applicable with each other'})

        #
        #
        search_filter=self.parse_search_phrase(allowed_fields,search_phrase)

        try:
            queryset=User.objects.filter(search_filter)

        except FieldError as e:
            raise ValidationError({'detail':e})


        serializers=UserSerializer(queryset,many=True)

        return Response(serializers.data)




