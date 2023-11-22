import decimal
from django.core.serializers.json import DjangoJSONEncoder


class ChartJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return round(float(obj), 2)
        return super().default(obj)
