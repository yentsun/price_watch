# -*- coding: utf-8 -*-

from colander import (SchemaNode, MappingSchema, SequenceSchema,
                      String, Int, Decimal, Length, Range, Email, All,
                      Function, Date, DateTime, Regex, null)


class ProductSchema(MappingSchema):
    title = SchemaNode(String())


class MerchantSchema(MappingSchema):
    title = SchemaNode(String())


class ReporterSchema(MappingSchema):
    name = SchemaNode(String())


class PriceReportSchema(MappingSchema):
    product = ProductSchema()
    merchant = MerchantSchema()
    date_time = SchemaNode(DateTime())
    price_value = SchemaNode(Decimal())
    reporter = ReporterSchema()
    url = SchemaNode(String())