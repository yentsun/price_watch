<%inherit file="base.mako"/>
      <div>
        <h1>
            <%block name="title">${req.context.get_data('keyword')}</%block>:
            ${req.context.get_price()}
        </h1>
      </div>

      <hr>

      <div class="row-fluid marketing">
          <div class="span12">
              <table class="table">
                  <thead>
                  <tr>
                      <th>Продукт</th>
                      <th>Упаковка</th>
                      <th>Цена</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for product in sorted(req.context.products.values(), \
                                          key=lambda pr: pr.get_price()):
                    <tr>
                        <td>
                            <a href="${req.resource_url(product)}">
                                ${product.title}
                            </a>
                        </td>
                        <td>${product.package}</td>
                        <td>${product.get_price()}</td>
                    </tr>
                  % endfor
                  </tbody>
              </table>
        </div>
      </div>