<%inherit file="base.mako"/>
      <div>
          <div class="pull-right well well-sm cat-price">
            ${current_price}р.
          </div>
        <h1 id="product_heading">
            <%block name="title">${req.context.title}</%block>
        </h1>
      </div>

      <div class="row-fluid marketing">
          <div class="span12">
              <div id="chart_div" style="width: 700px; height: 300px;"></div>
        <div>
              <table class="table">
                  <thead>
                  <tr>
                      <th>Дата и время отчета</th>
                      <th>Продавец</th>
                      <th>Цена</th>
                  </tr>
                  </thead>
                  <tbody>
                  % for url, date, merchant, price in reports:
                    <tr>
                        <td>
                            <a href="${url}">${date}</a>
                        </td>
                        <td>${merchant}</td>
                        <td>${price}</td>
                    </tr>
                  % endfor
                  </tbody>
              </table>
        </div>
      </div>
<%def name="js()">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
        google.load("visualization", "1", {packages:["corechart"]});
        google.setOnLoadCallback(drawChart);
        function drawChart() {
            var headers = [['Дата', 'Цена, руб.']];
            var data = google.visualization.arrayToDataTable(
                headers.concat(${chart_data|n})
            );
            var options = {
                title: 'Динамика цены за месяц ',
                curveType: 'function',
                legend: {position: 'top'},
                hAxis: {showTextEvery: 4},
                chartArea:{left:50, top:50, width:'90%', height:'75%'}
            };

            var chart = new google.visualization.LineChart(document.getElementById('chart_div'));

            chart.draw(data, options);
        }
    </script>
</%def>