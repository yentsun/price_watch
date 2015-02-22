<%inherit file="base.mako"/>
<%def name="title()">
     % if current_location:
    Цены на продукты, ${current_location}
    % else:
    Цены на продукты
    % endif
</%def>
<%def name="location_menu()">
    <%include file="partials/location_menu.mako"
              args="current_location=current_location, locations=locations,
                    current_path='/'" />
</%def>
      <div class="row-fluid marketing">
          <div class="span12">
              <div id="chart_div" style="width: 700px; height: 400px;"></div>

              <table class="table">
                  <thead>
                  <tr>
                      <th>Категория</th>
                      <th>средняя цена</th>
                      <th>упаковка</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for url, title, price, delta, \
                         package, locations in categories:
                    <tr>
                        <td>
                            <a href="${url}">${title}</a>
                        </td>
                        <td>
                             % if delta > 0:
                            <span title="+${delta}%"
                                  class="glyphicon glyphicon-arrow-up"
                                  style="color:red"></span>
                            % elif delta < 0:
                                <span title="${delta}%"
                                      class="glyphicon glyphicon-arrow-down"
                                      style="color:green"></span>
                            % endif
                            ${price}
                        </td>
                        <td>${package}</td>
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
            var date_column = ${date_column|n};
            var category_columns = ${category_columns|n};
            var data = new google.visualization.DataTable();
            var date_col = data.addColumn('string', 'Дата');
            console.log(category_columns);
            for (var i=0; i<date_column.length; i++) {
                var row_n = data.addRow();
                data.setCell(row_n, date_col, date_column[i]);
            }
            for (var j=0; j<category_columns.length; j++) {
                var title = category_columns[j].shift();
                console.log(title);
                var cat_col = data.addColumn('number', title);
                for (var cr=0; cr<category_columns[j].length; cr++) {
                    data.setCell(cr, cat_col, category_columns[j][cr]);
                }
            }

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