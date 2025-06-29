import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.exceptions import ValidationError
from django.db import transaction
import re


# Type Definitions
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"

    customer = graphene.Field(CustomerType)
    products = graphene.List(ProductType)
    total_amount = graphene.Decimal()

    def resolve_customer(self, info):
        return self.customer

    def resolve_products(self, info):
        return self.products.all()

    def resolve_total_amount(self, info):
        return self.calculate_total()


# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# Mutation Classes
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate phone format if provided
            if input.phone and not re.match(
                r"^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$", input.phone
            ):
                raise ValidationError(
                    "Phone must be in format +1234567890 or 123-456-7890"
                )

            customer = Customer(name=input.name, email=input.email, phone=input.phone)
            customer.full_clean()
            customer.save()

            return CreateCustomer(
                customer=customer, message="Customer created successfully", success=True
            )
        except ValidationError as e:
            return CreateCustomer(customer=None, message=str(e), success=False)
        except Exception as e:
            return CreateCustomer(
                customer=None, message=f"An error occurred: {str(e)}", success=False
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    error_count = graphene.Int()

    @staticmethod
    @transaction.atomic
    def mutate(root, info, inputs):
        customers = []
        errors = []

        for idx, input in enumerate(inputs):
            try:
                # Validate phone format if provided
                if input.phone and not re.match(
                    r"^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$", input.phone
                ):
                    raise ValidationError("Invalid phone format")

                customer = Customer(
                    name=input.name, email=input.email, phone=input.phone
                )
                customer.full_clean()
                customer.save()
                customers.append(customer)
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")

        return BulkCreateCustomers(
            customers=customers,
            errors=errors,
            success_count=len(customers),
            error_count=len(errors),
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, input):
        try:
            if input.price <= 0:
                raise ValidationError("Price must be positive")

            if hasattr(input, "stock") and input.stock < 0:
                raise ValidationError("Stock cannot be negative")

            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock if hasattr(input, "stock") else 0,
            )
            product.full_clean()
            product.save()

            return CreateProduct(
                product=product, message="Product created successfully", success=True
            )
        except ValidationError as e:
            return CreateProduct(product=None, message=str(e), success=False)
        except Exception as e:
            return CreateProduct(
                product=None, message=f"An error occurred: {str(e)}", success=False
            )


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                raise ValidationError("Customer does not exist")

            # Validate at least one product
            if not input.product_ids:
                raise ValidationError("At least one product is required")

            # Get all products at once
            products = Product.objects.filter(pk__in=input.product_ids)

            # Check if all products exist
            if len(products) != len(input.product_ids):
                found_ids = {str(p.id) for p in products}
                missing_ids = [pid for pid in input.product_ids if pid not in found_ids]
                raise ValidationError(f"Products not found: {', '.join(missing_ids)}")

            # Create the order
            order = Order(customer=customer)
            order.save()  # Save first to get an ID

            # Add products
            order.products.set(products)

            # Calculate and save total
            order.total_amount = order.calculate_total()
            order.save()

            return CreateOrder(
                order=order, message="Order created successfully", success=True
            )
        except ValidationError as e:
            return CreateOrder(order=None, message=str(e), success=False)
        except Exception as e:
            return CreateOrder(
                order=None, message=f"An error occurred: {str(e)}", success=False
            )


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
