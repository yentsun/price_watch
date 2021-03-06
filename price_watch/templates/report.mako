<%inherit file="base.mako"/>
<%def name="noindex()"><meta name="robots" content="noindex"></%def>
<%def name="description()">
Отчет о цене на ${req.context.product.title}
у продавца ${req.context.merchant.title} за ${view.fd(req.context.date_time,
                                                      format='long',
                                                      locale=req.locale_name)}
</%def>
      <div>
        <h1>
            <%block name="title">Отчет о цене</%block>
        </h1>
      </div>


      <div class="row-fluid marketing">
          <div class="span12">
              <div id="report_card">
                  <table class="table">
                  <tbody>
                  <tr class="id">
                      <td style="width:20%">ID</td>
                      <td class="barcode">${req.context.key}</td>
                  </tr>
                  <tr class="product">
                      <td>Товар</td>
                      <td>
                      <strong>${req.context.product.title}</strong>
                      </td>
                  </tr>
                  <tr class="package">
                      <td>Упаковка</td>
                      <td>
                      <strong>${req.context.product.get_package_key()}</strong>
                      </td>
                  </tr>
                  <tr>
                      <td>Продавец</td>
                      <td><strong>${req.context.merchant.title}
                          (${req.context.merchant.location})</strong>
                          </td>
                  </tr>
                  <tr class="url">
                      <td>URL</td>
                      <td>
                        <strong>${req.context.url}</strong>
                      </td>
                  </tr>
                  <tr title="Идентификатор товарной позиции у продавца / Артикул">
                      <td>SKU</td>
                      <td class="sku">
                          % if hasattr(req.context, 'sku'):
                              <strong>${req.context.sku}</strong>
                          % endif
                      </td>
                  </tr>
                  <tr>
                      <td>Дата и время</td>


                      <td>
                          <strong>
                              ${view.fd(req.context.date_time, format='long',
                                        locale=req.locale_name)}
                          </strong>
                      </td>
                  </tr>
                  <tr>
                      <td>Автор</td>
                      <td>
                          <strong>
                              ${req.context.reporter.name}
                          </strong>
                      </td>
                  </tr>
                  <tr>
                      <td>Цена</td>
                      <td>
                          <strong>${view.currency(req.context.price_value)} руб.</strong>
                      </td>
                  </tr>
                  <tr class="price_value warning">
                      <td>Цена за ${req.context.product.category.get_data('normal_package')}</td>
                      <td>
                          <strong title="Цена за нормированную упаковку">
                              ${view.currency(req.context.normalized_price_value)} руб.
                          </strong>
                      </td>
                  </tr>
                  </tbody>
                  </table>
              </div>
        </div>
      </div>