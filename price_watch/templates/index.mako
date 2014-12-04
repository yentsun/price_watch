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
                      <th>кол-во продуктов</th>
                      <th>кол-во отчетов</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for category in req.context['categories'].values():
                      % if len(category.products):
                    <tr>
                        <td>
                            <a href="${req.resource_url(category)}">
                                ${category.get_data('keyword')}
                            </a>
                        </td>
                        <td>
                            ${view.currency(category.get_price())}
                            <% delta = category.get_price_delta(view.delta_period)*100 %>
                             % if delta > 0:
                            <span title="+${delta}%"
                                  class="glyphicon glyphicon-arrow-up"
                                  style="color:red"></span>
                            % elif delta < 0:
                                <span title="${delta}%"
                                      class="glyphicon glyphicon-arrow-down"
                                      style="color:green"></span>
                            % endif
                        </td>
                        <td>${len(category.get_qualified_products())}</td>
                        <td>${len(category.get_reports())}</td>
                    </tr>
                        % endif
                  % endfor
                  </tbody>
              </table>
        </div>
      </div>