from colander import MappingSchema, SchemaNode, DateTime, Decimal, String


class MerchantSchema(MappingSchema):
    """Schema for `Merchant` model"""

    title = SchemaNode(String())
    location = SchemaNode(String())


class ManufacturerSchema(MappingSchema):
    """Schema for `Manufacturer` model"""


class CategorySchema(MappingSchema):
    """Schema for `Manufacturer` model"""


class ProductSchema(MappingSchema):
    """Schema for `Product` model"""

    title = SchemaNode(String())
    barcode = SchemaNode(String())
    manufacturer = ManufacturerSchema()
    category = CategorySchema()


class ReporterSchema(MappingSchema):
    """Schema for `Reporter` model"""


class PriceReportSchema(MappingSchema):
    """Schema for `PriceReport` model"""

    datetime = SchemaNode(DateTime())
    price_value = SchemaNode(Decimal())
    amount = SchemaNode(Decimal())
    merchant = MerchantSchema()
    product = ProductSchema()
    reporter = ReporterSchema()
    url = SchemaNode(String())