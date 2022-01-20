import re

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


    def conversion(self,value):
        """
        This method works on converting the operator into python understandable format.

        :param value: accept list data type
        :return: list of data and integer
        """
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
        """
        This method identity where the operation is nested or not and act accordingly.

        :param data_set: accept list data type
        :return: list of data and integer
        """
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


    def expression(self,data1,data2,phrase,count):
        """
        This method operation on the basis of operands and return the final output
        """
        if phrase[count - 1] == 'AND':
            processed_value = data1[0] & data2
            data1.pop(0)
            data1.append(processed_value)
        else:
            processed_value = data1[0] | data2
            data1.pop(0)
            data1.append(processed_value)

        return data1

    def parse_search_phrase(self,allowed_fields,phrase):
        """
        This method converts the normal expression into Q expression.

        :param allowed_fields: list data type
        :param phrase: list data type
        :return: Q object
        """
        bracket = 0
        counter = 0
        count = 0
        all_q_exp_list = []

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

        for data in allowed_data:

            if isinstance(data,list):
                q_exp_list=[]
                count=0

                for single_data in data:
                    value=Q(single_data)

                    if count ==0:
                        q_exp_list.append(value)

                    else:
                        list_expression=self.expression(q_exp_list,value,phrase,count)

                    count = count + 1

                if counter==0:
                    all_q_exp_list.append(list_expression[0])

                else:
                    list_expression = self.expression(all_q_exp_list, q_exp_list[0], phrase, count)
                    all_q_exp_list.append(list_expression[0])
            else:
                value=Q(data)

                if counter==0:
                    all_q_exp_list.append(value)

                else:
                    list_expression = self.expression(all_q_exp_list, value, phrase, count)
                    all_q_exp_list.append(list_expression[0])

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


        search_filter=self.parse_search_phrase(allowed_fields,search_phrase)

        try:
            queryset=User.objects.filter(search_filter)

        except FieldError as e:
            raise ValidationError({'detail':e})


        serializers=UserSerializer(queryset,many=True)

        return Response(serializers.data)




