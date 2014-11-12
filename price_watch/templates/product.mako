<%inherit file="base.mako"/>
      <div>
        <h1><%block name="title">${req.context.title}</%block>:
            ${req.context.get_price()}
        </h1>
      </div>

      <hr>

      <div class="row-fluid marketing">
          <div class="span12">
              <table class="table">
                  <thead>
                  <tr>
                      <th>Дата отчета</th>
                      <th>Продавец</th>
                      <th>Цена</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for report in sorted(req.context.reports.values(), key=lambda pr: pr.date_time):
                    <tr>
                        <td>
                            <a href="${req.resource_url(report)}">
                            ${report.date_time}
                            </a>
                        </td>
                        <td>${report.merchant.title}</td>
                        <td>${report.normalized_price_value}</td>
                    </tr>
                  % endfor
                  </tbody>
              </table>
        </div>
      </div>