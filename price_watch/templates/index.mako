<%inherit file="base.mako"/>
      <div>
            <%def name="title()">Главная</%def>
      </div>

      <div class="row-fluid marketing">
          <div class="span12">
              <div id="chart_div" style="width: 700px; height: 400px;"></div>

              <table class="table">
                  <thead>
                  <tr>
                      <th>Категория</th>
                      <th>средняя цена</th>
                      <th>кол-во продуктов</th>
                      <th>регионы</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for url, title, price, delta, \
                         product_count, locations in categories:
                    <tr>
                        <td>
                            <a href="${url}">${title}</a>
                        </td>
                        <td>
                            ${price}
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
                        <td>${product_count}</td>
                        <td>${locations}</td>
                    </tr>
                  % endfor
                  </tbody>
              </table>
              <span title="Время последнего обновления"
                    class="label label-default"
                    style="margin-bottom: 3em">
                  <i class="glyphicon glyphicon-time"></i>
                  ${time}
              </span>
        </div>
      </div>
<%def name="js()">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
        google.load("visualization", "1", {packages:["corechart"]});
        google.setOnLoadCallback(drawChart);
        function drawChart() {
            var headers = [['Дата'].concat(${chart_titles|n})];
            var data = google.visualization.arrayToDataTable(
                headers.concat(${chart_rows|n})
            );
            var options = {
                title: 'Категории продуктов',
                curveType: 'function',
                legend: {position: 'top'},
                hAxis: {showTextEvery: 4},
                chartArea:{left:50, top:50, width:'90%', height:'75%'}
            };

            var chart = new google.visualization.LineChart(
                    document.getElementById('chart_div'));

            chart.draw(data, options);
        }
    </script>
</%def>