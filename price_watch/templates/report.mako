<%inherit file="base.mako"/>
<%def name="noindex()"><meta name="robots" content="noindex"></%def>
<%def name="description()">
<meta name="description" content="Отчет о цене на ${req.context.product.title}
у продавца ${req.context.merchant.title} за ${view.fd(req.context.date_time,
                                                      format='long',
                                                      locale=req.locale_name)}">
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
                  <tr>
                      <td>Продавец</td>
                      <td><strong>${req.context.merchant.title}
                          (${req.context.merchant.location})</strong>
                          </td>
                  </tr>
                  <tr>
                      <td>URL / ID товара</td>
                      <td>
                        <strong>${req.context.url}</strong>
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
                  <tr class="price_value warning">
                      <td>Цена</td>
                      <td>
                          <strong>${view.currency(req.context.price_value)} руб.</strong> /
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