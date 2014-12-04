<%inherit file="page_base.mako"/>
<%def name="title()">О проекте</%def>

<p>
    Было ли вам когда-нибудь интересно узнать где в Москве самое дешевое молоко?
    Какая в Петербурге средняя цена на ржаной хлеб? Сколько в Новосибирске стоит
    килограмм картофеля? Проект <strong>${self.project_title()}</strong>
    разрабатывается с целью ответить
    на эти вопросы. Отчеты о ценах собираются как с интернет-магазинов, так и от
    пользователей.
</p>
<p>
    Средняя цена расчитывается с помощью
    <a href="https://ru.wikipedia.org/wiki/Медиана_(статистика)">медианы</a>
    чтобы исключить влияние экстремальных пиков.
</p>
<p>
    Также, в расчет берется "нормированная" упаковка продукта. Например, если
    упаковка молока 950 г стоит <em>55,91 руб.</em>, то при расчете средней цены
    будет учитываться цена этого молока за литр (литр - "нормированная"
    упаковка для молока), то есть <em>60,12 руб</em>.
</p>

<h3>Некоторые факты:</h3>
<ul>
    <li>цены обновляются <em>раз в день</em></li>
    <li>тенденция роста или падения цены показана <em>за месяц</em></li>
    <li>мы стараемся не учитывать цены на товары, упаковка которых значительно
        отличается от нормированной. Например, цены на молоко в пакете
        <em>200 л</em> игнорируются.</li>
</ul>

<h3>Текущие цели:</h3>

<ul>
    <li>собирать данные от бо́льшего числа магазинов</li>
    <li>выпустить публичный API</li>
    <li>прием отчетов от пользователей</li>
    <li>увеличение быстродействия</li>
</ul>