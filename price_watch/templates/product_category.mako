<%inherit file="base.mako"/>
<div class="pull-right well well-sm cat-price">
    ${median_price}
</div>
<h1>
    <%block name="title">Цены на ${cat_title}</%block><br>
    <small>${package_title}</small>
</h1>
<div class="row-fluid marketing">
    <div class="span12">
        <div id="chart_div" style="width: 700px; height: 300px;"></div>
        <div>
            Ниже представлен список продуктов, из цен на которые складывается
            средняя цена.
        </div>
        <table id="product_list" class="table">
            <thead>
            <tr>
                <th>№</th>
                <th>Продукт</th>
                <th class="price">Цена (руб.) за ${package_title}</th>
            </tr>
            </thead>
            <tbody>
                % for num, product, url, price, delta, median in products:
                    % if median:
                        <tr class="info" title="Этот товар имеет среднюю цену
                                                в категории">
                    % else:
                        <tr>
                    % endif
                        <td>${num}</td>
                        <td>
                            <a href="${url}">
                                ${product.title}
                            </a>
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
            var headers = [['Дата', 'Средняя цена, руб.']];
            var data = google.visualization.arrayToDataTable(
                headers.concat(${price_data|n})
            );
            var options = {
                title: 'Динамика за месяц',
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