<%inherit file="base.mako"/>
      <div>
        <h1><%block name="title">Категории</%block>:
        </h1>
      </div>

      <hr>

      <div class="row-fluid marketing">
          <div class="span12">
              <table class="table">
                  <thead>
                  <tr>
                      <th>Категория</th>
                      <th>средняя цена</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for category in req.context['ProductCategory'].values():
                    <tr>
                        <td>
                            <a href="${req.resource_url(category)}">
                                ${category.get_data('keyword')}
                            </a>
                        </td>
                        <td>${category.get_price()}</td>
                    </tr>
                  % endfor
                  </tbody>
              </table>
        </div>
      </div>