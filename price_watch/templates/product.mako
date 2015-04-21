<%inherit file="base.mako"/>
<%def name="title()">Цена на ${req.context.title}</%def>
<%def name="description()">
    Текущая цена и история цен на ${req.context.title} за последний месяц
</%def>
<div itemscope itemtype="http://www.data-vocabulary.org/Product">
% if current_price:
<div class="pull-right well well-sm cat_price">
    % if product_delta > 0:
        <span title="+${product_delta}%"
              class="fa fa-arrow-up"
              style="color:red"></span>
    % elif product_delta < 0:
        <span title="${product_delta}%"
              class="fa fa-arrow-down"
              style="color:green"></span>
    % endif
    <span>${current_price}</span><i class="fa fa-rub"></i><br>
    <small class="package_title">за ${package_title}</small>
</div>
% endif
<a id="category" href="${req.resource_url(req.root)}#${category_title}"
   title="основная категория">
    ${category_title_ru}
</a> /
<a itemprop="category" id="product_category" href="${product_category_url}"
   title="категория">
    ${product_category_title}
</a>
<h1 itemprop="name" id="product_heading">
    ${req.context.title}
</h1>
<div class="row-fluid marketing" itemprop="offers">
    <div class="span12">
        % if len(reports):
            <div id="chart_div" style="width: 700px; height: 300px;"></div>
            <table class="table">
                <thead>
                <tr>
                    <th>Дата и время отчета</th>
                    <th>Продавец</th>
                    <th>Цена / ${package_title}</th>
                    <th></th>
                </tr>
                </thead>
                <tbody>
                    % for url, date, merchant, location, price in reports:
                        <tr itemscope
                            itemtype="http://www.data-vocabulary.org/Offer">
                            <td>
                                <a itemprop="priceValidUntil"
                                   href="${url}">${date}</a>
                            </td>
                            <td itemprop="seller">${merchant} (${location})</td>
                            <td><span itemprop="price">${price}</span>
                            <i class="fa fa-rub"></i>
                            <span class="currency_iso"
                                  itemprop="currency">RUB</span>
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        % else:
            <div class="alert alert-warning">
                По этому продукту отчеты не поступали длительное время.
                % if last_report_url:
                <a href="${last_report_url}">Последний отчет</a>
                % endif
            </div>
        % endif
    </div>
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