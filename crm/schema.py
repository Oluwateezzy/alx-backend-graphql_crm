import graphene
from graphene_django import DjangoObjectType
from crm.models import Order, Customer, Product
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name")


class OrderType(DjangoObjectType):
    customer = graphene.Field(lambda: CustomerType)

    class Meta:
        model = Order
        fields = ("id", "order_date", "customer")

    def resolve_customer(self, info):
        return self.customer


class Query(graphene.ObjectType):
    orders = graphene.List(OrderType, days=graphene.Int(required=True))
    total_customers = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()

    def resolve_orders(self, info, days):
        cutoff_date = timezone.now() - timedelta(days=days)
        return Order.objects.filter(order_date__gte=cutoff_date)

    def resolve_total_customers(self, info):
        return Customer.objects.count()

    def resolve_total_orders(self, info):
        return Order.objects.count()

    def resolve_total_revenue(self, info):
        return Order.objects.aggregate(total=Sum("totalamount"))["total"] or 0.0


class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        threshold = graphene.Int(default_value=10)
        restock_amount = graphene.Int(default_value=10)

    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(graphene.String)

    def mutate(self, info, threshold, restock_amount):
        products = Product.objects.filter(stock__lt=threshold)
        updated_names = []

        for product in products:
            product.stock += restock_amount
            product.save()
            updated_names.append(f"{product.name} ({product.stock})")

        return UpdateLowStockProducts(
            success=True,
            message="Stock updated for low-stock products.",
            updated_products=updated_names,
        )


class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
